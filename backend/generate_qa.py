"""
generate_qa.py
--------------
Automatically generates question/answer pairs from your rapport JSONs.
These will be used to fine-tune mT5-small in finetune.py.

For each rapport, generates questions about:
  - Car identity (marque, type, immatriculation)
  - Owner (assure)
  - Damage description
  - Price items
  - Totals (HT, TVA, NET, TTC)
  - Dossier / date

Output:
  qa_pairs.json  — list of {context, question, answer} dicts

Usage:
  python generate_qa.py
"""

import os
import json
import random

# =============================================================================
# CONFIG
# =============================================================================
INPUT_FILE  = r"D:\rapports_out\_index.json"   # your master index
OUTPUT_FILE = r"D:\rapports_out\qa_pairs.json" # where to save QA pairs


# =============================================================================
# QUESTION TEMPLATES
# One function per field — returns (question, answer) or None if field missing
# =============================================================================

def qa_marque(r):
    if not r.get("marque"):
        return None
    qs = [
        "Quelle est la marque du véhicule ?",
        "De quelle marque est la voiture ?",
        "Quel est le constructeur du véhicule ?",
    ]
    return random.choice(qs), r["marque"].strip()


def qa_type(r):
    if not r.get("type"):
        return None
    qs = [
        "Quel est le type ou modèle du véhicule ?",
        "Quel modèle de voiture est mentionné ?",
        "Quel est le type du véhicule accidenté ?",
    ]
    return random.choice(qs), r["type"].strip()


def qa_immat(r):
    if not r.get("immatriculation"):
        return None
    qs = [
        "Quelle est l'immatriculation du véhicule ?",
        "Quel est le numéro d'immatriculation ?",
        "Donnez-moi la plaque d'immatriculation.",
    ]
    return random.choice(qs), r["immatriculation"].strip()


def qa_assure(r):
    if not r.get("assure"):
        return None
    qs = [
        "Qui est l'assuré ?",
        "Quel est le nom du propriétaire du véhicule ?",
        "Comment s'appelle l'assuré ?",
    ]
    return random.choice(qs), r["assure"].strip()


def qa_dossier(r):
    if not r.get("numero_dossier"):
        return None
    qs = [
        "Quel est le numéro de dossier ?",
        "Donnez-moi la référence du dossier.",
        "Quel est le numéro du rapport d'expertise ?",
    ]
    return random.choice(qs), r["numero_dossier"].strip()


def qa_date(r):
    if not r.get("date_accident"):
        return None
    qs = [
        "Quelle est la date de l'accident ?",
        "Quand a eu lieu le sinistre ?",
        "À quelle date s'est produit l'accident ?",
    ]
    return random.choice(qs), r["date_accident"].strip()


def qa_damage(r):
    if not r.get("damage_text"):
        return None
    qs = [
        "Quels sont les dommages constatés sur le véhicule ?",
        "Décrivez les dégâts du véhicule.",
        "Quelles parties du véhicule sont endommagées ?",
        "Quel est l'état du véhicule après l'accident ?",
    ]
    return random.choice(qs), r["damage_text"].strip()


def qa_total_ttc(r):
    if not r.get("total_ttc"):
        return None
    qs = [
        "Quel est le montant total TTC ?",
        "Combien coûte la réparation toutes taxes comprises ?",
        "Quel est le total TTC de la facture ?",
    ]
    return random.choice(qs), f"{r['total_ttc']} DT"


def qa_total_ht(r):
    if not r.get("total_ht"):
        return None
    qs = [
        "Quel est le total hors taxes ?",
        "Quel est le montant HT de la réparation ?",
    ]
    return random.choice(qs), f"{r['total_ht']} DT"


def qa_tva(r):
    if not r.get("tva"):
        return None
    qs = [
        "Quel est le montant de la TVA ?",
        "Combien représente la TVA dans ce rapport ?",
    ]
    return random.choice(qs), f"{r['tva']} DT"


def qa_total_net(r):
    if not r.get("total_net"):
        return None
    qs = [
        "Quel est le total net ?",
        "Quel est le montant net de la réparation ?",
    ]
    return random.choice(qs), f"{r['total_net']} DT"


def qa_price_items(r):
    """Ask about a specific part from the price table."""
    items = r.get("price_items", [])
    if not items:
        return None

    item = random.choice(items)
    desig = item.get("designation", "").strip()
    montant = item.get("montant", "").strip()
    pu = item.get("prix_unitaire", "").strip()

    if not desig or not montant:
        return None

    qs = [
        f"Quel est le montant pour '{desig}' ?",
        f"Combien coûte '{desig}' dans ce rapport ?",
        f"Quel est le prix de '{desig}' ?",
    ]

    answer = montant + " DT"
    if pu:
        answer = f"Prix unitaire : {pu} DT, Montant : {montant} DT"

    return random.choice(qs), answer


