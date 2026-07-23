#!/usr/bin/env python3
"""
redact_reports.py -- black out confidential ID numbers (police d'assurance,
contrat, sinistre/dossier, permis de conduire...) on scanned insurance-claim
PDFs (constat amiable, rapport d'expertise, note d'honoraires, factures...).

HOW IT WORKS
    These PDFs are scanned images (no selectable text layer), so redaction
    works by: render each page -> OCR it -> find label words like "Police",
    "Contrat", "Sinistre", "Permis" -> black out the handwritten/printed
    value that follows -> re-save as a new PDF made of the edited images.

USAGE
    python3 redact_reports.py rapport3.pdf
    python3 redact_reports.py rapport3.pdf my_output_folder
    python3 redact_reports.py /path/to/folder_of_pdfs/            (batch mode)
    python3 redact_reports.py rapport3.pdf --style blur

OUTPUT (per input file, in the output folder)
    redacted_<name>.pdf  <- the sanitized document (share/store this one)
    preview_<name>.pdf   <- same pages, detected zones outlined in red only
                            (nothing hidden) so you can double-check coverage

IMPORTANT: OCR on handwriting is never 100% reliable. Always open the
preview PDF and compare it to the redacted PDF before sending either one
out. If something is missed, add its coordinates to MANUAL_BOXES below
(read them off the preview file) and re-run.
"""

import argparse
import difflib
import re
import unicodedata
from pathlib import Path

import pypdfium2 as pdfium
import pytesseract
from pytesseract import Output
from PIL import Image, ImageDraw, ImageFilter

# =============================================================================
# CONFIGURATION -- tune this section for your documents
# =============================================================================

# Words that mark the START of a confidential field. Matching is fuzzy and
# accent-insensitive, so small OCR misreads ("Poice" for "Police") still hit.
# Add more stems here (e.g. "immatriculation", "tel") if you want to redact
# additional fields.
ANCHOR_KEYWORDS = [
    "police",    # "Police d'Assurance N°", "Police N°"
    "contrat",   # "Contrat N°" / "Contrat :"
    "sinistre",  # "Sinistre N°" (claim number)
    "dossier",   # "N° Dossier"
    "permis",    # "Permis de conduire N°" (driver's licence number)
]

OCR_LANG = "fra"          # add "+ara" if a document needs Arabic OCR too
RENDER_SCALE = 3.0        # ~216 DPI; raise for very small handwriting (slower)

# Geometry in pixels, calibrated at RENDER_SCALE = 3.0 (auto-scaled if you
# change RENDER_SCALE). See the README-style notes in the module docstring.
Y_TOLERANCE = 45          # how far above/below the label a value may drift
FIRST_GAP_MAX = 230       # max gap from label to the first value token
CONT_GAP_MAX = 95         # max gap between consecutive value tokens
MIN_REDACT_WIDTH = 300    # always blank out at least this much after a label
MAX_REDACT_WIDTH = 620    # never extend one redaction zone further than this
PADDING = 8               # margin added on every side of the computed box

REDACT_STYLE = "box"      # "box" = solid black (recommended); "blur" = softer
                          # but less secure for genuinely confidential numbers

# Extra hand-placed boxes for anything OCR still misses on a specific file.
# Read coordinates off the *_preview.pdf (they're in the same pixel space
# rendered at RENDER_SCALE). Format: {"filename.pdf": {page_index: [(x0,y0,x1,y1), ...]}}
MANUAL_BOXES = {
}

# =============================================================================


