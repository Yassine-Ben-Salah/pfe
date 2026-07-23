"""
build_index.py — FAISS + BM25 indexer (updated for new extractor output)
Changes vs previous version:
  - Reads individual JSON files from output folder (one per rapport)
  - semantic_text now includes price_items designations for better keyword recall
  - BM25 tokenizes both damage text AND part designations
  - Metadata stores all new fields (total_net, total_ht, tva, price_items)
"""

import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


# =============================================================================
# CONFIG — point this at your output folder from extract_rapports.py
# =============================================================================
OUTPUT_FOLDER = r"D:\rapports_outvf4"   # folder containing the per-rapport JSONs


# =============================================================================
# LOAD DATA  — reads every .json except _index.json
# =============================================================================
rapports = []
for filename in sorted(os.listdir(OUTPUT_FOLDER)):
    if not filename.endswith(".json") or filename.startswith("_"):
        continue
    path = os.path.join(OUTPUT_FOLDER, filename)
    with open(path, "r", encoding="utf-8") as f:
        try:
            rapports.append(json.load(f))
        except Exception as e:
            print(f"  ⚠ Could not load {filename}: {e}")

print(f"Loaded {len(rapports)} rapports")


# =============================================================================
# NORMALIZATION
# =============================================================================
REPLACEMENTS = {
    "pare-chocs":  "pare choc",
    "parechoc":    "pare choc",
    "p/choc":      "pare choc",
    "pchoc":       "pare choc",
    "pare-choc":   "pare choc",
    "optique":     "phare",
    "feux":        "phare",
    "feu avant":   "phare avant",
    "feu arriere": "phare arriere",
    "av.":         "avant",
    " av ":        " avant ",
    "ar.":         "arriere",
    " ar ":        " arriere ",
    "porte av":    "porte avant",
    "porte ar":    "porte arriere",
    "aile av":     "aile avant",
    "aile ar":     "aile arriere",
    "g.":          "gauche",
    " g ":         " gauche ",
    "d.":          "droite",
    " d ":         " droite ",
    "gche":        "gauche",
    "gch":         "gauche",
    "dte":         "droite",
    "drt":         "droite",
    "brise glace": "pare brise",
    "brise-glace": "pare brise",
    "br glace":    "pare brise",
    "vitre av":    "pare brise",
    "rtrv":        "retroviseur",
    "retro":       "retroviseur",
    "capot av":    "capot avant",
    "capot ar":    "coffre",
    "malle":       "coffre",
}

def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    for src, dst in sorted(REPLACEMENTS.items(), key=lambda x: -len(x[0])):
        text = text.replace(src, dst)
    return " ".join(text.split())


# =============================================================================
# SEMANTIC TEXT BUILDER
# Combines: marque + type + damage_text + price_items designations
# This gives the embedding model full context about what was damaged and
# what parts were ordered/priced — previously only damage_text was used.
# =============================================================================
def build_semantic_text(r: dict) -> str:
    parts = []

    if r.get("marque"):
        parts.append(r["marque"].strip())
    if r.get("type"):
        parts.append(r["type"].strip())
    if r.get("damage_text"):
        parts.append(normalize(r["damage_text"]))

    # NEW: include part designations from the price table
    for item in r.get("price_items", []):
        desig = item.get("designation", "").strip()
        if desig:
            parts.append(normalize(desig))

    return " ".join(parts)


def build_bm25_text(r: dict) -> str:
    """
    For BM25 (keyword matching), combine damage text + part designations.
    Keeps it focused on what was physically damaged/replaced.
    """
    parts = []
    if r.get("damage_text"):
        parts.append(normalize(r["damage_text"]))
    for item in r.get("price_items", []):
        desig = item.get("designation", "").strip()
        if desig:
            parts.append(normalize(desig))
    return " ".join(parts)


# =============================================================================
# FILTER & PREPARE
# =============================================================================
rapports_valid = []
texts = []

for r in rapports:
    semantic = build_semantic_text(r)
    if not semantic.strip():
        print(f"  ⚠ Skipped (no text): {r.get('filename')}")
        continue

    r["_semantic_text"]     = semantic
    r["_normalized_damage"] = build_bm25_text(r)
    rapports_valid.append(r)
    texts.append(semantic)

print(f"✓ {len(rapports_valid)} rapports ready for indexing")


# =============================================================================
# EMBEDDING MODEL
# =============================================================================
print("Loading embedding model...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# =============================================================================
# FAISS INDEX  (cosine similarity via normalized dot product)
# =============================================================================
print("Embedding texts...")
embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True,
    batch_size=64,
)
embeddings = np.array(embeddings, dtype="float32")

dimension = embeddings.shape[1]
faiss_index = faiss.IndexFlatIP(dimension)
faiss_index.add(embeddings)

print(f"✓ FAISS index: {faiss_index.ntotal} vectors, dim={dimension}")


# =============================================================================
# BM25 INDEX
# =============================================================================
print("Building BM25 index...")
tokenized_corpus = [r["_normalized_damage"].split() for r in rapports_valid]
bm25_index = BM25Okapi(tokenized_corpus)
print("✓ BM25 index ready")


# =============================================================================
# SAVE
# =============================================================================
faiss.write_index(faiss_index, "rapports.index")

with open("rapports_meta.pkl", "wb") as f:
    pickle.dump(rapports_valid, f)

with open("rapports_bm25.pkl", "wb") as f:
    pickle.dump(bm25_index, f)

print("\n✅ All indexes saved:")
print("   rapports.index      — FAISS cosine index")
print("   rapports_meta.pkl   — metadata (includes price_items, totals)")
print("   rapports_bm25.pkl   — BM25 keyword index")