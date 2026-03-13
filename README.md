# AuRA — Autonomous Universal Recognition Agent

A fully offline, sovereign AI system for code understanding, gap detection, patching, and cross-language translation. No APIs, no cloud, no internet required after setup.

## What Is This?

AuRA is a **command-line AI toolkit** that runs 100% on your machine. It can:

- **Detect** gaps, bugs, and vulnerabilities in code
- **Fix** broken code automatically
- **Complete** incomplete code (fill in TODOs, stubs)
- **Translate** code between 30+ programming languages
- **Analyze** code with full gap detection + compiler validation
- **Train** from scratch using synthetic data — no external datasets needed

It includes **David's Brain** — a sovereign background intelligence layer with:
- **ECL** (Emergence Continuity Loop) — self-referential reasoning
- **Hangman** — structured code analysis
- **Loom** — alignment model (warp/weft/observer)
- **PIM** — Uncle Greg's Pattern-based Identification Method
- **Genix** — SQLite-backed contextual memory
- **SOV-CHECK** — sovereignty validation gate
- **GDT** — Gap Detection Technology using Uncle Greg's formulas

## Quick Install

### PC / Laptop (Python 3.9+)

```bash
git clone https://github.com/dturner3282-commits/AuRa.git
cd AuRa
pip install torch pyyaml
pip install -e .
aura info
```

### Termux (Android / Fire Tablet) — No Login Required

```bash
pkg install python git && git clone https://github.com/dturner3282-commits/AuRa.git && cd AuRa && pip install torch pyyaml && pip install -e . && aura info
```

Or use the install script:
```bash
curl -sL https://raw.githubusercontent.com/dturner3282-commits/AuRa/main/scripts/install_termux.sh | bash
```

## Usage

```bash
aura detect myfile.c              # Find gaps/bugs
aura fix myfile.py                # Fix broken code
aura complete myfile.rs           # Complete incomplete code
aura translate myfile.py --to c   # Translate Python to C
aura analyze myfile.go            # Full analysis
aura train                        # Train from scratch
aura train --pc-only --steps 1000 # Quick PC model training
aura export --bundle ./my_model   # Export downloadable bundle
aura ui                           # Launch web UI (requires gradio)
aura voice                        # Voice control (requires vosk)
aura info                         # Show system info
```

## Architecture

```
aura/
  cli.py                    # Command-line interface
  core/
    model/                  # Transformer architecture (encoder-decoder)
    gdt/                    # Gap Detection Technology (Uncle Greg's formulas)
    tokenizer/              # Byte-level tokenizer (handles any language)
    data/                   # Synthetic training data generator
    training/               # Training pipeline
    inference/              # Inference engine
    export/                 # Model export (PyTorch + GGUF)
    sovereign/              # David's Brain (ECL, taxonomy, memory)
  plugins/
    esp32/                  # ESP32 embedded deployment (tiny model)
    compiler/               # Real compiler validation middleware
    voice/                  # Offline voice control (Vosk/SUSI.AI)
    ui/                     # Gradio web interface
    jetkvm/                 # Remote hardware control (future)
config.yaml                 # Model configuration
DAVID_PROMPT.json           # Reusable build prompt for AI agents
```

## Supported Languages

C, C++, Python, Rust, Go, JavaScript, TypeScript, Java, Kotlin, Swift, Ruby, PHP, Lua, Bash, Arduino/ESP32, Zig, Haskell, Dart, Terraform, GraphQL, Protobuf, SQL, Dockerfile, YAML, Makefile, CMake, Perl, Lisp/ECL, Assembly, and more.

## Gap Detection Categories

Missing error handling, buffer overflow, null dereference, resource leak, race condition, security vulnerability, type mismatch, missing import, incomplete implementation, missing bounds check, uninitialized variable, dead code, missing return, syntax error, logic error, performance issue.

## Uncle Greg's GDT Formulas

- **G = |E - O|** — Gap magnitude (expected vs observed)
- **C = [L, U]** — Confidence interval
- **Threshold classifier** — Binary gap/no-gap decision
- **S = 1 - (SumG / N)** — Soundness score
- **Delta+C engine** — Iterative gap closure

## Three Deployment Options

1. **Terminal tool** (primary) — `aura detect`, `aura fix`, etc.
2. **Local web UI** — `aura ui` (Gradio-based browser interface)
3. **Background agent** — Always-on with voice control, monitoring, JetKVM integration (future)

## License

MIT
