"""
Gap Detection Tool (GDT) Module — Uncle Greg's Substrate.

Core formula: G = |E - O| (gap magnitude)
Constraint window: C = [L, U] — gap is meaningful only if G not in C
Classifier: thresholds t1, t2 map gaps to discrete categories
Stability: S = 1 - (sum(G) / N) — pattern consistency metric
Delta+C engine: delta = |E - O|; MeaningfulGap = (delta not in C)

Analyzes code to find:
- Missing error handling
- Incomplete implementations (TODO, FIXME, stub functions)
- Security vulnerabilities (buffer overflows, null derefs, etc.)
- Missing imports/includes
- Type mismatches
- Resource leaks
- Race conditions
- Missing bounds checks
- Dead code
- Uninitialized variables

Uses the encoder output from the main model to classify gaps.
Runs 100% offline.
"""

import torch
import torch.nn as nn
from typing import List, Dict, Tuple


# Gap categories with human-readable descriptions
GAP_CATEGORIES: Dict[int, str] = {
    0: "no_gap",
    1: "missing_error_handling",
    2: "incomplete_implementation",
    3: "security_vulnerability",
    4: "missing_import",
    5: "type_mismatch",
    6: "buffer_overflow",
    7: "null_dereference",
    8: "resource_leak",
    9: "race_condition",
    10: "missing_bounds_check",
    11: "incomplete_switch",
    12: "dead_code",
    13: "missing_return",
    14: "uninitialized_variable",
    15: "syntax_error",
}

NUM_GAP_CATEGORIES = len(GAP_CATEGORIES)


class GapDetectionHead(nn.Module):
    """
    Classification head that attaches to the encoder to detect gaps.

    Takes encoder hidden states and predicts:
    1. Per-token gap probability (binary: is this token part of a gap?)
    2. Per-token gap category (what kind of gap?)
    3. Sequence-level gap summary (overall gap types in the code)

    This runs on top of the encoder - no decoder needed for detection.
    """

    def __init__(self, dim: int, num_categories: int = NUM_GAP_CATEGORIES) -> None:
        super().__init__()
        self.num_categories = num_categories

        # Per-token binary gap detection (Greg's G = |E - O|)
        self.token_gap_detector = nn.Sequential(
            nn.Linear(dim, dim // 2),
            nn.GELU(),
            nn.Linear(dim // 2, 1),
        )

        # Per-token gap category classification (Greg's threshold classifier)
        self.token_gap_classifier = nn.Sequential(
            nn.Linear(dim, dim // 2),
            nn.GELU(),
            nn.Linear(dim // 2, num_categories),
        )

        # Sequence-level gap summary (uses mean pooling over encoder output)
        self.sequence_classifier = nn.Sequential(
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Linear(dim, num_categories),
        )

        # Severity estimator (0-1 score for how critical the gap is)
        self.severity_head = nn.Sequential(
            nn.Linear(dim, dim // 4),
            nn.GELU(),
            nn.Linear(dim // 4, 1),
            nn.Sigmoid(),
        )

        # Greg's constraint window C = [L, U] — learnable bounds per category
        self.constraint_lower = nn.Parameter(torch.zeros(num_categories) + 0.3)
        self.constraint_upper = nn.Parameter(torch.ones(num_categories) * 0.7)

        # Greg's stability score head: S = 1 - (sum(G) / N)
        self.stability_head = nn.Sequential(
            nn.Linear(dim, dim // 4),
            nn.GELU(),
            nn.Linear(dim // 4, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        encoder_output: torch.Tensor,
        pad_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Detect gaps in the encoded code.

        Args:
            encoder_output: (batch, seq_len, dim) from the encoder
            pad_mask: (batch, seq_len) boolean, True = real token

        Returns dict with:
            token_gap_probs: (batch, seq_len) probability each token is a gap
            token_gap_categories: (batch, seq_len, num_categories) per-token category logits
            sequence_gaps: (batch, num_categories) sequence-level gap logits
            severity: (batch, 1) overall severity score
        """
        # Per-token gap detection (Greg's G = |E - O| via learned detector)
        token_gap_logits = self.token_gap_detector(encoder_output).squeeze(-1)
        token_gap_probs = torch.sigmoid(token_gap_logits)

        # Per-token category (Greg's threshold classifier)
        token_gap_categories = self.token_gap_classifier(encoder_output)

        # Sequence-level: mean pool over non-padding tokens
        mask_expanded = pad_mask.unsqueeze(-1).float()
        pooled = (encoder_output * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        sequence_gaps = self.sequence_classifier(pooled)

        # Severity
        severity = self.severity_head(pooled)

        # Greg's stability score: S = 1 - (sum(G) / N)
        # Learned approximation via the stability head
        stability = self.stability_head(pooled)

        return {
            "token_gap_probs": token_gap_probs,
            "token_gap_categories": token_gap_categories,
            "sequence_gaps": sequence_gaps,
            "severity": severity,
            "stability": stability,
            "constraint_window": {
                "lower": self.constraint_lower,
                "upper": self.constraint_upper,
            },
        }


def decode_gap_results(
    token_gap_probs: torch.Tensor,
    token_gap_categories: torch.Tensor,
    sequence_gaps: torch.Tensor,
    severity: torch.Tensor,
    threshold: float = 0.5,
) -> List[Dict]:
    """
    Decode raw model outputs into human-readable gap reports.

    Args:
        token_gap_probs: (seq_len,) per-token gap probabilities
        token_gap_categories: (seq_len, num_categories) per-token category logits
        sequence_gaps: (num_categories,) sequence-level gap logits
        severity: scalar severity score
        threshold: probability threshold for gap detection

    Returns:
        List of gap reports, each containing:
        - position: token index
        - category: gap type name
        - confidence: detection confidence
        - severity: how critical
    """
    gaps: List[Dict] = []

    # Find tokens flagged as gaps
    gap_mask = token_gap_probs > threshold
    gap_indices = torch.where(gap_mask)[0]

    for idx in gap_indices:
        cat_logits = token_gap_categories[idx]
        cat_id = cat_logits.argmax().item()
        confidence = token_gap_probs[idx].item()

        gaps.append({
            "position": idx.item(),
            "category": GAP_CATEGORIES.get(cat_id, "unknown"),
            "category_id": cat_id,
            "confidence": round(confidence, 3),
        })

    # Sequence-level summary
    seq_probs = torch.sigmoid(sequence_gaps)
    active_categories = torch.where(seq_probs > threshold)[0]

    summary = {
        "total_gaps_found": len(gaps),
        "severity": round(severity.item(), 3),
        "active_gap_types": [
            GAP_CATEGORIES.get(c.item(), "unknown") for c in active_categories
        ],
        "gaps": gaps,
    }

    return [summary]