def qa_marque_immat(r):
    """Combined: find rapport by marque + immat."""
    if not r.get("marque") or not r.get("immatriculation"):
        return None
    qs = [
        f"Quel est le rapport pour le véhicule {r['marque']} immatriculé {r['immatriculation']} ?",
        f"Donne-moi les informations du dossier {r.get('numero_dossier', '')} pour {r['marque']} {r.get('type', '')}.",
        f"Quel est l'assuré du véhicule {r['marque']} {r['immatriculation']} ?",
    ]
    q = random.choice(qs)

    # Build a rich answer
    parts = []
    if r.get("assure"):
        parts.append(f"Assuré : {r['assure']}")
    if r.get("date_accident"):
        parts.append(f"Date accident : {r['date_accident']}")
    if r.get("damage_text"):
        parts.append(f"Dommages : {r['damage_text'][:120]}")
    if r.get("total_ttc"):
        parts.append(f"Total TTC : {r['total_ttc']} DT")

    return q, " | ".join(parts) if parts else f"{r['marque']} {r.get('type', '')} — {r.get('immatriculation', '')}"


# =============================================================================
# ALL GENERATORS
# =============================================================================
GENERATORS = [
    qa_marque,
    qa_type,
    qa_immat,
    qa_assure,
    qa_dossier,
    qa_date,
    qa_damage,
    qa_total_ttc,
    qa_total_ht,
    qa_tva,
    qa_total_net,
    qa_price_items,
    qa_price_items,   # listed twice = sampled more often
    qa_marque_immat,
    qa_marque_immat,
]


# =============================================================================
# BUILD CONTEXT STRING
# Feeds the model everything it needs to answer questions about this rapport
# =============================================================================
def build_context(r: dict) -> str:
    parts = []

    if r.get("marque"):
        parts.append(f"Marque: {r['marque']}")
    if r.get("type"):
        parts.append(f"Type: {r['type']}")
    if r.get("immatriculation"):
        parts.append(f"Immatriculation: {r['immatriculation']}")
    if r.get("assure"):
        parts.append(f"Assuré: {r['assure']}")
    if r.get("numero_dossier"):
        parts.append(f"Dossier: {r['numero_dossier']}")
    if r.get("date_accident"):
        parts.append(f"Date accident: {r['date_accident']}")
    if r.get("damage_text"):
        parts.append(f"Dommages: {r['damage_text']}")

    # Price items
    items = r.get("price_items", [])
    if items:
        item_lines = []
        for item in items:
            desig  = item.get("designation", "")
            pu     = item.get("prix_unitaire", "")
            montant = item.get("montant", "")
            item_lines.append(f"{desig} | PU: {pu} | Montant: {montant}")
        parts.append("Pièces: " + " ; ".join(item_lines))

    # Totals
    if r.get("total_ht"):
        parts.append(f"Total HT: {r['total_ht']} DT")
    if r.get("tva"):
        parts.append(f"TVA: {r['tva']} DT")
    if r.get("total_net"):
        parts.append(f"Total NET: {r['total_net']} DT")
    if r.get("total_ttc"):
        parts.append(f"Total TTC: {r['total_ttc']} DT")

    return " | ".join(parts)


# =============================================================================
# GENERATE
# =============================================================================
def generate_pairs(rapports: list[dict], pairs_per_rapport: int = 20) -> list[dict]:
    pairs = []
    random.seed(42)

    for r in rapports:
        context = build_context(r)
        generated_for_this = 0
        attempts = 0

        # Shuffle generators so we get variety
        gens = GENERATORS.copy()
        random.shuffle(gens)

        while generated_for_this < pairs_per_rapport and attempts < pairs_per_rapport * 5:
            gen = random.choice(GENERATORS)
            result = gen(r)
            attempts += 1

            if result is None:
                continue

            question, answer = result

            pairs.append({
                "context":  context,
                "question": question,
                "answer":   answer,
                "source":   r.get("filename", "unknown"),
            })
            generated_for_this += 1

    return pairs


# =============================================================================
# MAIN
# =============================================================================
print(f"Loading rapports from: {INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    data = [data]

print(f"  {len(data)} rapports loaded")

pairs = generate_pairs(data, pairs_per_rapport=20)
print(f"  {len(pairs)} QA pairs generated")

# Save
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(pairs, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved → {OUTPUT_FILE}")

# Preview
print("\n── Sample QA pairs ───────────────────────────────────────")
for p in random.sample(pairs, min(5, len(pairs))):
    print(f"\n  Source  : {p['source']}")
    print(f"  Q: {p['question']}")
    print(f"  A: {p['answer']}")
print("\n──────────────────────────────────────────────────────────")
print(f"\nNext step: finetune.py  (uses qa_pairs.json to train mT5-small)")