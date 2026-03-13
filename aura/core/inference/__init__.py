"""Inference engines - imports are lazy to avoid requiring torch for lite mode."""


def __getattr__(name):
    if name == "InferenceEngine":
        from .engine import InferenceEngine
        return InferenceEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["InferenceEngine"]
