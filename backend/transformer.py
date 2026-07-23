"""
transformer.py
--------------
Small encoder-decoder Transformer built in pure PyTorch.
Sized for:
  - vocab_size  = 592   (from your BPE tokenizer)
  - GPU 4-8 GB VRAM
  - Domain: French insurance rapport d'expertise

Architecture:
  Encoder: reads the context (retrieved rapports)
  Decoder: generates the answer token by token

Usage:
  from transformer import RapportTransformer, TransformerConfig
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass

# =============================================================================
# CONFIG
# =============================================================================
@dataclass
class TransformerConfig:
    """
    All hyperparameters in one place.
    Sized for 4-8 GB VRAM with your 592-token vocab.
    """
    # Vocabulary
    vocab_size    : int   = 592
    pad_id        : int   = 0
    bos_id        : int   = 2
    eos_id        : int   = 3
    sep_id        : int   = 4

    # Sequence lengths
    max_src_len   : int   = 512   # encoder input  (context rapports)
    max_tgt_len   : int   = 128   # decoder output (generated answer)

    # Model dimensions
    d_model       : int   = 256   # embedding / hidden size
    n_heads       : int   = 8     # attention heads  (d_model must be divisible)
    d_ff          : int   = 512   # feed-forward inner dim (usually 2-4x d_model)
    n_enc_layers  : int   = 4     # encoder depth
    n_dec_layers  : int   = 4     # decoder depth

    # Regularisation
    dropout       : float = 0.1

    def __post_init__(self):
        assert self.d_model % self.n_heads == 0, \
            f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"

    def __repr__(self):
        params = self._estimate_params()
        return (
            f"TransformerConfig("
            f"vocab={self.vocab_size}, "
            f"d_model={self.d_model}, "
            f"heads={self.n_heads}, "
            f"enc={self.n_enc_layers}L, "
            f"dec={self.n_dec_layers}L, "
            f"~{params/1e6:.1f}M params)"
        )

    def _estimate_params(self):
        # Rough estimate: embeddings + layers
        emb    = self.vocab_size * self.d_model * 2          # src + tgt embeddings
        enc    = self.n_enc_layers * (
                     4 * self.d_model**2                     # self-attn QKV + O
                   + 2 * self.d_model * self.d_ff            # FFN
                 )
        dec    = self.n_dec_layers * (
                     4 * self.d_model**2                     # self-attn
                   + 4 * self.d_model**2                     # cross-attn
                   + 2 * self.d_model * self.d_ff            # FFN
                 )
        lm_head = self.d_model * self.vocab_size
        return emb + enc + dec + lm_head


# =============================================================================
# POSITIONAL ENCODING
# =============================================================================

class PositionalEncoding(nn.Module):
    """
    Classic sinusoidal positional encoding (Vaswani et al. 2017).
    Adds position information to token embeddings.
    """

    def __init__(self, d_model: int, max_len: int, dropout: float):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # Build the PE matrix once
        pe = torch.zeros(max_len, d_model)                        # (max_len, d_model)
        pos = torch.arange(max_len).unsqueeze(1).float()          # (max_len, 1)
        div = torch.exp(
            torch.arange(0, d_model, 2).float()
            * (-math.log(10000.0) / d_model)
        )                                                          # (d_model/2,)

        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)

        pe = pe.unsqueeze(0)                                       # (1, max_len, d_model)
        self.register_buffer("pe", pe)                            # not a parameter

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, d_model)
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


# =============================================================================
# MULTI-HEAD ATTENTION
# =============================================================================

class MultiHeadAttention(nn.Module):
    """
    Scaled dot-product multi-head attention.
    Used for:
      - Encoder self-attention
      - Decoder self-attention (masked)
      - Decoder cross-attention (attends to encoder output)
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float):
        super().__init__()
        assert d_model % n_heads == 0

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k     = d_model // n_heads   # dimension per head

        self.W_q = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, d_model, bias=False)
        self.W_v = nn.Linear(d_model, d_model, bias=False)
        self.W_o = nn.Linear(d_model, d_model, bias=False)

        self.dropout = nn.Dropout(dropout)
        self.scale   = math.sqrt(self.d_k)

    def _split_heads(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq, d_model) → (batch, heads, seq, d_k)
        B, S, _ = x.shape
        return x.view(B, S, self.n_heads, self.d_k).transpose(1, 2)

    def _merge_heads(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, heads, seq, d_k) → (batch, seq, d_model)
        B, H, S, D = x.shape
        return x.transpose(1, 2).contiguous().view(B, S, H * D)

    def forward(
        self,
        query  : torch.Tensor,
        key    : torch.Tensor,
        value  : torch.Tensor,
        mask   : torch.Tensor | None = None,
    ) -> torch.Tensor:
        Q = self._split_heads(self.W_q(query))   # (B, H, Sq, d_k)
        K = self._split_heads(self.W_k(key))     # (B, H, Sk, d_k)
        V = self._split_heads(self.W_v(value))   # (B, H, Sk, d_k)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale  # (B, H, Sq, Sk)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attn   = self.dropout(F.softmax(scores, dim=-1))
        out    = torch.matmul(attn, V)            # (B, H, Sq, d_k)

        return self.W_o(self._merge_heads(out))   # (B, Sq, d_model)