def clean(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_anchor(word_text):
    c = clean(word_text)
    if len(c) < 3:
        return False
    for kw in ANCHOR_KEYWORDS:
        if kw in c or c in kw:
            return True
        if difflib.SequenceMatcher(None, kw, c[: len(kw) + 2]).ratio() >= 0.72:
            return True
    return False


def ocr_words(image):
    data = pytesseract.image_to_data(
        image, lang=OCR_LANG, config="--psm 6", output_type=Output.DICT
    )
    words = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        words.append(
            {
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            }
        )
    return words


def find_redaction_boxes(image):
    f = RENDER_SCALE / 3.0
    y_tol, first_gap, cont_gap = Y_TOLERANCE * f, FIRST_GAP_MAX * f, CONT_GAP_MAX * f
    min_w, max_w, pad = MIN_REDACT_WIDTH * f, MAX_REDACT_WIDTH * f, PADDING * f

    words = ocr_words(image)
    boxes = []

    for anchor in words:
        if not is_anchor(anchor["text"]):
            continue

        ax1 = anchor["left"] + anchor["width"]
        band_top = anchor["top"] - y_tol
        band_bottom = anchor["top"] + anchor["height"] + y_tol

        candidates = sorted(
            (
                w
                for w in words
                if w is not anchor
                and w["left"] >= ax1 - 5
                and band_top <= w["top"] <= band_bottom
                and not is_anchor(w["text"])
            ),
            key=lambda w: w["left"],
        )

        cluster, cursor = [], ax1
        for w in candidates:
            gap = w["left"] - cursor
            allowed = first_gap if not cluster else cont_gap
            if gap > allowed or (w["left"] + w["width"]) - ax1 > max_w:
                break
            cluster.append(w)
            cursor = max(cursor, w["left"] + w["width"])

        if cluster:
            x0 = min(w["left"] for w in cluster)
            y0 = min(w["top"] for w in cluster)
            x1 = min(max(w["left"] + w["width"] for w in cluster), ax1 + max_w)
            y1 = max(w["top"] + w["height"] for w in cluster)
        else:
            # Nothing readable followed the label -- still blank a safety
            # zone rather than silently leaving a real value exposed.
            x0, x1 = ax1, ax1 + min_w
            y0 = anchor["top"] - anchor["height"] * 0.3
            y1 = anchor["top"] + anchor["height"] * 1.8

        boxes.append((x0 - pad, y0 - pad, x1 + pad, y1 + pad))

    return merge_boxes(boxes)


def merge_boxes(boxes, gap=15):
    boxes = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if (
                    a[0] - gap <= b[2]
                    and b[0] - gap <= a[2]
                    and a[1] - gap <= b[3]
                    and b[1] - gap <= a[3]
                ):
                    boxes[i] = [
                        min(a[0], b[0]),
                        min(a[1], b[1]),
                        max(a[2], b[2]),
                        max(a[3], b[3]),
                    ]
                    boxes.pop(j)
                    changed = True
                    break
            if changed:
                break
    return [tuple(b) for b in boxes]


def apply_redactions(image, boxes, style="box", outline_only=False):
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    for x0, y0, x1, y1 in boxes:
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(img.width, int(x1)), min(img.height, int(y1))
        if x1 <= x0 or y1 <= y0:
            continue
        if outline_only:
            draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=4)
        elif style == "blur":
            region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(25))
            img.paste(region, (x0, y0))
        else:
            draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))
    return img


def process_pdf(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(input_path))
    manual = MANUAL_BOXES.get(input_path.name, {})
    redacted_pages, preview_pages = [], []

    for i, page in enumerate(pdf):
        image = page.render(scale=RENDER_SCALE).to_pil()

        boxes = find_redaction_boxes(image) + [tuple(b) for b in manual.get(i, [])]

        redacted_pages.append(apply_redactions(image, boxes, style=REDACT_STYLE))
        preview_pages.append(apply_redactions(image, boxes, outline_only=True))
        print(f"  page {i + 1}: {len(boxes)} zone(s) flagged")

    out_path = output_dir / f"redacted_{input_path.stem}.pdf"
    preview_path = output_dir / f"preview_{input_path.stem}.pdf"
    redacted_pages[0].save(out_path, save_all=True, append_images=redacted_pages[1:])
    preview_pages[0].save(preview_path, save_all=True, append_images=preview_pages[1:])
    return out_path, preview_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="a PDF file, or a folder of PDFs to batch-process")
    parser.add_argument("output_dir", nargs="?", default="redacted_output")
    parser.add_argument("--style", choices=["box", "blur"], default=None, help="override REDACT_STYLE")
    args = parser.parse_args()

    global REDACT_STYLE
    if args.style:
        REDACT_STYLE = args.style

    input_path = Path(args.input)
    targets = sorted(input_path.glob("*.pdf")) if input_path.is_dir() else [input_path]
    if not targets:
        print(f"No PDFs found at {input_path}")
        return

    for pdf_path in targets:
        print(f"Processing {pdf_path.name} ...")
        out, preview = process_pdf(pdf_path, args.output_dir)
        print(f"  -> {out}")
        print(f"  -> {preview}  (check this first!)")


if __name__ == "__main__":
    main()