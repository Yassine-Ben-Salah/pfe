#!/usr/bin/env python3
"""
redact_pdf.py — Masque automatiquement les numéros confidentiels dans des
rapports PDF scannés (police d'assurance, contrat, sinistre, permis de
conduire, immatriculation, téléphone, chassis, etc.).

FONCTIONNEMENT
1. Chaque page du PDF est convertie en image (haute résolution).
2. Une reconnaissance de texte (OCR) localise les mots et leurs positions.
3. Le script repère les mots-clés sensibles (ex: "Police N°", "Contrat",
   "Sinistre", "Permis", "Immatriculation", "Tél", "GSM", "Chassis") et
   noircit les numéros qui les suivent sur la même ligne.
4. Il noircit aussi automatiquement les motifs qui ressemblent à des
   numéros de plaque tunisienne (ex: 175 TU 2560) ou des numéros de
   châssis (17 caractères alphanumériques).
5. Les images (redigées) sont réassemblées dans un nouveau PDF.

UTILISATION
    python3 redact_pdf.py mon_rapport.pdf
    -> crée mon_rapport_redacted.pdf

    python3 redact_pdf.py dossier_entier/*.pdf
    -> traite plusieurs fichiers d'un coup

NOTE IMPORTANTE
L'OCR fonctionne très bien sur le texte imprimé (factures, notes
d'honoraires, rapports d'expertise) mais est moins fiable sur l'écriture
manuscrite (constats amiables remplis à la main). Pour ces cas, vous
pouvez ajouter des zones de masquage manuelles avec --manual-box
(voir plus bas), ou vérifier visuellement le PDF de sortie et signaler
les zones ratées.
"""

import sys
import re
import argparse
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image, ImageDraw
import pytesseract
import img2pdf
import io

# ---------------------------------------------------------------------------
# Mots-clés (en minuscules) qui indiquent qu'un numéro sensible SUIT sur la
# même ligne. On noircit les mots suivants sur la ligne (jusqu'à MAX_WORDS
# après le mot-clé, ou jusqu'à la fin de la ligne).
# ---------------------------------------------------------------------------
SENSITIVE_KEYWORDS = [
    "police", "contrat", "sinistre", "permis", "immatriculation",
    "immatricul", "chassis", "châssis", "tél", "tel", "telephone",
    "gsm", "cin", "matricule",
]

MAX_WORDS_AFTER_KEYWORD = 6   # combien de mots après le mot-clé on masque
MAX_LINE_GAP_PX = 40          # tolérance verticale pour "même ligne"

# ---------------------------------------------------------------------------
# Motifs indépendants du mot-clé : on les masque partout où ils apparaissent.
# ---------------------------------------------------------------------------
STANDALONE_PATTERNS = [
    re.compile(r"^\d{2,4}\s?(TU|TN)\s?\d{2,4}$", re.I),   # plaque tunisienne
    re.compile(r"^[A-Z0-9]{15,17}$"),                      # n° de châssis
    re.compile(r"^\d{7,}$"),                                # long numéro brut
    re.compile(r"^\d{2,4}[/-]\d{2,4}[/-]?\d{0,4}$"),        # n° police type 510004760/2
]


def ocr_words(image):
    """Retourne une liste de dicts {text, left, top, width, height} pour
    chaque mot détecté."""
    data = pytesseract.image_to_data(image, lang="eng", output_type=pytesseract.Output.DICT)
    words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if not text:
            continue
        words.append({
            "text": text,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
        })
    return words


