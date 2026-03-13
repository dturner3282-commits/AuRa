"""
Model export utilities.

Export trained models to various formats:
1. PyTorch .pt (default, full precision)
2. ONNX (cross-platform inference)
3. C header arrays (for ESP32 firmware embedding)
4. Quantized int8 (smaller, faster, ESP32-compatible)

All offline. No APIs.
"""

import os
import struct
import json
import shutil
import torch
import torch.nn as nn
import yaml
from typing import Optional, Dict
from pathlib import Path


class ModelExporter:
    """Export trained models to deployable formats."""

    @staticmethod
    def export_quantized(
        model: nn.Module,
        output_path: str,
        calibration_data: Optional[torch.Tensor] = None,
    ) -> str:
        """
        Export model with dynamic int8 quantization.
        Reduces model size by ~4x with minimal accuracy loss.
        """
        quantized = torch.quantization.quantize_dynamic(
            model, {nn.Linear}, dtype=torch.qint8
        )
        torch.save(quantized.state_dict(), output_path)
        size_mb = os.path.getsize(output_path) / 1e6
        print(f"Quantized model saved: {output_path} ({size_mb:.1f} MB)")
        return output_path

    @staticmethod
    def export_onnx(
        model: nn.Module,
        output_path: str,
        max_seq_len: int = 256,
        vocab_size: int = 512,
    ) -> str:
        """
        Export model to ONNX format for cross-platform inference.
        Works with ONNX Runtime, TensorRT, etc.
        """
        model.eval()
        device = next(model.parameters()).device

        dummy_src = torch.randint(0, vocab_size, (1, max_seq_len), device=device)
        dummy_tgt = torch.randint(0, vocab_size, (1, max_seq_len), device=device)

        torch.onnx.export(
            model,
            (dummy_src, dummy_tgt),
            output_path,
            input_names=["source", "target"],
            output_names=["logits"],
            dynamic_axes={
                "source": {0: "batch", 1: "src_len"},
                "target": {0: "batch", 1: "tgt_len"},
                "logits": {0: "batch", 1: "tgt_len"},
            },
            opset_version=14,
        )
        size_mb = os.path.getsize(output_path) / 1e6
        print(f"ONNX model saved: {output_path} ({size_mb:.1f} MB)")
        return output_path

    @staticmethod
    def export_to_c_array(
        model: nn.Module,
        output_dir: str,
        model_name: str = "gap_model",
    ) -> str:
        """
        Export model weights as C header files for ESP32 firmware.

        Creates:
        - {model_name}_weights.h: weight arrays
        - {model_name}_config.h: model configuration
        """
        os.makedirs(output_dir, exist_ok=True)

        # Collect all weights as flat arrays
        state = model.state_dict()
        total_params = 0

        # Write weights header
        weights_path = os.path.join(output_dir, f"{model_name}_weights.h")
        with open(weights_path, "w") as f:
            f.write(f"// Auto-generated ESP32 model weights\n")
            f.write(f"// Model: {model_name}\n")
            f.write(f"#ifndef {model_name.upper()}_WEIGHTS_H\n")
            f.write(f"#define {model_name.upper()}_WEIGHTS_H\n\n")
            f.write(f"#include <stdint.h>\n\n")

            for name, tensor in state.items():
                flat = tensor.detach().cpu().flatten()
                total_params += flat.numel()

                # Quantize to int8
                scale = flat.abs().max().item() / 127.0
                if scale == 0:
                    scale = 1.0
                quantized = (flat / scale).clamp(-127, 127).to(torch.int8)

                c_name = name.replace(".", "_")
                f.write(f"// {name}: shape={list(tensor.shape)}, scale={scale:.6f}\n")
                f.write(f"static const float {c_name}_scale = {scale:.6f}f;\n")
                f.write(f"static const int8_t {c_name}[] = {{\n")

                vals = quantized.tolist()
                for i in range(0, len(vals), 16):
                    chunk = vals[i:i+16]
                    f.write("    " + ", ".join(str(int(v)) for v in chunk) + ",\n")

                f.write(f"}};\n\n")

            f.write(f"#endif // {model_name.upper()}_WEIGHTS_H\n")

        # Write config header
        config_path = os.path.join(output_dir, f"{model_name}_config.h")
        with open(config_path, "w") as f:
            f.write(f"// Auto-generated ESP32 model config\n")
            f.write(f"#ifndef {model_name.upper()}_CONFIG_H\n")
            f.write(f"#define {model_name.upper()}_CONFIG_H\n\n")
            f.write(f"#define {model_name.upper()}_TOTAL_PARAMS {total_params}\n")
            f.write(f"#define {model_name.upper()}_NUM_LAYERS {len([k for k in state.keys() if 'blocks' in k and 'weight' in k]) // 4}\n")
            f.write(f"\n#endif // {model_name.upper()}_CONFIG_H\n")

        total_bytes = total_params  # int8 = 1 byte per param
        print(f"C arrays exported to {output_dir}/")
        print(f"Total parameters: {total_params:,}")
        print(f"Estimated firmware size: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
        return output_dir

    @staticmethod
    def export_full_package(
        checkpoint_path: str,
        output_dir: str,
    ) -> None:
        """
        Export a complete downloadable package with model + config + CLI.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Copy checkpoint
        model_dest = os.path.join(output_dir, "model.pt")
        shutil.copy2(checkpoint_path, model_dest)

        # Create a simple run script
        run_script = os.path.join(output_dir, "run.sh")
        with open(run_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# GapDet - Offline AI Compiler/Patcher\n")
            f.write("# Usage: ./run.sh detect mycode.c\n")
            f.write("#        ./run.sh fix mycode.py\n")
            f.write("#        ./run.sh translate mycode.py --to c\n")
            f.write("#        ./run.sh analyze mycode.rs\n\n")
            f.write('DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n')
            f.write('python3 -m aura.cli --model "$DIR/model.pt" "$@"\n')
        os.chmod(run_script, 0o755)

        size_mb = os.path.getsize(model_dest) / 1e6
        print(f"Package exported to {output_dir}/")
        print(f"Model size: {size_mb:.1f} MB")
        print(f"Run with: cd {output_dir} && ./run.sh detect <file>")

    @staticmethod
    def export_model_bundle(
        checkpoint_path: str,
        output_dir: str,
        model_name: str = "gapdet",
        include_gguf: bool = True,
    ) -> str:
        """
        Export a complete model bundle like Llama/HuggingFace downloads.

        Creates a directory with:
        - model.pt (PyTorch weights)
        - config.yaml (model configuration)
        - tokenizer.json (byte tokenizer state)
        - metadata.json (model info, capabilities, languages)
        - README.md (usage instructions)
        - gapdet.gguf (optional, universal format for Ollama/llama.cpp)
        - run.sh (convenience script)

        This is the primary deliverable — a single directory you can
        download and use anywhere, just like downloading a Llama model.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        config = checkpoint.get("config", {})
        pc_cfg = config.get("pc_model", {})
        step = checkpoint.get("step", 0)

        # 1. Copy model weights
        model_dest = os.path.join(output_dir, "model.pt")
        shutil.copy2(checkpoint_path, model_dest)

        # 2. Write config.yaml
        model_config = {
            "model_type": "gapdet",
            "architecture": "encoder-decoder-transformer",
            "version": "0.2.0",
            "codename": "davids-brain",
            "pc_model": {
                "vocab_size": pc_cfg.get("vocab_size", 512),
                "dim": pc_cfg.get("dim", 512),
                "encoder_layers": pc_cfg.get("encoder_layers", 8),
                "decoder_layers": pc_cfg.get("decoder_layers", 8),
                "heads": pc_cfg.get("heads", 8),
                "ff_dim": pc_cfg.get("ff_dim", 2048),
                "max_seq_len": pc_cfg.get("max_seq_len", 1024),
                "dropout": pc_cfg.get("dropout", 0.1),
            },
            "tokenizer": {
                "type": "byte",
                "vocab_size": 512,
                "special_tokens": {
                    "PAD": 256, "SOS": 257, "EOS": 258, "UNK": 259,
                    "MASK": 260, "SEP": 261, "GAP": 262, "FIX": 263,
                    "LANG": 264, "TRANSLATE": 265,
                },
            },
            "training": {
                "step": step,
                "optimizer": "AdamW",
                "learning_rate": config.get("training", {}).get("learning_rate", 1e-4),
            },
            "capabilities": [
                "gap_detection", "code_patching", "code_completion",
                "cross_language_translation", "compiler_validation",
            ],
            "sovereign": {
                "ecl": True,
                "sov_check": True,
                "genix_memory": True,
                "taxonomy": True,
            },
        }
        config_path = os.path.join(output_dir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(model_config, f, default_flow_style=False, sort_keys=False)

        # 3. Write tokenizer.json
        tokenizer_state = {
            "type": "byte",
            "vocab_size": 512,
            "byte_range": [0, 255],
            "special_tokens": model_config["tokenizer"]["special_tokens"],
            "encoding": "utf-8",
            "description": "Byte-level tokenizer handling any programming language, config, or binary format",
        }
        tokenizer_path = os.path.join(output_dir, "tokenizer.json")
        with open(tokenizer_path, "w") as f:
            json.dump(tokenizer_state, f, indent=2)

        # 4. Write metadata.json
        metadata = {
            "model_name": model_name,
            "version": "0.2.0",
            "codename": "David's Brain",
            "description": "GapDet - Fully offline AI compiler/patcher/translator/gap-detector with sovereign reasoning",
            "author": "David Turner",
            "license": "MIT",
            "source": "https://github.com/dturner3282-commits/s8",
            "training_step": step,
            "architecture": {
                "type": "encoder-decoder-transformer",
                "parameters": sum(p.numel() for p in [
                    v for v in checkpoint.get("pc_model", {}).values()
                    if isinstance(v, torch.Tensor)
                ]),
            },
            "capabilities": [
                "gap_detection", "code_patching", "code_completion",
                "cross_language_translation", "compiler_validation",
            ],
            "supported_languages": [
                "c", "cpp", "python", "rust", "go", "java", "javascript",
                "typescript", "bash", "arduino_cpp", "kotlin", "swift",
                "ruby", "php", "lua", "assembly", "sql", "dockerfile",
                "yaml", "json", "toml", "xml", "makefile", "cmake",
                "perl", "lisp", "zig", "haskell", "dart", "terraform",
                "graphql", "protobuf",
            ],
            "gap_types": [
                "missing_error_handling", "buffer_overflow", "null_dereference",
                "resource_leak", "race_condition", "security_vulnerability",
                "type_mismatch", "missing_import", "incomplete_implementation",
                "missing_bounds_check", "uninitialized_variable", "missing_return",
            ],
            "sovereign_features": {
                "ECL": "Emergence Continuity Loop - self-referential reasoning",
                "Hangman": "Code gap detection framework",
                "Loom": "Concurrency pattern manager",
                "PIM": "Pattern-based Identification Method",
                "Genix": "Contextual memory store",
                "SOV_CHECK": "Sovereignty validation gate",
            },
            "offline": True,
            "requires_internet": False,
        }
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # 5. Write README.md
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("""# GapDet - David's Brain

Fully offline AI compiler/patcher/translator/gap-detector.
100% private. No APIs. No cloud. No internet required.

## Quick Start

```bash
# Install
pip install torch pyyaml
pip install -e .

# Use
gapdet detect mycode.c          # Find gaps/bugs
gapdet fix mycode.py             # Fix broken code
gapdet complete mycode.rs        # Complete incomplete code
gapdet translate mycode.py --to rust  # Translate between languages
gapdet analyze mycode.go         # Full analysis
gapdet ui                        # Launch web UI
gapdet voice                     # Voice control
gapdet info                      # Show system info
```

## Files in This Bundle

| File | Description |
|------|-------------|
| `model.pt` | PyTorch model weights |
| `config.yaml` | Model architecture configuration |
| `tokenizer.json` | Byte-level tokenizer state |
| `metadata.json` | Model capabilities and supported languages |
| `gapdet.gguf` | GGUF format (for Ollama/llama.cpp/Jan/LM Studio) |
| `run.sh` | Convenience run script |

## Supported Languages

C, C++, Python, Rust, Go, Java, JavaScript, TypeScript, Bash, Arduino,
Kotlin, Swift, Ruby, PHP, Lua, Assembly, SQL, Dockerfile, YAML, JSON,
TOML, XML, Makefile, CMake, Perl, Lisp/ECL, Zig, Haskell, Dart,
Terraform, GraphQL, Protobuf

## Sovereign Features (Background Brain)

- **ECL** (Emergence Continuity Loop): Self-referential reasoning
- **Hangman**: Code gap detection framework
- **Loom**: Concurrency pattern manager
- **SOV-CHECK**: Sovereignty validation gate
- **Genix**: Contextual memory store

## Offline Promise

This model works 100% offline. After installation, no internet is needed.
Your code never leaves your machine.
""")

        # 6. Create run.sh
        run_script = os.path.join(output_dir, "run.sh")
        with open(run_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# GapDet - David's Brain\n")
            f.write('DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n')
            f.write('python3 -m aura.cli --model "$DIR/model.pt" "$@"\n')
        os.chmod(run_script, 0o755)

        # 7. Export GGUF (universal format)
        if include_gguf:
            try:
                from aura.core.export.gguf_export import export_gguf
                gguf_path = os.path.join(output_dir, "gapdet.gguf")
                export_gguf(checkpoint_path, gguf_path, model_name=model_name)
            except Exception as e:
                print(f"GGUF export skipped: {e}")

        # Summary
        total_size = sum(
            os.path.getsize(os.path.join(output_dir, f))
            for f in os.listdir(output_dir)
            if os.path.isfile(os.path.join(output_dir, f))
        )
        print(f"")
        print(f"Model bundle exported to: {output_dir}/")
        print(f"Total size: {total_size / 1e6:.1f} MB")
        print(f"Files:")
        for f in sorted(os.listdir(output_dir)):
            fp = os.path.join(output_dir, f)
            if os.path.isfile(fp):
                print(f"  {f} ({os.path.getsize(fp) / 1e6:.1f} MB)")
        print(f"")
        print(f"Use: cd {output_dir} && ./run.sh detect <file>")
        print(f"Or:  gapdet --model {output_dir}/model.pt detect <file>")

        return output_dir
