"""
main.py — FastAPI wrapper for the hybrid rapport search engine
Run with: uvicorn main:app --reload
"""

import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import fitz
import os
import uuid
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import uuid
from llama_cloud import LlamaCloud
from dotenv import load_dotenv
import os
import json
from fastapi import Body
from groq import Groq
from agent import run_claim_analysis

import asyncio
# Import your existing search module
from search import search_hybrid, search_semantic, print_results, normalize

from ultralytics import YOLO
damage_model = YOLO("best.pt")
# ==========================================================================
# APP SETUP
# ==========================================================================
app = FastAPI(
    title="Rapport Search API",
    description="Hybrid semantic + BM25 search engine for insurance damage reports",
    version="1.0.0",
)

# Allow all origins for local dev — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "blurred"
load_dotenv(dotenv_path="D:/projects/pfe/backend/.env")
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
client = LlamaCloud()
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


REGIONS = [
    (30, 200, 580, 480),
]

# =============================================================================
# SCHEMAS
# =============================================================================
class PriceItem(BaseModel):
    designation: Optional[str] = None
    prix_unitaire: Optional[str] = None
    montant: Optional[str] = None


class RapportResult(BaseModel):
    filename: Optional[str] = None
    score: Optional[float] = None
    marque: Optional[str] = None
    type: Optional[str] = None
    immatriculation: Optional[str] = None
    assure: Optional[str] = None
    date_accident: Optional[str] = None
    numero_dossier: Optional[str] = None
    damage_text: Optional[str] = None
    price_items: Optional[list[PriceItem]] = None
    total_ht: Optional[str] = None
    tva: Optional[str] = None
    total_net: Optional[str] = None
    total_ttc: Optional[str] = None


class SearchRequest(BaseModel):
    marque: Optional[str] = Field(None, description="Vehicle brand (e.g. Peugeot, Renault)")
    type: Optional[str] = None
    assurance: Optional[str] = None 
    damage_query: Optional[str] = Field(None, description="Free-text damage description")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    semantic_weight: float = Field(0.6, ge=0.0, le=1.0)
    bm25_weight: float = Field(0.4, ge=0.0, le=1.0)
    rerank: bool = Field(False, description="Use cross-encoder reranking (slower but more accurate)")
    score_threshold: Optional[float] = Field(None, description="Minimum score filter")


class SearchResponse(BaseModel):
    total: int
    results: list[RapportResult]

class ExtractFieldsRequest(BaseModel):
    text: str

# =============================================================================
# ROUTES
# =============================================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "Rapport Search API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not req.marque and not req.damage_query:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 'marque' or 'damage_query'."
        )

    results = search_hybrid(
        marque=req.marque,
        type=req.type,
        assurance=req.assurance,
        damage_query=req.damage_query,
        top_k=req.top_k,
        semantic_weight=req.semantic_weight,
        bm25_weight=req.bm25_weight,
        rerank=req.rerank,
        score_threshold=req.score_threshold,
    )

    return SearchResponse(total=len(results), results=results)


@app.get("/search", response_model=SearchResponse)
def search_get(
    marque: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None, alias="type"),  # ← rename to avoid shadowing builtin
    assurance: Optional[str] = Query(None),                   # ← was missing
    damage_query: Optional[str] = Query(None),
    top_k: int = Query(5, ge=1, le=50),
    rerank: bool = Query(False),
    score_threshold: Optional[float] = Query(None),
):
    results = search_hybrid(
        marque=marque,
        type=vehicle_type,      # ← was passing Python's builtin type()
        assurance=assurance,    # ← was missing
        damage_query=damage_query,
        top_k=top_k,
        rerank=rerank,
        score_threshold=score_threshold,
    )
    return SearchResponse(total=len(results), results=results)


@app.get("/search/semantic", response_model=SearchResponse)
def search_semantic_endpoint(
    q: str = Query(..., description="Semantic query"),
    top_k: int = Query(5, ge=1, le=50),
):
    results = search_semantic(damage_query=q, top_k=top_k)
    return SearchResponse(total=len(results), results=results)


@app.post("/blur-pdf")
async def blur_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    uid = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{uid}.pdf")
    output_path = os.path.join(OUTPUT_DIR, f"{uid}_blurred.pdf")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    doc = fitz.open(input_path)
    for page in doc:
        for (x1, y1, x2, y2) in REGIONS:
            rect = fitz.Rect(x1, y1, x2, y2)
            page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()

    doc.save(output_path)
    doc.close()

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="blurred.pdf"
    )


