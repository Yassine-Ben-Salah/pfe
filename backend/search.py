"""
search.py — Hybrid search engine (updated for new extractor output)
Changes:
  - print_results shows total_net, total_ht, tva, and price_items table
  - _strip_internals preserves all new fields
  - __main__ reads per-rapport JSONs folder (like build_index.py) instead of cleaned.json
"""

import os
import json
import unicodedata
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer, CrossEncoder


# =============================================================================
# NORMALIZATION
# =============================================================================
REPLACEMENTS = {
    "pare-chocs":  "pare choc",
    "parechoc":    "pare choc",
    "p/choc":      "pare choc",
    "pchoc":       "pare choc",
    "pare-choc":   "pare choc",
    "pc":          "pare choc",
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
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    for src, dst in sorted(REPLACEMENTS.items(), key=lambda x: -len(x[0])):
        text = text.replace(src, dst)
    return " ".join(text.split())


# =============================================================================
# LOAD INDEXES
# =============================================================================
print("Loading indexes and models...")

faiss_index = faiss.read_index("rapports.index")

with open("rapports_meta.pkl", "rb") as f:
    rapports = pickle.load(f)

with open("rapports_bm25.pkl", "rb") as f:
    bm25_index = pickle.load(f)

bi_encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

_cross_encoder = None

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        print("Loading cross-encoder (first use)...")
        _cross_encoder = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=256,
        )
    return _cross_encoder

print(f"✓ Ready — {faiss_index.ntotal} rapports indexed\n")


# =============================================================================
# SEMANTIC SEARCH
# =============================================================================
def search_semantic(damage_query: str, top_k: int = 5) -> list[dict]:
    q = normalize(damage_query)
    q_vec = bi_encoder.encode([q], normalize_embeddings=True)
    q_vec = np.array(q_vec, dtype="float32")

    distances, indices = faiss_index.search(q_vec, top_k)

    results = []
    for score, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append({**rapports[idx], "score": round(float(score), 4)})

    return results


# =============================================================================
# HYBRID SEARCH
# =============================================================================
def search_hybrid(
    marque: str | None = None,
    type: str | None = None,        # ← add
    assurance: str | None = None,   # ← add
    damage_query: str | None = None,
    top_k: int = 5,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
    rerank: bool = False,
    score_threshold: float | None = None,
) -> list[dict]:
    if not marque and not damage_query and not type and not assurance:
        print("Provide at least marque, type, assurance or damage_query.")
        return []

    q = normalize(damage_query or "")
    q_tokens = q.split()
    q_vec = bi_encoder.encode([q or "dommage"], normalize_embeddings=True)
    q_vec = np.array(q_vec, dtype="float32")

    pool_size = min(top_k * 20, len(rapports))
    sem_distances, sem_indices = faiss_index.search(q_vec, pool_size)

    sem_scores = {
        int(idx): float(score)
        for score, idx in zip(sem_distances[0], sem_indices[0])
        if idx != -1
    }

    if q_tokens:
        bm25_raw = bm25_index.get_scores(q_tokens)
        bm25_max = bm25_raw.max() or 1.0
        bm25_norm = bm25_raw / bm25_max
    else:
        bm25_norm = np.zeros(len(rapports))

    q_marque    = normalize(marque)    if marque    else None
    q_type      = normalize(type)      if type      else None      # ← add
    q_assurance = normalize(assurance) if assurance else None      # ← add

    candidates = []
    for idx, sem_score in sem_scores.items():
        r = rapports[idx]

        if q_marque:
            if q_marque not in normalize(r.get("marque", "")):
                continue

        if q_type:                                                  # ← add
            if q_type not in normalize(r.get("type", "")):
                continue

        if q_assurance:                                             # ← add
            if q_assurance not in normalize(r.get("assure", "")):
                continue

        bm25_score = float(bm25_norm[idx])
        damage = r.get("_normalized_damage", "")

        side_penalty = 0.0
        if q:
            if "avant" in q and "arriere" in damage and "avant" not in damage:
                side_penalty = 0.08
            elif "arriere" in q and "avant" in damage and "arriere" not in damage:
                side_penalty = 0.08
            if "gauche" in q and "droite" in damage and "gauche" not in damage:
                side_penalty += 0.05
            elif "droite" in q and "gauche" in damage and "droite" not in damage:
                side_penalty += 0.05

        final_score = (
            semantic_weight * sem_score
            + bm25_weight   * bm25_score
            - side_penalty
        )

        candidates.append({**r, "score": round(final_score, 4), "_idx": idx})

    # rest of function unchanged...

    candidates.sort(key=lambda x: x["score"], reverse=True)

    if not rerank:
        if score_threshold is not None:
            candidates = [c for c in candidates if c["score"] >= score_threshold]
        return [_strip_internals(c) for c in candidates[:top_k]]

    top_candidates = candidates[:top_k * 3]
    if not top_candidates:
        return []

    ce = get_cross_encoder()
    pairs = [(q, c.get("_normalized_damage", "")) for c in top_candidates]
    ce_scores = ce.predict(pairs)

    for c, ce_score in zip(top_candidates, ce_scores):
        c["score"] = round(float(ce_score), 4)

    top_candidates.sort(key=lambda x: x["score"], reverse=True)

    if score_threshold is not None:
        top_candidates = [c for c in top_candidates if c["score"] >= score_threshold]

    return [_strip_internals(c) for c in top_candidates[:top_k]]


