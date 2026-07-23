"""
train_tokenizer.py
------------------
Trains a BPE tokenizer on all text fields from the rapport JSONs.

Text sources used:
  - damage_text
  - semantic_text
  - price_items designations
  - marque, type, assure, immatriculation, numero_dossier

Output files:
  - tokenizer/vocab.json      — token → id mapping
  - tokenizer/merges.txt      — BPE merge rules
  - tokenizer/tokenizer.json  — full HuggingFace-compatible config

Usage:
  pip install tokenizers
  python train_tokenizer.py
"""

import os
import json
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.normalizers import NFD, Lowercase, StripAccents, Sequence
from tokenizers.processors import TemplateProcessing


# =============================================================================
# CONFIG
# =============================================================================
INPUT_FILE   = r"D:\rapports_out\_index.json"   # master JSON from extractor
OUTPUT_DIR   = r"D:\rapports_out\tokenizer"     # where to save tokenizer files
VOCAB_SIZE   = 8000
MIN_FREQ     = 1   # low because dataset is small


# =============================================================================
# SPECIAL TOKENS
# =============================================================================
# These are used later by the transformer:
#   [PAD]  — padding to fixed length
#   [UNK]  — unknown token
#   [BOS]  — beginning of sequence (decoder input)
#   [EOS]  — end of sequence (generation stop signal)
#   [SEP]  — separates context fields in encoder input
#   [MASK] — for masked language modelling (optional, good to have)

SPECIAL_TOKENS = ["[PAD]", "[UNK]", "[BOS]", "[EOS]", "[SEP]", "[MASK]"]


# =============================================================================
# TEXT EXTRACTION — collect ALL text from every field
# =============================================================================

def extract_all_text(data: list[dict]) -> list[str]:
    """
    Extract every piece of text from the rapport JSONs.
    Returns a flat list of strings (one per field value or item).
    """
    texts = []

    for r in data:
        # Free-text fields
        for field in ["damage_text", "semantic_text"]:
            val = r.get(field)
            if val and isinstance(val, str):
                texts.append(val.strip())

        # Identity fields
        for field in ["marque", "type", "assure", "immatriculation",
                      "numero_dossier", "date_accident"]:
            val = r.get(field)
            if val and isinstance(val, str):
                texts.append(val.strip())

        # Price item designations
        for item in r.get("price_items", []):
            desig = item.get("designation", "").strip()
            if desig:
                texts.append(desig)

        # Numeric totals as strings (so the model learns number tokens)
        for field in ["total_ht", "tva", "total_net", "total_ttc"]:
            val = r.get(field)
            if val and isinstance(val, str):
                texts.append(val.strip())

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


# =============================================================================
# LOAD DATA
# =============================================================================
print(f"Loading data from: {INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    data = [data]

print(f"  {len(data)} rapports loaded")

texts = extract_all_text(data)
print(f"  {len(texts)} unique text samples extracted")


# =============================================================================
# WRITE TEMP CORPUS FILE
# (HuggingFace tokenizers trainer reads from files, not lists)
# =============================================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)
corpus_path = os.path.join(OUTPUT_DIR, "_corpus.txt")

with open(corpus_path, "w", encoding="utf-8") as f:
    for line in texts:
        f.write(line + "\n")

print(f"  Corpus written → {corpus_path}  ({len(texts)} lines)")


# =============================================================================
# BUILD & TRAIN TOKENIZER
# =============================================================================
print("\nTraining BPE tokenizer...")

# 1. Model: BPE with unknown token
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))

# 2. Normalizer: NFD → lowercase → strip accents
#    We keep accents for French (é, è, ê are meaningful), so StripAccents is OFF
#    If you want accent-insensitive matching, uncomment StripAccents below.
tokenizer.normalizer = Sequence([
    NFD(),
    Lowercase(),
    # StripAccents(),   # ← uncomment to fold accents
])

# 3. Pre-tokenizer: split on whitespace
#    For a domain with lots of hyphenated terms (pare-chocs, avant-gauche),
#    Whitespace is safer than ByteLevel (which would split hyphens).
tokenizer.pre_tokenizer = Whitespace()

# 4. Trainer
trainer = BpeTrainer(
    vocab_size=VOCAB_SIZE,
    min_frequency=MIN_FREQ,
    special_tokens=SPECIAL_TOKENS,
    show_progress=True,
)

# 5. Train
tokenizer.train(files=[corpus_path], trainer=trainer)

print(f"  ✓ Trained — vocab size: {tokenizer.get_vocab_size()}")


# =============================================================================
# POST-PROCESSOR: auto-add [BOS] and [EOS] around every encoded sequence
# =============================================================================
bos_id = tokenizer.token_to_id("[BOS]")
eos_id = tokenizer.token_to_id("[EOS]")

tokenizer.post_processor = TemplateProcessing(
    single="[BOS] $A [EOS]",
    pair="[BOS] $A [SEP] $B [EOS]",
    special_tokens=[
        ("[BOS]", bos_id),
        ("[EOS]", eos_id),
        ("[SEP]", tokenizer.token_to_id("[SEP]")),
    ],
)


# =============================================================================
# SAVE
# =============================================================================
tokenizer_path = os.path.join(OUTPUT_DIR, "tokenizer.json")
tokenizer.save(tokenizer_path)
print(f"  ✓ Saved → {tokenizer_path}")

# Also save vocab separately for easy inspection
vocab = tokenizer.get_vocab()
vocab_sorted = dict(sorted(vocab.items(), key=lambda x: x[1]))
vocab_path = os.path.join(OUTPUT_DIR, "vocab.json")
with open(vocab_path, "w", encoding="utf-8") as f:
    json.dump(vocab_sorted, f, ensure_ascii=False, indent=2)
print(f"  ✓ Vocab saved → {vocab_path}")


# =============================================================================
# QUICK SANITY CHECK
# =============================================================================
print("\n── Sanity check ──────────────────────────────────────")

test_sentences = [
    "Pare-chocs avant gauche cassé et déformé",
    "Aile avant gauche entassée et cabossée",
    "Remplacement des pièces en fourniture",
    "Total NET : 1811.025 DT",
    "CITROEN Optique avant gauche",
]

for s in test_sentences:
    encoded = tokenizer.encode(s)
    decoded = tokenizer.decode(encoded.ids)
    print(f"\n  Input  : {s}")
    print(f"  Tokens : {encoded.tokens}")
    print(f"  IDs    : {encoded.ids}")
    print(f"  Decoded: {decoded}")

print("\n──────────────────────────────────────────────────────")
print(f"Special token IDs:")
for tok in SPECIAL_TOKENS:
    print(f"  {tok:8s} → {tokenizer.token_to_id(tok)}")

print(f"\n✅ Tokenizer ready in: {OUTPUT_DIR}")
print(f"   vocab_size = {tokenizer.get_vocab_size()}")
print(f"\nNext step: train_transformer.py  (uses this tokenizer)")