"""
Core transformer model for the universal compiler/translator/AI/GDT system.

Built from scratch using only PyTorch. No external model APIs.
Encoder-decoder architecture for:
- Code completion (fill in gaps)
- Code translation (language A -> language B)
- Patch generation (broken -> fixed)
- Gap detection (find bugs, missing code, vulnerabilities)

Runs 100% offline.
"""

import math
import torch
import torch.nn as nn
from typing import Optional


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding."""

    def __init__(self, dim: int, max_len: int = 2048, dropout: float = 0.1) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, dim)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, dim, 2).float() * (-math.log(10000.0) / dim)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, dim)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    """Multi-head self-attention from scratch."""

    def __init__(self, dim: int, heads: int, dropout: float = 0.1) -> None:
        super().__init__()
        assert dim % heads == 0, f"dim ({dim}) must be divisible by heads ({heads})"
        self.dim = dim
        self.heads = heads
        self.head_dim = dim // heads
        self.scale = self.head_dim ** -0.5

        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        self.attn_dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch, seq_len, _ = query.shape

        q = self.q_proj(query).view(batch, -1, self.heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(key).view(batch, -1, self.heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(value).view(batch, -1, self.heads, self.head_dim).transpose(1, 2)

        attn = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))

        attn = torch.softmax(attn, dim=-1)
        attn = self.attn_dropout(attn)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch, -1, self.dim)
        return self.out_proj(out)


class FeedForward(nn.Module):
    """Position-wise feed-forward with GELU activation."""

    def __init__(self, dim: int, ff_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class EncoderLayer(nn.Module):
    """Single transformer encoder layer."""

    def __init__(self, dim: int, heads: int, ff_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.self_attn = MultiHeadAttention(dim, heads, dropout)
        self.ff = FeedForward(dim, ff_dim, dropout)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = x + self.self_attn(self.norm1(x), self.norm1(x), self.norm1(x), mask)
        x = x + self.ff(self.norm2(x))
        return x


class DecoderLayer(nn.Module):
    """Single transformer decoder layer with cross-attention."""

    def __init__(self, dim: int, heads: int, ff_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.self_attn = MultiHeadAttention(dim, heads, dropout)
        self.cross_attn = MultiHeadAttention(dim, heads, dropout)
        self.ff = FeedForward(dim, ff_dim, dropout)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.norm3 = nn.LayerNorm(dim)

    def forward(
        self,
        x: torch.Tensor,
        encoder_out: torch.Tensor,
        tgt_mask: Optional[torch.Tensor] = None,
        memory_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        normed = self.norm1(x)
        x = x + self.self_attn(normed, normed, normed, tgt_mask)
        normed = self.norm2(x)
        x = x + self.cross_attn(normed, encoder_out, encoder_out, memory_mask)
        x = x + self.ff(self.norm3(x))
        return x


class GapDetectorModel(nn.Module):
    """
    Full encoder-decoder transformer for code understanding, gap detection,
    patching, translation, and completion.

    Architecture:
    - Byte-level embedding (handles any language/format)
    - Sinusoidal positional encoding
    - N encoder layers (understand input code)
    - N decoder layers (generate output: patches, translations, completions)
    - Output projection to vocab (byte-level + special tokens)
    """

    def __init__(
        self,
        vocab_size: int = 512,
        dim: int = 512,
        encoder_layers: int = 8,
        decoder_layers: int = 8,
        heads: int = 8,
        ff_dim: int = 2048,
        max_seq_len: int = 1024,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.dim = dim
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len

        # Shared embedding for encoder and decoder
        self.embedding = nn.Embedding(vocab_size, dim, padding_idx=0)
        self.pos_encoding = PositionalEncoding(dim, max_seq_len, dropout)

        # Encoder stack
        self.encoder_layers = nn.ModuleList([
            EncoderLayer(dim, heads, ff_dim, dropout)
            for _ in range(encoder_layers)
        ])
        self.encoder_norm = nn.LayerNorm(dim)

        # Decoder stack
        self.decoder_layers = nn.ModuleList([
            DecoderLayer(dim, heads, ff_dim, dropout)
            for _ in range(decoder_layers)
        ])
        self.decoder_norm = nn.LayerNorm(dim)

        # Output head - project back to vocab
        self.output_proj = nn.Linear(dim, vocab_size)

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def _make_causal_mask(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """Create causal (autoregressive) attention mask."""
        mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
        return mask.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, seq_len)

    def _make_pad_mask(self, tokens: torch.Tensor) -> torch.Tensor:
        """Create padding mask (1 = attend, 0 = ignore)."""
        return (tokens != 0).unsqueeze(1).unsqueeze(2)  # (batch, 1, 1, seq_len)

    def encode(self, src: torch.Tensor) -> torch.Tensor:
        """Encode source sequence."""
        pad_mask = self._make_pad_mask(src)
        x = self.embedding(src) * math.sqrt(self.dim)
        x = self.pos_encoding(x)
        for layer in self.encoder_layers:
            x = layer(x, pad_mask)
        return self.encoder_norm(x)

    def decode(
        self,
        tgt: torch.Tensor,
        encoder_out: torch.Tensor,
        memory_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Decode target sequence with encoder context."""
        seq_len = tgt.size(1)
        causal_mask = self._make_causal_mask(seq_len, tgt.device)
        x = self.embedding(tgt) * math.sqrt(self.dim)
        x = self.pos_encoding(x)
        for layer in self.decoder_layers:
            x = layer(x, encoder_out, causal_mask, memory_mask)
        return self.decoder_norm(x)

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
    ) -> torch.Tensor:
        """
        Full forward pass.

        Args:
            src: source token IDs (batch, src_len)
            tgt: target token IDs (batch, tgt_len)

        Returns:
            logits: (batch, tgt_len, vocab_size)
        """
        memory_mask = self._make_pad_mask(src)
        encoder_out = self.encode(src)
        decoder_out = self.decode(tgt, encoder_out, memory_mask)
        return self.output_proj(decoder_out)

    def generate(
        self,
        src: torch.Tensor,
        max_len: int = 512,
        temperature: float = 0.8,
        bos_token: int = 256,
        eos_token: int = 257,
    ) -> torch.Tensor:
        """
        Autoregressive generation (inference).
        Fully offline - no API calls.

        Args:
            src: source token IDs (1, src_len)
            max_len: maximum output length
            temperature: sampling temperature (lower = more deterministic)
            bos_token: beginning of sequence token
            eos_token: end of sequence token

        Returns:
            generated: token IDs (1, gen_len)
        """
        self.eval()
        device = src.device
        encoder_out = self.encode(src)
        memory_mask = self._make_pad_mask(src)

        generated = torch.tensor([[bos_token]], device=device, dtype=torch.long)

        with torch.no_grad():
            for _ in range(max_len):
                decoder_out = self.decode(generated, encoder_out, memory_mask)
                logits = self.output_proj(decoder_out[:, -1, :])

                if temperature > 0:
                    probs = torch.softmax(logits / temperature, dim=-1)
                    next_token = torch.multinomial(probs, 1)
                else:
                    next_token = logits.argmax(dim=-1, keepdim=True)

                generated = torch.cat([generated, next_token], dim=1)

                if next_token.item() == eos_token:
                    break

        return generated

    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
