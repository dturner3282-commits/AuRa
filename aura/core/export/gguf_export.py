"""
GGUF Model Export.

Exports trained GapDet models to GGUF format — the universal format used by
llama.cpp, Ollama, Jan, LM Studio, and other offline inference engines.

This creates a self-contained .gguf file you can download and use anywhere.

Usage:
    python -m aura.export.gguf_export --checkpoint checkpoints/pc_model_final.pt --output gapdet.gguf

GGUF format spec: https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
"""

import struct
import os
import json
import torch
import torch.nn as nn
from typing import Dict, Optional, BinaryIO
from pathlib import Path

# GGUF magic and version
GGUF_MAGIC = 0x46475547  # "GGUF" in little-endian
GGUF_VERSION = 3

# GGUF metadata value types
GGUF_TYPE_UINT8 = 0
GGUF_TYPE_INT8 = 1
GGUF_TYPE_UINT16 = 2
GGUF_TYPE_INT16 = 3
GGUF_TYPE_UINT32 = 4
GGUF_TYPE_INT32 = 5
GGUF_TYPE_FLOAT32 = 6
GGUF_TYPE_BOOL = 7
GGUF_TYPE_STRING = 8
GGUF_TYPE_ARRAY = 9
GGUF_TYPE_UINT64 = 10
GGUF_TYPE_INT64 = 11
GGUF_TYPE_FLOAT64 = 12

# GGML tensor types
GGML_TYPE_F32 = 0
GGML_TYPE_F16 = 1
GGML_TYPE_Q8_0 = 8


def _write_string(f: BinaryIO, s: str) -> None:
    """Write a GGUF string (length-prefixed UTF-8)."""
    encoded = s.encode("utf-8")
    f.write(struct.pack("<Q", len(encoded)))
    f.write(encoded)


def _write_metadata_kv(f: BinaryIO, key: str, value, value_type: int) -> None:
    """Write a single GGUF metadata key-value pair."""
    _write_string(f, key)
    f.write(struct.pack("<I", value_type))

    if value_type == GGUF_TYPE_STRING:
        _write_string(f, value)
    elif value_type == GGUF_TYPE_UINT32:
        f.write(struct.pack("<I", value))
    elif value_type == GGUF_TYPE_INT32:
        f.write(struct.pack("<i", value))
    elif value_type == GGUF_TYPE_FLOAT32:
        f.write(struct.pack("<f", value))
    elif value_type == GGUF_TYPE_UINT64:
        f.write(struct.pack("<Q", value))
    elif value_type == GGUF_TYPE_BOOL:
        f.write(struct.pack("<B", 1 if value else 0))
    elif value_type == GGUF_TYPE_ARRAY:
        # value should be (element_type, elements_list)
        elem_type, elements = value
        f.write(struct.pack("<I", elem_type))
        f.write(struct.pack("<Q", len(elements)))
        for elem in elements:
            if elem_type == GGUF_TYPE_STRING:
                _write_string(f, elem)
            elif elem_type == GGUF_TYPE_FLOAT32:
                f.write(struct.pack("<f", elem))
            elif elem_type == GGUF_TYPE_INT32:
                f.write(struct.pack("<i", elem))
            elif elem_type == GGUF_TYPE_UINT32:
                f.write(struct.pack("<I", elem))


def _quantize_tensor_q8(tensor: torch.Tensor) -> bytes:
    """
    Quantize a tensor to Q8_0 format (block-wise int8 quantization).
    Each block: 32 values, 1 f16 scale + 32 int8 values = 34 bytes per block.
    """
    flat = tensor.detach().cpu().float().flatten()
    n = flat.numel()

    # Pad to multiple of 32
    if n % 32 != 0:
        pad_size = 32 - (n % 32)
        flat = torch.cat([flat, torch.zeros(pad_size)])
        n = flat.numel()

    num_blocks = n // 32
    result = bytearray()

    for b in range(num_blocks):
        block = flat[b * 32:(b + 1) * 32]
        max_abs = block.abs().max().item()
        scale = max_abs / 127.0 if max_abs > 0 else 1.0

        # Write scale as float16
        import numpy as np
        scale_f16 = np.float16(scale)
        result.extend(scale_f16.tobytes())

        # Write quantized values as int8
        quantized = (block / scale).clamp(-128, 127).to(torch.int8)
        result.extend(quantized.numpy().tobytes())

    return bytes(result)