def _strip_internals(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


# =============================================================================
# DISPLAY  — updated to show price_items and totals
# =============================================================================
def print_results(results: list[dict], mode: str = "") -> None:
    sep = "═" * 66
    print(f"\n{sep}")
    if mode:
        print(f"MODE: {mode}")

    if not results:
        print("❌ No results found")
        print(sep)
        return

    print(f"✅ {len(results)} results\n")

    for i, r in enumerate(results, 1):
        print(f"#{i} 📄 {r.get('filename')}  |  Score: {r.get('score')}")
        print(f"   🚗 {r.get('marque', '—')} {r.get('type', '')}  |  {r.get('immatriculation', '—')}")
        print(f"   👤 {r.get('assure', '—')}  |  📅 {r.get('date_accident', '—')}")
        print(f"   🗂  Dossier: {r.get('numero_dossier', '—')}")

        # Damage description
        damage = (r.get("damage_text") or "")[:140]
        print(f"   🔧 {damage}{'...' if len(r.get('damage_text') or '') > 140 else ''}")

        # Price table
        items = r.get("price_items", [])
        if items:
            print(f"   {'─'*58}")
            print(f"   {'DÉSIGNATION':<35} {'P.U':>10} {'MONTANT':>10}")
            print(f"   {'─'*58}")
            for item in items:
                desig = item.get("designation", "")[:34]
                pu    = item.get("prix_unitaire", "")
                mt    = item.get("montant", "")
                print(f"   {desig:<35} {pu:>10} {mt:>10}")
            print(f"   {'─'*58}")

        # Totals
        total_ht  = r.get("total_ht")
        tva       = r.get("tva")
        total_net = r.get("total_net")
        total_ttc = r.get("total_ttc")

        if any([total_ht, tva, total_net, total_ttc]):
            if total_ht:
                print(f"   💵 Total HT  : {total_ht} DT")
            if tva:
                print(f"   📊 TVA       : {tva} DT")
            if total_net:
                print(f"   💰 Total NET : {total_net} DT")
            if total_ttc:
                print(f"   💰 Total TTC : {total_ttc} DT")

        print()

    print(sep)


# =============================================================================
# MAIN — reads queries from the output folder JSONs
# =============================================================================


if __name__ == "__main__":

    INPUT_FILE = r"D:\projects\extraction\cleaned.json"  # 👈 your JSON file

    # =========================
    # LOAD JSON
    # =========================
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ensure list format
    if isinstance(data, dict):
        queries = [data]
    else:
        queries = data

    print(f"Running search for {len(queries)} queries...\n")

    # =========================
    # PROCESS EACH QUERY
    # =========================
    for i, query in enumerate(queries, 1):

        print(f"\n{'─'*66}")
        print(f"Query #{i}: {query.get('marque', '—')} | {(query.get('damage_text') or '')[:80]}")

        results = search_hybrid(
            marque=query.get("marque"),
            damage_query=query.get("damage_text"),
            top_k=5,
            rerank=True,
            score_threshold=0.0,
        )

        print_results(results, f"RESULT #{i}")