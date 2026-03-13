"""
Tiny model variant that fits on ESP32 hardware.

Constraints:
- ESP32: 4MB flash, 520KB SRAM (+ optional 4-8MB PSRAM)
- Model must be < 500KB (quantized weights)
- Inference must work with limited RAM
- No Python runtime on ESP32 - this is for training/export only

This model is trained in Python, then exported to:
1. TFLite format for TFLite Micro on ESP32
2. Raw C arrays for direct embedding in firmware

Architecture: Minimal encoder-only transformer
- 64-dim embeddings
- 2 encoder layers
- 4 attention heads
- 256-dim feed-forward
- ~100K parameters (~400KB at float32, ~100KB quantized to int8)
"""

import torch
import torch.nn as nn
import math
from typing import Optional, Dict


class ESP32Attention(nn.Module):
    """Lightweight multi-head attention for ESP32."""

    def __init__(self, dim: int = 64, heads: int = 4) -> None:
        super().__init__()
        self.heads = heads
        self.head_dim = dim // heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(dim, dim * 3)
        self.out = nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, seq_len, dim = x.shape
        qkv = self.qkv(x).reshape(batch, seq_len, 3, self.heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        attn = torch.softmax(attn, dim=-1)
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().reshape(batch, seq_len, dim)
        return self.out(out)


class ESP32Block(nn.Module):
    """Lightweight transformer block for ESP32."""

    def __init__(self, dim: int = 64, heads: int = 4, ff_dim: int = 256) -> None:
        super().__init__()
        self.attn = ESP32Attention(dim, heads)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.ff = nn.Sequential(
            nn.Linear(dim, ff_dim),
            nn.ReLU(),  # ReLU instead of GELU for ESP32 efficiency
            nn.Linear(ff_dim, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x


class ESP32GapModel(nn.Module):
    """
    Tiny gap detection model for ESP32.

    Encoder-only architecture:
    - Detects gaps/anomalies in input sequences
    - Classifies gap types
    - Small enough to run on ESP32 with PSRAM

    After training, export with:
    - export_to_tflite() for TensorFlow Lite Micro
    - export_to_c_array() for direct firmware embedding
    """

    def __init__(
        self,
        vocab_size: int = 512,
        dim: int = 64,
        layers: int = 2,
        heads: int = 4,
        ff_dim: int = 256,
        max_seq_len: int = 256,
        num_gap_categories: int = 16,
    ) -> None:
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len

        self.embedding = nn.Embedding(vocab_size, dim, padding_idx=0)

        # Simple learned positional embedding (smaller than sinusoidal for ESP32)
        self.pos_embedding = nn.Embedding(max_seq_len, dim)

        self.blocks = nn.ModuleList([
            ESP32Block(dim, heads, ff_dim) for _ in range(layers)
        ])
        self.norm = nn.LayerNorm(dim)

        # Gap detection output heads
        self.gap_detector = nn.Linear(dim, 1)  # per-token: is this a gap?
        self.gap_classifier = nn.Linear(dim, num_gap_categories)  # per-token: what kind?
        self.severity = nn.Sequential(
            nn.Linear(dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: token IDs (batch, seq_len)

        Returns dict:
            gap_probs: (batch, seq_len) per-token gap probability
            gap_categories: (batch, seq_len, num_categories) per-token category logits
            severity: (batch, 1) overall severity
        """
        batch, seq_len = x.shape
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0).expand(batch, -1)

        h = self.embedding(x) + self.pos_embedding(positions)

        for block in self.blocks:
            h = block(h)
        h = self.norm(h)

        gap_logits = self.gap_detector(h).squeeze(-1)
        gap_probs = torch.sigmoid(gap_logits)
        gap_categories = self.gap_classifier(h)

        # Pool for severity
        pooled = h.mean(dim=1)
        sev = self.severity(pooled)

        return {
            "gap_probs": gap_probs,
            "gap_categories": gap_categories,
            "severity": sev,
        }

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def estimate_size_bytes(self, quantized: bool = True) -> int:
        """Estimate model size in bytes."""
        params = self.count_parameters()
        if quantized:
            return params  # int8: 1 byte per param
        return params * 4  # float32: 4 bytes per param
