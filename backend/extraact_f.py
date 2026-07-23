"""
extract_rapports_v4.py
----------------------
Uses pdfplumber for text extraction + Groq for structured field parsing.
No LlamaCloud, no regex fragility.
"""

import os
import re
import json
import pdfplumber
import pytesseract
import cv2
import numpy as np
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/projects/extraction/.env")
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
TESS_CONFIG = "--psm 6 --oem 1 -l fra"


# =============================================================================
# TEXT EXTRACTION
# =============================================================================

def _to_gray(pil_img):
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2GRAY)

def preprocess(pil_img):
    gray = _to_gray(pil_img)
    std = float(np.std(gray))
    if std > 60:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)

RAPPORT_KEYWORDS = [
    "RAPPORT", "EXPERTISE", "ESTIMATION", "TRAVAUX",
    "TOTAL NET", "TOTAL GL", "FOURNITURE", "MAIN D'OEUVRE",
    "NATURE DES CHOCS", "Immatriculation", "Dossier", "Assuré",
    "MANDANT",        # ← rapport3 page 6 header
    "ACCORD AVEC",    # ← rapport3 page 6
    "Point de Choc",  # ← rapport3 page 6
    "DESIGNATION FOURNITURE",  # ← rapport3 page 6
    "KIA",            # ← marque appears on rapport page
    "CITROEN",
    "Volkswagen",
]

def is_rapport_page(text: str) -> bool:
    return any(kw.lower() in text.lower() for kw in RAPPORT_KEYWORDS)

def extract_text_from_pdf(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Try native text first
            native = (page.extract_text() or "").strip()
            if len(native) > 80 and is_rapport_page(native):
                full_text += f"\n--- PAGE {i+1} ---\n{native}\n"
                print(f"  Page {i+1}: native ✓ ({len(native)} chars)")
                continue

            # Fall back to OCR
            try:
                pil_img = page.to_image(resolution=300).original.convert("RGB")
                processed = preprocess(pil_img)
                text = pytesseract.image_to_string(processed, config=TESS_CONFIG)
                if text.strip() and is_rapport_page(text):
                    full_text += f"\n--- PAGE {i+1} ---\n{text}\n"
                    print(f"  Page {i+1}: OCR ✓")
                else:
                    print(f"  Page {i+1}: skipped")
            except Exception as e:
                print(f"  Page {i+1}: error — {e}")

    return full_text


# =============================================================================
# GROQ EXTRACTION
# =============================================================================

def extract_fields_with_groq(full_text: str, filename: str) -> dict:
    prompt = f"""You are extracting data from a French insurance expertise rapport PDF.

Extract ONLY these fields. Return ONLY valid JSON, no explanation, no markdown:
{{
  "filename": "{filename}",
  "numero_dossier": null,
  "marque": null,
  "type": null,
  "immatriculation": null,
  "date_accident": null,
  "assure": null,
  "damage_text": null,
  "price_items": [],
  "total_ht": null,
  "tva": null,
  "total_net": null,
  "total_ttc": null
}}

Rules:
- "damage_text": the free-text damage description (NATURE DES CHOCS section)
- "total_ttc": the repair total from RAPPORT D'EXPERTISE or ESTIMATION DES TRAVAUX page (TOTAL NET or TOTAL GL). 
    IGNORE the NOTE D'HONORAIRES page — that's the expert's fee, not the repair cost.
- "marque": found in RAPPORT D'EXPERTISE under Marque field
- "assure": found in RAPPORT D'EXPERTISE under Assuré(e) field — a person's name only
- "total_net": same as total_ttc if no separate net exists
- "price_items": list of repair line items, each with "designation", "prix_unitaire", "montant"
- For numbers: keep original format (e.g. "1 811,025" or "1179.100")
- Set null if not found

Document:
{full_text[:10000]}"""

    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    text = completion.choices[0].message.content or "{}"
    clean = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(clean)
        result["semantic_text"] = " | ".join(filter(None, [
            result.get("marque"),
            result.get("damage_text")
        ]))
        return result
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Raw: {clean[:200]}")
        return {"filename": filename, "error": str(e)}


# =============================================================================
# MAIN
# =============================================================================

def extract_rapport(pdf_path: str) -> dict:
    filename = os.path.basename(pdf_path)
    print(f"\n📄 {filename}")
    full_text = extract_text_from_pdf(pdf_path)
    if not full_text.strip():
        print("  ⚠ No text extracted")
        return {"filename": filename, "error": "No text extracted"}
    return extract_fields_with_groq(full_text, filename)


def process_folder(folder: str, output_folder: str | None = None) -> list[dict]:
    output_folder = output_folder or folder
    os.makedirs(output_folder, exist_ok=True)
    all_results = []

    for filename in sorted(os.listdir(folder)):
        if not filename.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(folder, filename)
        try:
            data = extract_rapport(pdf_path)
            all_results.append(data)

            json_name = os.path.splitext(filename)[0] + ".json"
            json_path = os.path.join(output_folder, json_name)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✅ {json_name}")
            print(f"     Marque: {data.get('marque')} | TTC: {data.get('total_ttc')}")
        except Exception as e:
            print(f"  ✗ {filename} → {e}")

    index_path = os.path.join(output_folder, "_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done. {len(all_results)} rapports processed.")
    return all_results


if __name__ == "__main__":
    RAPPORTS_FOLDER = r"D:\rapports"
    OUTPUT_FOLDER   = r"D:\rapports_outvf4"
    process_folder(RAPPORTS_FOLDER, OUTPUT_FOLDER)