@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    uid = str(uuid.uuid4())
    temp_path = f"temp_{uid}.pdf"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    uploaded = client.files.create(file=temp_path, purpose="parse")
    result = client.parsing.parse(
        file_id=uploaded.id,
        tier="agentic",
        version="latest",
        expand=["markdown"],
    )

    output = {"file_id": uploaded.id, "pages": []}
    for i, page in enumerate(result.markdown.pages):
        output["pages"].append({"page_number": i + 1, "markdown": page.markdown})

    os.remove(temp_path)
    return JSONResponse(content=output)


@app.post("/process-constat")
async def process_constat(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    uid = str(uuid.uuid4())
    input_path = f"input_{uid}.pdf"
    blurred_path = f"blurred_{uid}.pdf"

    try:
        with open(input_path, "wb") as f:
            f.write(await file.read())

        doc = fitz.open(input_path)
        for page in doc:
            for (x1, y1, x2, y2) in REGIONS:
                rect = fitz.Rect(x1, y1, x2, y2)
                page.add_redact_annot(rect, fill=(0, 0, 0))
            page.apply_redactions()
        doc.save(blurred_path)
        doc.close()

        uploaded = client.files.create(file=blurred_path, purpose="parse")
        result = client.parsing.parse(
            file_id=uploaded.id,
            tier="agentic",
            version="latest",
            expand=["markdown"],
        )

        full_text = "\n\n".join(page.markdown for page in result.markdown.pages)

        return JSONResponse(content={
            "file_id": uploaded.id,
            "full_text": full_text,
            "page_count": len(result.markdown.pages),
            "blurred_pdf_url": f"http://localhost:8000/view-blurred/{os.path.basename(blurred_path)}",
        })
    

    finally:         
        if os.path.exists(input_path):
            os.remove(input_path)
        pass


# =============================================================================
# FULL TEXT ENDPOINT
# =============================================================================


@app.get("/view-blurred/{filename}")
async def view_blurred(filename: str):
    path = filename

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        media_type="application/pdf"
    )

@app.post("/extract-clean")
def extract_clean(payload: dict = Body(...)):
    """
    Return the raw markdown produced by LlamaParse.
    No field extraction.
    """

    pages = []

    for page in payload.get("pages", []):
        pages.append({
            "page_number": page.get("page_number"),
            "markdown": page.get("markdown", "")
        })

    full_text = "\n\n".join(
        page.get("markdown", "")
        for page in payload.get("pages", [])
    )

    return {
        "total_pages": len(pages),
        "full_text": full_text,
        "pages": pages
    }
@app.post("/detect-damage")
async def detect_damage(file: UploadFile = File(...)):

    temp_file = f"temp_{uuid.uuid4()}.jpg"

    with open(temp_file, "wb") as f:
        f.write(await file.read())

    results = damage_model(temp_file)

    detections = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            detections.append({
                "class": damage_model.names[cls],
                "confidence": conf
            })

    os.remove(temp_file)

    return {"detections": detections}
@app.post("/extract-fields")
async def extract_fields(req: ExtractFieldsRequest):
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{
            "role": "user",
            "content": f"""You are a data extraction tool. Extract fields from this French insurance constat.

STRICT RULES:
- Return ONLY a JSON object, nothing else
- Use EXACTLY these keys, no more, no less
- Set a field to null if not found

{{
  "date_accident": null,
  "heure": null,
  "lieu": null,
  "blesses": null,
  "vehicule_a_marque": null,
  "vehicule_a_type": null,
  "vehicule_a_immatriculation": null,
  "assurance_a": null,       
  "assurance_b": null,   
  "vehicule_b_marque": null,
  "vehicule_b_type": null,
  "vehicule_b_immatriculation": null,
  "degats_vehicule_a": null,
  "degats_vehicule_b": null,
  "observations": null
}}

Document:
{req.text}"""
        }]
    )
    text = completion.choices[0].message.content or "{}"
    clean = text.replace("```json", "").replace("```", "").strip()
    
    print("RAW MODEL OUTPUT:", clean)   # ← add this
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print("JSON parse error:", e)
        raise HTTPException(status_code=500, detail=f"Model returned invalid JSON: {clean}")


@app.post("/analyze-constat")
async def analyze_constat(payload: dict = Body(...)):
    full_text = payload.get("full_text")
    if not full_text:
        raise HTTPException(status_code=400, detail="No full_text provided")
    try:
        report = await asyncio.to_thread(run_claim_analysis, full_text)
        return JSONResponse(content=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)