def export_gguf(
    checkpoint_path: str,
    output_path: str,
    model_name: str = "gapdet",
    quantize: bool = True,
    description: str = "GapDet - Offline AI compiler/patcher/translator/gap-detector",
) -> str:
    """
    Export a trained GapDet model to GGUF format.

    Args:
        checkpoint_path: Path to the .pt checkpoint
        output_path: Output .gguf file path
        model_name: Model name metadata
        quantize: If True, use Q8_0 quantization (4x smaller)
        description: Model description

    Returns:
        Path to the exported .gguf file
    """
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = checkpoint.get("config", {})
    pc_cfg = config.get("pc_model", {})

    state_dict = checkpoint.get("pc_model", checkpoint.get("model", {}))
    gdt_state = checkpoint.get("gdt_head", {})

    # Merge all weights
    all_weights = {}
    for k, v in state_dict.items():
        all_weights[f"model.{k}"] = v
    for k, v in gdt_state.items():
        all_weights[f"gdt.{k}"] = v

    # Prepare metadata
    metadata = {
        "general.architecture": ("gapdet", GGUF_TYPE_STRING),
        "general.name": (model_name, GGUF_TYPE_STRING),
        "general.description": (description, GGUF_TYPE_STRING),
        "general.file_type": (8 if quantize else 0, GGUF_TYPE_UINT32),  # Q8_0 or F32
        "general.author": ("GapDet", GGUF_TYPE_STRING),
        "general.license": ("MIT", GGUF_TYPE_STRING),
        "general.source.url": ("https://github.com/dturner3282-commits/s8", GGUF_TYPE_STRING),

        # Architecture params
        "gapdet.vocab_size": (pc_cfg.get("vocab_size", 512), GGUF_TYPE_UINT32),
        "gapdet.embedding_length": (pc_cfg.get("dim", 512), GGUF_TYPE_UINT32),
        "gapdet.block_count": (pc_cfg.get("encoder_layers", 8), GGUF_TYPE_UINT32),
        "gapdet.decoder_block_count": (pc_cfg.get("decoder_layers", 8), GGUF_TYPE_UINT32),
        "gapdet.head_count": (pc_cfg.get("heads", 8), GGUF_TYPE_UINT32),
        "gapdet.feed_forward_length": (pc_cfg.get("ff_dim", 2048), GGUF_TYPE_UINT32),
        "gapdet.context_length": (pc_cfg.get("max_seq_len", 1024), GGUF_TYPE_UINT32),

        # Tokenizer info
        "tokenizer.ggml.model": ("byte", GGUF_TYPE_STRING),
        "tokenizer.ggml.tokens": (
            (GGUF_TYPE_STRING, [str(i) for i in range(512)]),
            GGUF_TYPE_ARRAY,
        ),

        # Training info
        "gapdet.training_step": (checkpoint.get("step", 0), GGUF_TYPE_UINT32),

        # Capabilities
        "gapdet.capabilities": (
            (GGUF_TYPE_STRING, [
                "gap_detection", "code_patching", "code_completion",
                "cross_language_translation", "compiler_validation",
            ]),
            GGUF_TYPE_ARRAY,
        ),

        # Supported languages
        "gapdet.languages": (
            (GGUF_TYPE_STRING, [
                "c", "cpp", "python", "rust", "go", "java", "javascript",
                "typescript", "bash", "arduino", "assembly", "lua", "ruby",
                "php", "swift", "kotlin", "dart", "zig", "haskell", "scala",
                "r", "perl", "matlab", "sql", "html", "css", "yaml", "json",
                "toml", "xml", "cmake", "makefile", "dockerfile", "terraform",
                "protobuf", "graphql",
            ]),
            GGUF_TYPE_ARRAY,
        ),
    }

    # Prepare tensor info
    tensor_data_list = []
    tensor_info_list = []
    current_offset = 0

    for name, tensor in all_weights.items():
        shape = list(tensor.shape)
        n_dims = len(shape)

        if quantize and tensor.numel() >= 32:
            data = _quantize_tensor_q8(tensor)
            dtype = GGML_TYPE_Q8_0
        else:
            data = tensor.detach().cpu().float().numpy().tobytes()
            dtype = GGML_TYPE_F32

        # Align to 32 bytes
        alignment = 32
        padding = (alignment - (len(data) % alignment)) % alignment
        data = data + b"\x00" * padding

        tensor_info_list.append({
            "name": name,
            "n_dims": n_dims,
            "shape": shape,
            "dtype": dtype,
            "offset": current_offset,
        })
        tensor_data_list.append(data)
        current_offset += len(data)

    # Write GGUF file
    with open(output_path, "wb") as f:
        # Header
        f.write(struct.pack("<I", GGUF_MAGIC))
        f.write(struct.pack("<I", GGUF_VERSION))
        f.write(struct.pack("<Q", len(tensor_info_list)))  # n_tensors
        f.write(struct.pack("<Q", len(metadata)))  # n_kv

        # Metadata KV pairs
        for key, (value, vtype) in metadata.items():
            _write_metadata_kv(f, key, value, vtype)

        # Tensor infos
        for info in tensor_info_list:
            _write_string(f, info["name"])
            f.write(struct.pack("<I", info["n_dims"]))
            for dim in info["shape"]:
                f.write(struct.pack("<Q", dim))
            f.write(struct.pack("<I", info["dtype"]))
            f.write(struct.pack("<Q", info["offset"]))

        # Alignment padding before tensor data
        alignment = 32
        current_pos = f.tell()
        padding = (alignment - (current_pos % alignment)) % alignment
        f.write(b"\x00" * padding)

        # Tensor data
        for data in tensor_data_list:
            f.write(data)

    file_size = os.path.getsize(output_path)
    print(f"GGUF model exported: {output_path}")
    print(f"File size: {file_size / 1e6:.1f} MB")
    print(f"Tensors: {len(tensor_info_list)}")
    print(f"Quantization: {'Q8_0' if quantize else 'F32'}")
    print(f"Format: GGUF v{GGUF_VERSION}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Export GapDet model to GGUF format")
    parser.add_argument("--checkpoint", required=True, help="Path to .pt checkpoint")
    parser.add_argument("--output", default="gapdet.gguf", help="Output .gguf file")
    parser.add_argument("--name", default="gapdet", help="Model name")
    parser.add_argument("--no-quantize", action="store_true", help="Skip quantization (larger file)")
    args = parser.parse_args()

    export_gguf(
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        model_name=args.name,
        quantize=not args.no_quantize,
    )


if __name__ == "__main__":
    main()
