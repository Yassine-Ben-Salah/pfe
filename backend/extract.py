"""
extract_rapports.py
-------------------
Improved extractor for scanned French insurance rapport d'expertise PDFs.

Key improvements over v1:
  - Tesseract PSM 6 (uniform block) + preprocessing (denoise, contrast, deskew)
  - Looser page filter — keeps any page that has at least 1 rapport keyword
  - Dedicated price-table parser that handles multi-column OCR output
  - Wider / more forgiving regex patterns for all fields
  - One clean JSON file per rapport saved next to the PDF
"""

import os
import re
import json
import pdfplumber
import pytesseract
import cv2
import numpy as np
from PIL import Image

# ── Tesseract config ──────────────────────────────────────────────────────────
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# PSM 6  = "Assume a single uniform block of text" — best for printed forms
# OEM 1  = LSTM engine only (most accurate for printed French)
TESS_CONFIG = "--psm 6 --oem 1 -l fra"


# =============================================================================
# IMAGE PRE-PROCESSING
# =============================================================================

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """
    Sharpen, denoise and binarise a PIL image before Tesseract.
    Returns a PIL image in mode 'L' (greyscale).
    """
    img = np.array(pil_img.convert("RGB"))

    # 1. Convert to greyscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 2. Mild denoise (preserves edges better than GaussianBlur)
    gray = cv2.fastNlMeansDenoising(gray, h=15)

    # 3. Adaptive threshold — handles uneven lighting across the page
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=12,
    )

    # 4. Slight sharpening kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(binary, -1, kernel)

    return Image.fromarray(sharpened)


# =============================================================================
# PAGE CLASSIFICATION
# =============================================================================

# Any page that matches at least one of these is kept
RAPPORT_KEYWORDS = [
    r"NATURE\s+DES\s+CHOCS",
    r"ESTIMATION\s+DES\s+TRAVAUX",
    r"TOTAL\s+NET",
    r"DESIGNATION",
    r"RAPPORT\s+D.EXPERTISE",
    r"Marque",
    r"Immatriculation",
    r"N[°o]\s*Dossier",
    r"Assuré",
    r"Date\s+d.accident",
    r"FOURNITURE",
    r"MAIN\s+D.OEUVRE",
]

def is_rapport_page(text: str) -> bool:
    text_upper = text.upper()
    for kw in RAPPORT_KEYWORDS:
        if re.search(kw, text_upper, re.IGNORECASE):
            return True
    return False


# =============================================================================
# OCR + PAGE COLLECTION
# =============================================================================

def ocr_page(page) -> str:
    """Rasterise a pdfplumber page at 300 DPI and OCR it."""
    pil_img = page.to_image(resolution=300).original.convert("RGB")
    clean = preprocess_image(pil_img)
    return pytesseract.image_to_string(clean, config=TESS_CONFIG)


