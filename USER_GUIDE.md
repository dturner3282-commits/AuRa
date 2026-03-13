# AuRA User Guide

**Autonomous Universal Recognition Agent**
Version 0.2.0 — David's Brain

A complete guide to every function, command, ability, and feature.

---

## Table of Contents

1. [What Is AuRA?](#what-is-aura)
2. [Installation](#installation)
3. [Two Modes: Full vs Lite](#two-modes-full-vs-lite)
4. [Commands Reference](#commands-reference)
5. [Using on Your Phone (Jan + GGUF)](#using-on-your-phone-jan--gguf)
6. [Using on Ventoy / USB Boot](#using-on-ventoy--usb-boot)
7. [David's Brain (Sovereign AI)](#davids-brain-sovereign-ai)
8. [Uncle Greg's GDT Formulas](#uncle-gregs-gdt-formulas)
9. [Gap Detection Categories](#gap-detection-categories)
10. [Supported Languages](#supported-languages)
11. [Training Your Own Model](#training-your-own-model)
12. [Exporting Models](#exporting-models)
13. [Plugins](#plugins)
14. [Troubleshooting](#troubleshooting)
15. [Architecture Overview](#architecture-overview)

---

## What Is AuRA?

AuRA is a **fully offline AI toolkit** that lives on your machine. It reads code, finds problems, fixes them, translates between languages, and learns from what you do. No internet, no APIs, no cloud services — everything runs locally.

Think of it as a Swiss Army knife for code:
- Give it broken code, it tells you what's wrong
- Give it incomplete code, it fills in the gaps
- Give it Python, it gives you C (or Rust, or Go, or 30+ other languages)
- Give it anything, it learns your patterns over time

It was built around **Uncle Greg's Gap Detection Technology (GDT)** — a mathematical framework for finding what's missing in code using deterministic formulas, not guesswork.

### Who Is This For?

- **You have a PC with a GPU**: Full AI model with neural inference, training, and all features
- **You have a phone (Pixel 6, etc.)**: Lite mode via Termux, or load the GGUF model into Jan
- **You have a USB stick (Ventoy)**: Boot Linux, clone the repo, use lite mode instantly
- **You have an old laptop**: Lite mode works without PyTorch — just Python 3

---

## Installation

### PC / Laptop (Full Mode)

```bash
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install torch pyyaml
pip install -e .
aura info
```

This gives you the full experience: neural model, training, GGUF export, everything.

### Termux on Android (Lite Mode) — No Login Required

```bash
pkg install python git
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install pyyaml
pip install -e .
aura info
```

Note: Skip `pip install torch` on phones — it's huge and unnecessary. AuRA automatically uses lite mode (rule-based gap detection) when PyTorch isn't installed.

**One-liner install:**
```bash
pkg install python git && git clone https://github.com/dturner3282-commits/AuRa.git && cd AuRa && pip install pyyaml && pip install -e . && aura info
```

### Ventoy / USB Linux Boot

Boot into your Linux partition (Mint, Ubuntu, Kali, etc.), open a terminal:

```bash
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install pyyaml
pip install -e .
aura info
```

Same as Termux — skip torch for lightweight use. Install torch later if you want full AI.

---

## Two Modes: Full vs Lite

AuRA automatically detects what's available and adjusts:

| Feature | Full Mode (PyTorch) | Lite Mode (No PyTorch) |
|---------|-------------------|----------------------|
| Gap detection | Neural AI + rules | Rule-based only |
| Code fixing | AI-generated patches | Not available |
| Code completion | AI-generated | Not available |
| Translation | AI-powered | Not available |
| Code analysis | AI + compiler | Rules + compiler |
| System info | Full model stats | Lite mode stats |
| Training | Yes | Not available |
| GGUF export | Yes | Not available |
| David's Brain | Full ECL + memory | Full ECL + memory |
| Compiler validation | Yes | Yes |

### How It Works

- If PyTorch is installed AND a trained model exists: **Full mode**
- If PyTorch is installed but no model: **Lite mode** (with message)
- If PyTorch is NOT installed: **Lite mode** automatically
- You can force lite mode anytime: `aura --lite detect myfile.py`

### What Lite Mode Can Do

Lite mode uses **pattern matching and Uncle Greg's GDT rules** to find problems in code. It checks for:
- Buffer overflows, null dereferences, resource leaks
- Missing error handling, security vulnerabilities
- Incomplete implementations (TODO, FIXME, stubs)
- Dead code, missing returns, uninitialized variables
- And more (16 gap categories total)

It works on: C, C++, Python, Rust, Go, JavaScript, TypeScript, Java, Bash, Arduino

### What Lite Mode Cannot Do

- **Fix code** — needs the neural model to generate patches
- **Complete code** — needs the neural model to generate completions
- **Translate code** — needs the neural model to map between languages

For these features, install PyTorch and train a model on a PC with a GPU.

---

## Commands Reference

### `aura detect <file>`

**What it does:** Scans code and finds gaps (bugs, vulnerabilities, missing pieces).

**Works in:** Full mode AND Lite mode

**Usage:**
```bash
aura detect myfile.c                    # Detect gaps in C code
aura detect myfile.py --lang python     # Specify language explicitly
aura detect myfile.rs --json            # Output as JSON
aura detect - < myfile.go              # Read from stdin
cat myfile.js | aura detect -          # Pipe input
```

**Example output:**
```
Gaps found: 3
Severity: 0.82
Types: buffer_overflow, missing_error_handling, resource_leak
  [90%] pos 5: buffer_overflow
  [70%] pos 12: missing_error_handling
  [60%] pos 18: resource_leak
```

**JSON output fields:**
- `total_gaps_found` — Number of gaps detected
- `severity` — Weighted severity score (0.0 to 1.0)
- `stability` — Uncle Greg's S score: 1 - (sum(G) / N)
- `gap_magnitude` — Ratio of gaps to total lines
- `active_gap_types` — List of gap categories found
- `gaps` — Array of individual gap reports
- `engine` — "full" or "lite"

---

### `aura fix <file>`

**What it does:** Takes broken code and generates a fixed version.

**Works in:** Full mode ONLY (requires PyTorch + trained model)

**Usage:**
```bash
aura fix myfile.py                      # Fix Python code
aura fix myfile.c --lang c              # Fix C code
aura fix myfile.rs --json               # Output fix as JSON
aura fix myfile.py --output fixed.py    # Save to file
```

**What happens:**
1. Detects gaps using the neural model
2. Generates patches for each gap
3. Validates patches through the compiler middleware
4. Returns the fixed code

---

### `aura complete <file>`

**What it does:** Fills in incomplete code (TODOs, stubs, empty functions).

**Works in:** Full mode ONLY (requires PyTorch + trained model)

**Usage:**
```bash
aura complete myfile.py                 # Complete Python code
aura complete myfile.rs --lang rust     # Complete Rust code
aura complete myfile.go --json          # Output as JSON
```

**What happens:**
1. Finds incomplete sections (TODO, pass, stubs, empty bodies)
2. Uses the neural model to generate implementations
3. Validates through compiler
4. Returns completed code

---

### `aura translate <file> --to <language>`

**What it does:** Translates code from one programming language to another.

**Works in:** Full mode ONLY (requires PyTorch + trained model)

**Usage:**
```bash
aura translate myfile.py --to c         # Python to C
aura translate myfile.c --to rust       # C to Rust
aura translate myfile.js --to typescript # JS to TypeScript
aura translate myfile.go --to python    # Go to Python
```

**Supported translation targets:**
c, cpp, python, rust, go, java, javascript, typescript, bash, kotlin, swift, ruby, php, lua, zig, haskell, dart, and more.

---

### `aura analyze <file>`

**What it does:** Full analysis — gap detection + code stats + compiler validation.

**Works in:** Full mode AND Lite mode

**Usage:**
```bash
aura analyze myfile.c                   # Full analysis
aura analyze myfile.py --lang python    # Specify language
aura analyze myfile.rs --json           # Output as JSON
```

**Output includes:**
- Language detected
- Compiler validation result (does it compile?)
- All gaps found (same as detect)
- Code statistics (total lines, code lines, blank lines, comment lines)
- Suggested fix (full mode only)
- Whether the fix compiles

---

### `aura train`

**What it does:** Trains the neural model from scratch using synthetic data.

**Works in:** Full mode ONLY (requires PyTorch, ideally a GPU)

**Usage:**
```bash
aura train                              # Train everything (default 10000 steps)
aura train --pc-only --steps 5000       # Train PC model only, 5000 steps
aura train --steps 20000                # Longer training
aura train --batch-size 16              # Adjust batch size
```

**What happens:**
1. Generates synthetic training data (patch templates, translations, completions)
2. Trains the encoder-decoder transformer model
3. Saves checkpoints to `~/.aura/checkpoints/`
4. Reports loss and progress

**Requirements:**
- GPU recommended (CUDA). CPU works but is very slow.
- At least 4GB RAM
- PyTorch installed

---

### `aura export`

**What it does:** Exports your trained model to various formats.

**Works in:** Full mode ONLY

**Usage:**
```bash
aura export                             # Export to all formats
aura export --bundle ./my_model         # Export complete bundle
aura export --format gguf              # Export GGUF only (for Jan/Ollama)
aura export --format onnx              # Export ONNX
aura export --format c-array           # Export C headers (ESP32)
```

**Bundle contents:**
- `model.pt` — PyTorch weights
- `config.yaml` — Model configuration
- `tokenizer.json` — Byte-level tokenizer state
- `metadata.json` — Model info, capabilities
- `aura.gguf` — GGUF format (for Jan, Ollama, llama.cpp, LM Studio)
- `run.sh` — Convenience run script
- `README.md` — Usage instructions

---

### `aura ui`

**What it does:** Launches a local web interface (Gradio-based).

**Works in:** Full mode (requires gradio: `pip install gradio`)

**Usage:**
```bash
aura ui                                 # Launch on default port
aura ui --port 8080                     # Custom port
```

Opens a browser with:
- Code input area
- Detect / Fix / Complete / Translate buttons
- Results display
- Language selector

---

### `aura voice`

**What it does:** Voice control for AuRA (offline speech recognition).

**Works in:** Full mode (requires vosk: `pip install vosk`)

**Usage:**
```bash
aura voice                              # Start voice listener
```

Say commands like:
- "detect my file"
- "fix the code"
- "translate to rust"

---

### `aura info`

**What it does:** Shows system information, mode, available compilers, and model stats.

**Works in:** Full mode AND Lite mode

**Usage:**
```bash
aura info                               # Show everything
aura info --json                        # Output as JSON
```

**Output includes:**
- AuRA version
- Mode (Full or Lite)
- PyTorch version and GPU info (if available)
- Model info (path, size, architecture, training step)
- Available compilers on your system
- David's Brain status (ECL cycles, validated ratio)
- Training data stats
- Lite mode capabilities (if in lite mode)

---

### Global Options

These work with any command:

| Option | Description |
|--------|-------------|
| `--model PATH` | Path to a specific model .pt file |
| `--device DEVICE` | Force device: `cuda` or `cpu` |
| `--lite` | Force lite mode (skip neural model even if available) |
| `--json` | Output results as JSON (where supported) |
| `--lang LANGUAGE` | Specify input language (otherwise auto-detected) |

---

## Using on Your Phone (Jan + GGUF)

### What Is Jan?

Jan is a free, offline AI app that runs on your phone. It can load GGUF model files. AuRA exports to GGUF format, so you can load your trained AuRA model into Jan.

### Setup Steps

1. **Train AuRA on your PC:**
   ```bash
   aura train --steps 10000
   ```

2. **Export to GGUF:**
   ```bash
   aura export --format gguf
   ```
   This creates `aura.gguf` in your export directory.

3. **Get the GGUF to your phone:**
   - Push to your GitHub repo: copy `aura.gguf` to your repo and push
   - Or transfer via USB / shared folder
   - Or use a file sharing service

4. **Load in Jan:**
   - Open Jan on your Pixel 6
   - Go to **Downloaded Models**
   - Tap **Import Model**
   - Select `aura.gguf`
   - Start chatting with your model

### What You Get in Jan

Jan loads AuRA as a chat model. You can:
- Ask it to analyze code (paste code into chat)
- Ask it about gap detection
- Use it as a general code assistant

Note: Jan runs the model through its own chat interface. The full AuRA CLI features (detect, fix, translate, etc.) are only available through the command line.

### Alternative: Termux on Phone

If you want the full AuRA CLI experience on your phone (not through Jan), use Termux:

```bash
pkg install python git
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install pyyaml
pip install -e .
aura detect myfile.py
```

This gives you lite mode with gap detection and analysis.

---

## Using on Ventoy / USB Boot

### What Is Ventoy?

Ventoy is a multi-boot USB tool. You can have Linux Mint, Ubuntu, Kali, etc. all on one USB drive. Boot into any of them, then use AuRA.

### Setup

1. Boot into your Linux partition from Ventoy
2. Open a terminal
3. Install AuRA:
   ```bash
   git clone https://github.com/dturner3282-commits/AuRa.git
   cd AuRa
   pip install pyyaml
   pip install -e .
   aura info
   ```

4. Use it:
   ```bash
   aura detect myfile.c
   aura analyze myfile.py
   ```

### Persistence

If your Ventoy partition has persistent storage:
- AuRA's sovereign memory (David's Brain) saves to `~/.davids_brain/`
- This persists across reboots on persistent partitions
- On non-persistent boots, it starts fresh each time

---

## David's Brain (Sovereign AI)

David's Brain is the background intelligence layer. It runs alongside the main gap detection system and adds:

### ECL (Emergence Continuity Loop)

A self-referential reasoning engine:
1. Takes input (code, intent, query)
2. Classifies it through the taxonomy (Kingdom -> Phylum -> Class)
3. Checks sovereign memory for prior validated patterns
4. If found: auto-applies with high confidence
5. If not found: reasons about it, proposes action, logs for validation
6. Feeds output back as context for the next cycle

The "emergence" is that meaning arises from the interaction of taxonomy + memory + validation — not from hardcoded rules.

### Taxonomic Hierarchy

Code actions are classified like biological species:

| Level | Categories |
|-------|-----------|
| **Kingdom** | MANIPULATION (open, close, create, delete), ANALYSIS (detect, scan, analyze), TRANSFORMATION (compile, patch, fix, translate), GENERATION (generate, complete, synthesize), VALIDATION (test, verify, check) |
| **Phylum** | SOURCE_CODE (c, python, rust...), CONFIG (yaml, json...), BUILD (makefile, cmake...), BINARY (elf, wasm...), FIRMWARE (arduino, esp-idf...), SYSTEM (kernel, driver...) |
| **Class** | Gap types (buffer_overflow, null_dereference...) and Transform types (patch, translation, completion...) |
| **Order** | SEVERITY (critical to info), CONFIDENCE (certain to speculative) |
| **Family** | Populated by your patterns |
| **Genus** | Populated by learned code patterns |
| **Species** | Populated by validated specific instances |

### SOV-CHECK Gate

Before executing any action, the SOV-CHECK gate evaluates:
- Is there a validated Species match in memory? -> Auto-approve
- Is confidence above threshold (85%)? -> Auto-approve
- Otherwise -> Requires user validation

This ensures the system doesn't act on uncertain information without your approval.

### Genix Memory

SQLite-backed contextual knowledge store. Stores:
- Validated species (actions that worked before)
- ECL cycle logs (reasoning history)
- Concepts (emergent definitions)
- Key-value context data

Lives at `~/.davids_brain/sovereign.db`

---

## Uncle Greg's GDT Formulas

The mathematical foundation of gap detection:

### G = |E - O| (Gap Magnitude)

The difference between what's **expected** (E) and what's **observed** (O).
- Expected: clean, complete, secure code patterns
- Observed: what the code actually does
- Gap: the difference — what's missing or wrong

### C = [L, U] (Confidence Interval)

Each gap has a confidence window:
- L = lower bound (minimum confidence this is a real gap)
- U = upper bound (maximum confidence)
- If G falls within C, it's a meaningful gap

### Threshold Classifier

Binary decision: is this a gap or not?
- Above threshold: yes, report it
- Below threshold: noise, ignore it
- Default threshold: 0.5 (adjustable per command)

### S = 1 - (SumG / N) (Stability Score)

Overall code stability:
- S = 1.0: perfect code, no gaps found
- S = 0.5: half the code has gaps
- S = 0.0: every line has a gap
- N = total lines of code

### Delta+C Engine

Iterative gap closure:
1. Detect gaps
2. Generate patches
3. Validate through compiler
4. Re-detect gaps
5. Repeat until stable

---

## Gap Detection Categories

AuRA detects 16 categories of code gaps:

| Category | Description | Severity |
|----------|-------------|----------|
| `buffer_overflow` | Write beyond allocated memory | Critical (0.95) |
| `security_vulnerability` | Exploitable code pattern | Critical (0.90) |
| `syntax_error` | Code won't compile/parse | Critical (0.90) |
| `null_dereference` | Pointer used without null check | High (0.85) |
| `race_condition` | Shared state without sync | High (0.80) |
| `missing_bounds_check` | Array access without validation | High (0.80) |
| `uninitialized_variable` | Variable used before assignment | High (0.75) |
| `missing_error_handling` | No error check after fallible operation | Medium (0.70) |
| `resource_leak` | Opened resource never closed | Medium (0.70) |
| `logic_error` | Compiles but wrong behavior | Medium (0.70) |
| `missing_return` | Function path without return value | Medium (0.65) |
| `type_mismatch` | Incompatible types | Medium (0.60) |
| `incomplete_implementation` | TODO, FIXME, pass, stubs | Medium (0.60) |
| `missing_import` | Symbol used but not imported | Low (0.50) |
| `dead_code` | Unreachable code | Low (0.30) |
| `performance_issue` | Inefficient pattern | Low (0.30) |

---

## Supported Languages

### Full Support (detection rules + compiler validation)

C, C++, Python, Rust, Go, JavaScript, TypeScript, Java, Bash

### Detection Only (pattern matching)

Arduino/ESP32, Kotlin, Swift, Ruby, PHP, Lua, Assembly, Zig, Haskell, Dart

### Tokenizer Support (byte-level, can handle anything)

All of the above plus: SQL, Dockerfile, YAML, JSON, TOML, XML, Makefile, CMake, Perl, Lisp/ECL, Terraform, GraphQL, Protobuf, INI, PowerShell, LLVM IR, MicroPython, ESP-IDF

---

## Training Your Own Model

### Prerequisites

- Python 3.9+
- PyTorch (with CUDA for GPU acceleration)
- At least 4GB RAM (8GB+ recommended)
- GPU recommended but not required

### Quick Training

```bash
# Clone and install
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install torch pyyaml
pip install -e .

# Train (GPU recommended)
aura train --steps 10000
```

### Training Options

| Option | Default | Description |
|--------|---------|-------------|
| `--steps N` | 10000 | Number of training steps |
| `--batch-size N` | 8 | Batch size (reduce if OOM) |
| `--pc-only` | False | Train only the PC model (faster) |
| `--lr RATE` | 1e-4 | Learning rate |

### What Training Does

1. **Generates synthetic data** from built-in templates:
   - Patch templates (broken code -> fixed code pairs)
   - Translation templates (Python -> C, Rust -> Go, etc.)
   - Completion templates (incomplete -> complete code)

2. **Trains an encoder-decoder transformer**:
   - Encoder reads input code
   - Decoder generates output (fix, translation, completion)
   - Byte-level tokenization (handles any language)

3. **Saves checkpoints** to `~/.aura/checkpoints/`

### After Training

```bash
# Check model info
aura info

# Use it
aura detect myfile.c
aura fix myfile.py
aura translate myfile.py --to rust

# Export for other devices
aura export --bundle ./my_model
```

---

## Exporting Models

### GGUF (for Jan, Ollama, llama.cpp, LM Studio)

```bash
aura export --format gguf
```

Creates `aura.gguf` — a universal model file that works with:
- **Jan** (your Pixel 6)
- **Ollama** (any computer)
- **llama.cpp** (command line)
- **LM Studio** (desktop app)

### Full Bundle

```bash
aura export --bundle ./my_model
```

Creates a complete directory with everything needed to use the model anywhere:
- model.pt, config.yaml, tokenizer.json, metadata.json, aura.gguf, run.sh, README.md

### ONNX (cross-platform inference)

```bash
aura export --format onnx
```

For use with ONNX Runtime, TensorRT, etc.

### C Arrays (ESP32 firmware)

```bash
aura export --format c-array
```

Generates C header files with quantized int8 weights for embedding in ESP32 firmware.

---

## Plugins

### Compiler Middleware

Validates AI-generated code using real compilers (gcc, clang, rustc, python, go, javac, node, tsc, bash). Automatically detects which compilers are installed on your system.

- Used by `fix`, `complete`, and `analyze` commands
- Runs locally, no APIs
- Supports iterative fixing (compile -> fix errors -> compile again)

### Voice Control

Offline speech recognition using Vosk.

```bash
pip install vosk
aura voice
```

### Web UI

Local browser-based interface using Gradio.

```bash
pip install gradio
aura ui
```

### ESP32 Plugin

For deploying tiny models to ESP32 microcontrollers.

### JetKVM Plugin (Future)

Remote hardware control via JetKVM device.

---

## Troubleshooting

### "PyTorch not installed, using lite mode"

This is normal on phones and lightweight devices. Lite mode works for gap detection and analysis. To get full features, install PyTorch:
```bash
pip install torch
```

### "No model found, using lite mode"

PyTorch is installed but you haven't trained a model yet. Train one:
```bash
aura train --steps 5000
```

### "'fix' command requires PyTorch"

The fix, complete, and translate commands need the neural model. These only work in full mode.

### "Compiler for X not installed, skipping check"

The compiler middleware needs real compilers. Install them:
```bash
# Ubuntu/Debian
sudo apt install gcc g++ rustc golang-go nodejs

# Termux
pkg install clang golang nodejs-lts
```

### Training is slow

- Use a GPU: `pip install torch` with CUDA support
- Reduce steps: `aura train --steps 1000`
- Reduce batch size: `aura train --batch-size 4`

### GGUF export fails

Make sure you have a trained model first:
```bash
aura train --steps 5000
aura export --format gguf
```

### Jan can't load the model

AuRA's GGUF uses a custom architecture ("aura"). Jan might not recognize it as a standard LLM architecture. In that case:
- Use AuRA directly via Termux (full CLI experience)
- Or wait for Jan to add custom architecture support

---

## Architecture Overview

```
AuRA
 |
 |-- CLI (aura command)
 |    |-- detect    <- Works in Full + Lite mode
 |    |-- fix       <- Full mode only
 |    |-- complete  <- Full mode only
 |    |-- translate <- Full mode only
 |    |-- analyze   <- Works in Full + Lite mode
 |    |-- train     <- Full mode only
 |    |-- export    <- Full mode only
 |    |-- ui        <- Full mode only
 |    |-- voice     <- Full mode only
 |    |-- info      <- Works in Full + Lite mode
 |
 |-- Core
 |    |-- Model (encoder-decoder transformer)
 |    |-- GDT Engine (Uncle Greg's gap detection)
 |    |-- Tokenizer (byte-level, any language)
 |    |-- Data Generator (synthetic training data)
 |    |-- Training Pipeline
 |    |-- Inference Engine (Full: neural, Lite: rule-based)
 |    |-- Export (PyTorch, GGUF, ONNX, C arrays)
 |    |-- Sovereign (David's Brain: ECL, taxonomy, memory)
 |
 |-- Plugins
      |-- Compiler Middleware (gcc, rustc, python, go, node, etc.)
      |-- Voice (offline speech with Vosk)
      |-- UI (Gradio web interface)
      |-- ESP32 (embedded deployment)
      |-- JetKVM (remote hardware control)
```

### Data Flow

```
Input Code
    |
    v
Language Detection (auto or specified)
    |
    v
+---Full Mode?---+---Lite Mode?---+
|                 |                |
v                 v                |
Neural Model      Rule-based       |
(Transformer)     Pattern Match    |
|                 (GDT Rules)      |
v                 v                |
Gap Results       Gap Results      |
|                 |                |
+--------+--------+                |
         |                         |
         v                         |
Compiler Validation                |
(if available)                     |
         |                         |
         v                         |
David's Brain                      |
(ECL classify + SOV-CHECK)         |
         |                         |
         v                         |
Output (terminal / JSON / UI)      |
```

---

## Quick Reference Card

```
DETECT GAPS:     aura detect myfile.c
FIX CODE:        aura fix myfile.py          (needs PyTorch)
COMPLETE CODE:   aura complete myfile.rs     (needs PyTorch)
TRANSLATE:       aura translate myfile.py --to c  (needs PyTorch)
FULL ANALYSIS:   aura analyze myfile.go
TRAIN MODEL:     aura train --steps 10000    (needs PyTorch + GPU)
EXPORT MODEL:    aura export --bundle ./out  (needs PyTorch)
SYSTEM INFO:     aura info
WEB UI:          aura ui                     (needs gradio)
VOICE CONTROL:   aura voice                  (needs vosk)
FORCE LITE:      aura --lite detect myfile.c
JSON OUTPUT:     aura detect myfile.c --json
```

---

*AuRA v0.2.0 — Built by David Turner. 100% offline. Your code never leaves your machine.*