# =============================================================================
# FEED-FORWARD BLOCK
# =============================================================================

class FeedForward(nn.Module):
    """
    Position-wise feed-forward network.
    FFN(x) = ReLU(xW1 + b1)W2 + b2
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# =============================================================================
# ENCODER LAYER
# =============================================================================

class EncoderLayer(nn.Module):
    """
    One encoder layer:
      x → Self-Attention → Add & Norm → FFN → Add & Norm
    """

    def __init__(self, cfg: TransformerConfig):
        super().__init__()
        self.self_attn  = MultiHeadAttention(cfg.d_model, cfg.n_heads, cfg.dropout)
        self.ffn        = FeedForward(cfg.d_model, cfg.d_ff, cfg.dropout)
        self.norm1      = nn.LayerNorm(cfg.d_model)
        self.norm2      = nn.LayerNorm(cfg.d_model)
        self.dropout    = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor, src_mask: torch.Tensor | None) -> torch.Tensor:
        # Self-attention + residual
        x = self.norm1(x + self.dropout(self.self_attn(x, x, x, src_mask)))
        # FFN + residual
        x = self.norm2(x + self.dropout(self.ffn(x)))
        return x


# =============================================================================
# DECODER LAYER
# =============================================================================

class DecoderLayer(nn.Module):
    """
    One decoder layer:
      x → Masked Self-Attention → Add & Norm
        → Cross-Attention (enc output) → Add & Norm
        → FFN → Add & Norm
    """

    def __init__(self, cfg: TransformerConfig):
        super().__init__()
        self.self_attn  = MultiHeadAttention(cfg.d_model, cfg.n_heads, cfg.dropout)
        self.cross_attn = MultiHeadAttention(cfg.d_model, cfg.n_heads, cfg.dropout)
        self.ffn        = FeedForward(cfg.d_model, cfg.d_ff, cfg.dropout)
        self.norm1      = nn.LayerNorm(cfg.d_model)
        self.norm2      = nn.LayerNorm(cfg.d_model)
        self.norm3      = nn.LayerNorm(cfg.d_model)
        self.dropout    = nn.Dropout(cfg.dropout)

    def forward(
        self,
        x        : torch.Tensor,
        enc_out  : torch.Tensor,
        src_mask : torch.Tensor | None,
        tgt_mask : torch.Tensor | None,
    ) -> torch.Tensor:
        # 1. Masked self-attention (can't look at future tokens)
        x = self.norm1(x + self.dropout(self.self_attn(x, x, x, tgt_mask)))
        # 2. Cross-attention (queries from decoder, keys/values from encoder)
        x = self.norm2(x + self.dropout(self.cross_attn(x, enc_out, enc_out, src_mask)))
        # 3. FFN
        x = self.norm3(x + self.dropout(self.ffn(x)))
        return x


# =============================================================================
# ENCODER
# =============================================================================

class Encoder(nn.Module):

    def __init__(self, cfg: TransformerConfig):
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.d_model, padding_idx=cfg.pad_id)
        self.pos_enc   = PositionalEncoding(cfg.d_model, cfg.max_src_len, cfg.dropout)
        self.layers    = nn.ModuleList([EncoderLayer(cfg) for _ in range(cfg.n_enc_layers)])
        self.norm      = nn.LayerNorm(cfg.d_model)
        self.scale     = math.sqrt(cfg.d_model)

    def forward(self, src: torch.Tensor, src_mask: torch.Tensor | None) -> torch.Tensor:
        # src: (batch, src_len)
        x = self.embedding(src) * self.scale    # scale as in original paper
        x = self.pos_enc(x)
        for layer in self.layers:
            x = layer(x, src_mask)
        return self.norm(x)                     # (batch, src_len, d_model)


# =============================================================================
# DECODER
# =============================================================================

class Decoder(nn.Module):

    def __init__(self, cfg: TransformerConfig):
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.d_model, padding_idx=cfg.pad_id)
        self.pos_enc   = PositionalEncoding(cfg.d_model, cfg.max_tgt_len, cfg.dropout)
        self.layers    = nn.ModuleList([DecoderLayer(cfg) for _ in range(cfg.n_dec_layers)])
        self.norm      = nn.LayerNorm(cfg.d_model)
        self.scale     = math.sqrt(cfg.d_model)

    def forward(
        self,
        tgt      : torch.Tensor,
        enc_out  : torch.Tensor,
        src_mask : torch.Tensor | None,
        tgt_mask : torch.Tensor | None,
    ) -> torch.Tensor:
        # tgt: (batch, tgt_len)
        x = self.embedding(tgt) * self.scale
        x = self.pos_enc(x)
        for layer in self.layers:
            x = layer(x, enc_out, src_mask, tgt_mask)
        return self.norm(x)                     # (batch, tgt_len, d_model)


# =============================================================================
# FULL MODEL
# =============================================================================

class RapportTransformer(nn.Module):
    """
    Encoder-Decoder Transformer for French insurance rapport generation.

    Forward pass (training):
      logits = model(src, tgt)
      loss   = CrossEntropy(logits, tgt_shifted)

    Inference:
      answer_ids = model.generate(src, max_len=128)
    """

    def __init__(self, cfg: TransformerConfig = None):
        super().__init__()
        if cfg is None:
            cfg = TransformerConfig()
        self.cfg     = cfg
        self.encoder = Encoder(cfg)
        self.decoder = Decoder(cfg)
        self.lm_head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)

        # Weight tying: share embedding weights with lm_head
        # Helps small models generalise better
        self.lm_head.weight = self.decoder.embedding.weight

        self._init_weights()

    # ── Weight initialisation ─────────────────────────────────────────────────
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    # ── Mask builders ─────────────────────────────────────────────────────────
    def _src_mask(self, src: torch.Tensor) -> torch.Tensor:
        """
        Padding mask for encoder: 1 where token is real, 0 where [PAD].
        Shape: (batch, 1, 1, src_len) — broadcasts over heads and query positions.
        """
        return (src != self.cfg.pad_id).unsqueeze(1).unsqueeze(2)

    def _tgt_mask(self, tgt: torch.Tensor) -> torch.Tensor:
        """
        Causal + padding mask for decoder.
        Prevents attending to future tokens AND padding.
        Shape: (batch, 1, tgt_len, tgt_len)
        """
        B, T    = tgt.shape
        pad_mask = (tgt != self.cfg.pad_id).unsqueeze(1).unsqueeze(2)  # (B,1,1,T)
        causal   = torch.tril(torch.ones(T, T, device=tgt.device)).bool()  # (T,T)
        return pad_mask & causal                                            # (B,1,T,T)

    # ── Forward (training) ────────────────────────────────────────────────────
    def forward(
        self,
        src: torch.Tensor,   # (batch, src_len)  — encoder input
        tgt: torch.Tensor,   # (batch, tgt_len)  — decoder input (shifted right)
    ) -> torch.Tensor:
        """
        Returns logits of shape (batch, tgt_len, vocab_size).
        Loss = CrossEntropy(logits[:, :-1], tgt[:, 1:])
        """
        src_mask = self._src_mask(src)
        tgt_mask = self._tgt_mask(tgt)

        enc_out  = self.encoder(src, src_mask)
        dec_out  = self.decoder(tgt, enc_out, src_mask, tgt_mask)
        logits   = self.lm_head(dec_out)        # (batch, tgt_len, vocab_size)
        return logits

    # ── Greedy decoding (inference) ───────────────────────────────────────────
    @torch.no_grad()
    def generate(
        self,
        src     : torch.Tensor,
        max_len : int = 128,
        temperature: float = 1.0,
    ) -> list[list[int]]:
        """
        Greedy auto-regressive generation.
        src: (batch, src_len)
        Returns list of token-id lists (one per batch item), without [BOS]/[EOS].
        """
        self.eval()
        device   = src.device
        B        = src.size(0)
        cfg      = self.cfg

        src_mask = self._src_mask(src)
        enc_out  = self.encoder(src, src_mask)

        # Start decoder with [BOS]
        tgt      = torch.full((B, 1), cfg.bos_id, dtype=torch.long, device=device)
        finished = torch.zeros(B, dtype=torch.bool, device=device)
        results  = [[] for _ in range(B)]

        for _ in range(max_len):
            tgt_mask = self._tgt_mask(tgt)
            dec_out  = self.decoder(tgt, enc_out, src_mask, tgt_mask)
            logits   = self.lm_head(dec_out[:, -1, :])   # last position only

            if temperature != 1.0:
                logits = logits / temperature

            next_tok = logits.argmax(dim=-1)              # greedy (B,)

            for i in range(B):
                if not finished[i]:
                    tok = next_tok[i].item()
                    if tok == cfg.eos_id:
                        finished[i] = True
                    else:
                        results[i].append(tok)

            if finished.all():
                break

            tgt = torch.cat([tgt, next_tok.unsqueeze(1)], dim=1)

        return results

    # ── Parameter count ───────────────────────────────────────────────────────
    def count_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing RapportTransformer...\n")

    cfg   = TransformerConfig()
    print(cfg)

    model = RapportTransformer(cfg)
    total = model.count_params()
    print(f"Trainable parameters: {total:,}  (~{total/1e6:.2f}M)\n")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    model  = model.to(device)

    # Fake batch: batch=2, src_len=64, tgt_len=32
    B, SL, TL = 2, 64, 32
    src = torch.randint(6, cfg.vocab_size, (B, SL)).to(device)
    tgt = torch.randint(6, cfg.vocab_size, (B, TL)).to(device)

    # Add some padding
    src[:, -10:] = cfg.pad_id
    tgt[:, -5:]  = cfg.pad_id

    # Forward pass
    logits = model(src, tgt)
    print(f"\nForward pass:")
    print(f"  src shape   : {src.shape}")
    print(f"  tgt shape   : {tgt.shape}")
    print(f"  logits shape: {logits.shape}  (expected: {B, TL, cfg.vocab_size})")

    # Loss computation (teacher forcing)
    loss_fn = nn.CrossEntropyLoss(ignore_index=cfg.pad_id)
    # Shift: predict tgt[1:] from tgt[:-1]
    loss = loss_fn(
        logits[:, :-1].reshape(-1, cfg.vocab_size),
        tgt[:, 1:].reshape(-1),
    )
    print(f"  loss        : {loss.item():.4f}  (random init, ~log({cfg.vocab_size})={math.log(cfg.vocab_size):.2f} expected)")

    # Greedy generation
    generated = model.generate(src, max_len=20)
    print(f"\nGeneration test:")
    for i, seq in enumerate(generated):
        print(f"  Batch {i}: {seq[:10]}{'...' if len(seq)>10 else ''}  (len={len(seq)})")

    print("\n✅ Transformer OK — next step: prepare_dataset.py + train.py")