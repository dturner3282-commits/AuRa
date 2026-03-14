"""
AuRA Signal Processing Plugin — Peripheral Sensory Module.

Decodes audio signals using an 11-step protocol:
FFT frequency extraction, alphabet mapping, divisor sweeps,
multi-key analysis, and ECL scoring.

Usage:
    from aura.plugins.signal.engine import decode_file
    result = decode_file("path/to/audio.wav")
"""

from .engine import decode_file, RU_TO_LATIN

__all__ = ["decode_file", "RU_TO_LATIN"]
