from llama_cloud import LlamaCloud
from dotenv import load_dotenv
import os
import json

load_dotenv(dotenv_path="D:/projects/extraction/.env")

client = LlamaCloud()

# Upload and parse document
file = client.files.create(
    file=r"D:\rapports\constats\blurred_constats\constat_blurred2.pdf",
    purpose="parse"
)

result = client.parsing.parse(
    file_id=file.id,
    tier="agentic",
    version="latest",
    expand=["markdown"],
)

# =========================================================================================================================================
# BUILD JSON OUTPUT
# =========================

output = {
    "file_id": file.id,
    "pages": []
}

for i, page in enumerate(result.markdown.pages):
    output["pages"].append({
        "page_number": i + 1,
        "markdown": page.markdown
    })

# =========================
# SAVE TO JSON FILE
# =========================

output_path = "constat_output.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Saved JSON to {output_path}")