def collect_text(pdf_path: str) -> str:
    """
    Return all rapport-relevant OCR text from a PDF, concatenated.
    Skips Arabic / photo-only pages that produce no French content.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Try native text first (unlikely for scans, but fast)
            native = page.extract_text() or ""
            if len(native.strip()) > 80 and is_rapport_page(native):
                full_text += native + "\n"
                print(f"  Page {i+1}: native text ✓")
                continue

            # Fall back to OCR
            try:
                text = ocr_page(page)
                if is_rapport_page(text):
                    full_text += text + "\n"
                    print(f"  Page {i+1}: OCR rapport page ✓")
                else:
                    print(f"  Page {i+1}: skipped (no rapport keywords)")
            except Exception as e:
                print(f"  Page {i+1}: OCR failed — {e}")

    return full_text


# =============================================================================
# FIELD PARSERS
# =============================================================================

def _get(pattern: str, text: str, group: int = 1) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(group).strip() if m else None


def parse_identity_fields(text: str) -> dict:
    """Extract header / identity fields from the rapport."""
    return {
        "numero_dossier":  _get(r"N[°o°]\s*[Dd]ossier\s*[:\-]?\s*(\d[\d/\-]*)", text),
        "marque":          _get(r"Marque\s*[:\-]?\s*([A-Za-zÀ-ÿ\-]+)", text),
        "type":            _get(r"\bType\s*[:\-]?\s*([A-Za-z0-9\-]+)", text),
        "immatriculation": _get(
            r"Immatriculation\s*[:\-]?\s*([\dA-Za-z]{1,6}\s*TU\s*[\dA-Za-z]{1,6})", text
        ),
        "date_accident":   _get(r"[Dd]ate\s+d[''.]?accident\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", text),
        "assure":          _get(
            r"[Aa]ssur[ée]\(?e?\)?\s*[:\-]?\s*([A-Za-zÀ-ÿ '\-]+?)(?:\s*[\*\|]|\s{3,}|\n)", text
        ),
    }


# ── Damage section ────────────────────────────────────────────────────────────

def parse_damage(text: str) -> str | None:
    """
    Extract the free-text block under NATURE DES CHOCS ET DÉGÂTS.
    Stops at the first blank line or start of another major section.
    """
    m = re.search(
        r"NATURE\s+DES\s+CHOCS[^\n]*\n"           # header line
        r"(?:[Pp]i[eè]ces?[^\n]*\n)?"             # optional "Pièces endommagées" sub-header
        r"(.*?)"                                   # <-- capture group
        r"(?:\n{2,}|(?=ESTIMATION)|(?=TOTAL)|(?=DESIGNATION)|(?=NB\s*:)|\Z)",
        text, re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None

    raw = m.group(1)

    # Strip "Pièces endommagées :" prefix that sometimes leaks in
    raw = re.sub(r"Pi[eè]ces?\s+endommagées?\s*:?[^\n]*\n?", "", raw, flags=re.IGNORECASE)

    # Clean lines
    clean = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # Skip obvious OCR garbage (long runs of accented chars, digits, symbols)
        if re.search(r"[ÀÂÃÄÅÇÈÊËÌÎÏÒÔÕÖÙÛÜÝß]{2,}", line):
            continue
        if re.fullmatch(r"[\W\d\s]+", line):
            continue
        ratio = sum(c.isalpha() or c in " ,;./()-'" for c in line) / max(len(line), 1)
        if ratio > 0.5:
            clean.append(line)

    return "\n".join(clean).strip() or None


# ── Price table ───────────────────────────────────────────────────────────────

def parse_price_table(text: str) -> list[dict]:
    """
    Extract line items from the ESTIMATION DES TRAVAUX table.

    OCR of a multi-column table typically produces lines like:
        Pare-chocs avant   Fourniture   1   280,000   280,000
        Main d'œuvre       MO           3h  45,000    135,000

    Strategy:
      1. Find the table block between ESTIMATION header and TOTAL NET
      2. Each line: label (text) + up to 3 numbers at the end
    """
    # Grab the table block
    m = re.search(
        r"ESTIMATION\s+DES\s+TRAVAUX.*?\n(.*?)(?=TOTAL\s*NET|\Z)",
        text, re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return []

    block = m.group(1)
    items = []

    # Number pattern — handles spaces inside numbers: "1 280,000" or "1280.000"
    NUM = r"[\d\s]{1,6}[,.][\d]{2,3}"

    for line in block.splitlines():
        line = line.strip()
        if not line or len(line) < 6:
            continue

        # Find all numbers at the tail of the line
        nums = re.findall(NUM, line)
        if not nums:
            continue

        # Label = everything before the first number
        first_num_pos = line.find(nums[0])
        label = line[:first_num_pos].strip(" .:;-–")
        if not label or len(label) < 3:
            continue

        # Normalise numbers: remove spaces, unify decimal separator → "."
        def norm(n):
            return n.replace(" ", "").replace(",", ".")

        item = {"designation": label}
        if len(nums) >= 1:
            item["prix_unitaire"] = norm(nums[-2]) if len(nums) >= 2 else norm(nums[0])
        if len(nums) >= 2:
            item["montant"]       = norm(nums[-1])

        items.append(item)

    return items


def parse_totals(text: str) -> dict:
    """Extract TOTAL HT, TVA, TOTAL NET / TTC."""
    return {
        "total_ht":  _get(r"TOTAL\s*H\.?T\.?\s*[:\-]?\s*([\d\s.,]+?)(?:\s*D|\s*DT|\n)", text),
        "tva":       _get(r"T\.?V\.?A\.?\s*[:\-]?\s*([\d\s.,]+?)(?:\s*D|\s*DT|\n|%)", text),
        "total_net": _get(r"TOTAL\s*NET\s*[:\-]?\s*([\d\s.,]+?)(?:\s*D|\s*DT|\n)", text),
        "total_ttc": _get(r"TOTAL\s*T\.?T\.?C\.?\s*[:\-]?\s*([\d\s.,]+?)(?:\s*D|\s*DT|\n)", text),
    }


# =============================================================================
# MAIN EXTRACTOR
# =============================================================================

def extract_rapport(pdf_path: str) -> dict:
    print(f"\n📄 {os.path.basename(pdf_path)}")
    text = collect_text(pdf_path)

    identity = parse_identity_fields(text)
    damage   = parse_damage(text)
    items    = parse_price_table(text)
    totals   = parse_totals(text)

    return {
        "filename": os.path.basename(pdf_path),
        **identity,
        "damage_text":   damage,
        "semantic_text": " | ".join(filter(None, [identity.get("marque"), damage])),
        "price_items":   items,
        **totals,
    }


# =============================================================================
# BATCH RUNNER
# =============================================================================

def process_folder(folder: str, output_folder: str | None = None) -> list[dict]:
    """
    Process every PDF in `folder`.
    Saves one JSON per rapport alongside the PDF (or in output_folder if given).
    Returns a list of all extracted records.
    """
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

            # Save individual JSON
            json_name = os.path.splitext(filename)[0] + ".json"
            json_path = os.path.join(output_folder, json_name)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✅ Saved → {json_name}")
            print(f"     Marque: {data.get('marque')}  |  Immat: {data.get('immatriculation')}")
            print(f"     Total NET: {data.get('total_net')}  |  Items: {len(data.get('price_items', []))}")

        except Exception as e:
            print(f"  ✗ {filename} → {e}")

    # Also save a master index
    index_path = os.path.join(output_folder, "_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done. {len(all_results)} rapports processed.")
    print(f"   Master index → {index_path}")
    return all_results


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    RAPPORTS_FOLDER = r"D:\rapports"     # ← your PDF folder
    OUTPUT_FOLDER   = r"D:\rapports_out" # ← where JSONs will be saved (can be same folder)

    process_folder(RAPPORTS_FOLDER, OUTPUT_FOLDER)