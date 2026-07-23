import fitz  # PyMuPDF

PDF_PATH = r"D:\rapports\constats\constat5.pdf"
OUTPUT_PDF = r"D:\rapports\constats\blurred_constats\constat_blurred5.pdf"

# Same coordinates for all pages (PDF coords, NOT pixels)
REGIONS = [
    (30, 200, 580, 480),   # example: adjust once
    
]

def main():
    doc = fitz.open(PDF_PATH)

    for page in doc:
        for (x1, y1, x2, y2) in REGIONS:
            rect = fitz.Rect(x1, y1, x2, y2)

            # 🔴 true black box (better than draw_rect)
            page.add_redact_annot(rect, fill=(0, 0, 0))

        # apply redaction permanently
        page.apply_redactions()

    doc.save(OUTPUT_PDF)
    doc.close()

    print("✅ Saved blurred constat:", OUTPUT_PDF)


if __name__ == "__main__":
    main()