def find_redaction_boxes(words):
    boxes = []

    # 1) mots-clés -> masquer les N mots suivants sur la même ligne
    for idx, w in enumerate(words):
        lw = w["text"].lower().strip(":.,°n°")
        if any(k in lw for k in SENSITIVE_KEYWORDS):
            count = 0
            for j in range(idx + 1, len(words)):
                nxt = words[j]
                same_line = abs(nxt["top"] - w["top"]) < MAX_LINE_GAP_PX
                if not same_line:
                    break
                # ignore purely-alphabetic connector words like "de", "N"
                if re.fullmatch(r"[A-Za-zéèêàç°]{1,3}", nxt["text"]):
                    continue
                boxes.append((nxt["left"], nxt["top"], nxt["left"] + nxt["width"], nxt["top"] + nxt["height"]))
                count += 1
                if count >= MAX_WORDS_AFTER_KEYWORD:
                    break

    # 2) motifs autonomes (plaques, châssis, longs numéros) n'importe où
    for w in words:
        t = w["text"].strip()
        if any(p.match(t) for p in STANDALONE_PATTERNS):
            boxes.append((w["left"], w["top"], w["left"] + w["width"], w["top"] + w["height"]))

    # 3) plaques tunisiennes écrites en 3 mots séparés : "2560" "TU" "175"
    for i in range(len(words) - 2):
        a, b, c = words[i], words[i + 1], words[i + 2]
        same_line = abs(a["top"] - b["top"]) < MAX_LINE_GAP_PX and abs(b["top"] - c["top"]) < MAX_LINE_GAP_PX
        if (
            same_line
            and re.fullmatch(r"\d{2,4}", a["text"])
            and re.fullmatch(r"(TU|TN)", b["text"], re.I)
            and re.fullmatch(r"\d{2,4}", c["text"])
        ):
            boxes.append((a["left"], a["top"], c["left"] + c["width"], c["top"] + c["height"]))

    return boxes


def redact_image(image, boxes, padding=4):
    img = image.convert("RGB")
    draw = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in boxes:
        draw.rectangle(
            [x0 - padding, y0 - padding, x1 + padding, y1 + padding],
            fill="black",
        )
    return img


def process_pdf(input_path: Path, output_path: Path, dpi=300, manual_boxes=None):
    print(f"→ {input_path.name}")
    pages = convert_from_path(str(input_path), dpi=dpi)
    redacted_images = []

    for page_num, page_img in enumerate(pages, start=1):
        words = ocr_words(page_img)
        boxes = find_redaction_boxes(words)

        # zones manuelles (mêmes pour toutes les pages du même gabarit)
        if manual_boxes:
            for (pn, x0, y0, x1, y1) in manual_boxes:
                if pn == page_num:
                    boxes.append((x0, y0, x1, y1))

        print(f"   page {page_num}: {len(boxes)} zone(s) masquée(s)")
        redacted_images.append(redact_image(page_img, boxes))

    # Réassembler en PDF
    img_bytes_list = []
    for im in redacted_images:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        img_bytes_list.append(buf.getvalue())

    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(img_bytes_list))

    print(f"   ✔ enregistré : {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Masque les numéros confidentiels dans des PDF scannés.")
    parser.add_argument("pdfs", nargs="+", help="Fichier(s) PDF à traiter")
    parser.add_argument("--dpi", type=int, default=300, help="Résolution de rendu (défaut: 300)")
    parser.add_argument(
        "--manual-box", action="append", default=[],
        metavar="page,x0,y0,x1,y1",
        help="Zone à masquer manuellement, en pixels à la résolution --dpi. "
             "Peut être répété. Ex: --manual-box 3,100,200,400,240",
    )
    args = parser.parse_args()

    manual_boxes = []
    for spec in args.manual_box:
        pn, x0, y0, x1, y1 = [int(v) for v in spec.split(",")]
        manual_boxes.append((pn, x0, y0, x1, y1))

    for pdf_path in args.pdfs:
        pdf_path = Path(pdf_path)
        out_dir = Path("/mnt/user-data/outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / (pdf_path.stem + "_redacted.pdf")
        process_pdf(pdf_path, out_path, dpi=args.dpi, manual_boxes=manual_boxes)


if __name__ == "__main__":
    main()