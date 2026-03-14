"""
AuRA CLI - David's Brain - Simple command-line interface.

Usage:
    aura process <file>             Auto-detect file type, show options (the mirror)
    aura signal <file>              Decode audio signal (11-step protocol)
    aura search <query>             Search knowledge base (try 'Greg Turner')
    aura detect <file>              Find gaps/bugs in code
    aura fix <file>                 Fix broken code
    aura complete <file>            Complete incomplete code
    aura translate <file> --to <lang>  Translate to another language
    aura analyze <file>             Full analysis (detect + fix + validate)
    aura train                      Train the model from scratch
    aura train --resume <checkpoint>  Resume training
    aura export --bundle <dir>      Export downloadable model bundle
    aura ui                         Launch Gradio web UI
    aura voice                      Voice control (Vosk/SUSI)
    aura info                       Show model info

All offline. No APIs. No internet required.
"""

import argparse
import sys
import json
import os
from pathlib import Path

# Check if PyTorch is available — determines full vs lite mode
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def read_input(file_path: str) -> str:
    """Read code from file or stdin."""
    if file_path == "-":
        return sys.stdin.read()
    with open(file_path, "r") as f:
        return f.read()


def get_model_path() -> str:
    """Find the model file. Check common locations."""
    candidates = [
        "checkpoints/pc_model_final.pt",
        "pc_model_final.pt",
        os.path.expanduser("~/.aura/model.pt"),
        os.path.expanduser("~/aura_model.pt"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]  # default even if not found yet


def _get_engine(args):
    """Get the appropriate inference engine (full or lite)."""
    if TORCH_AVAILABLE and not getattr(args, 'lite', False):
        model_path = args.model or get_model_path()
        if os.path.exists(model_path):
            from aura.core.inference.engine import InferenceEngine
            return InferenceEngine(model_path, device=args.device)
        else:
            print(f"[INFO] No model found at {model_path}, using lite mode (rule-based)", file=sys.stderr)
    elif not TORCH_AVAILABLE:
        print("[INFO] PyTorch not installed, using lite mode (rule-based)", file=sys.stderr)

    from aura.core.inference.lite_engine import LiteEngine
    return LiteEngine()


def cmd_detect(args):
    """Detect gaps in code."""
    code = read_input(args.file)
    engine = _get_engine(args)
    results = engine.detect_gaps(code, language=args.lang)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for report in results:
            print(f"\nGaps found: {report['total_gaps_found']}")
            print(f"Severity: {report['severity']}")
            if report["active_gap_types"]:
                print(f"Types: {', '.join(report['active_gap_types'])}")
            for gap in report["gaps"]:
                print(f"  [{gap['confidence']:.0%}] pos {gap['position']}: {gap['category']}")


def cmd_fix(args):
    """Fix broken code."""
    if not TORCH_AVAILABLE:
        print("[ERROR] 'fix' command requires PyTorch. Install with: pip install torch", file=sys.stderr)
        print("[INFO] Use 'aura detect' for rule-based gap detection (works without PyTorch)", file=sys.stderr)
        sys.exit(1)

    from aura.core.inference.engine import InferenceEngine

    code = read_input(args.file)
    engine = InferenceEngine(args.model or get_model_path(), device=args.device)
    result = engine.fix_code(code, language=args.lang, validate=not args.no_validate)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if args.output:
            with open(args.output, "w") as f:
                f.write(result["fixed"])
            print(f"Fixed code written to {args.output}")
        else:
            print(result["fixed"])

        if result.get("validation"):
            v = result["validation"]
            if v["patched_valid"]:
                print("\n[OK] Fixed code compiles successfully", file=sys.stderr)
            else:
                print(f"\n[WARN] Fixed code has errors: {v['patched_errors']}", file=sys.stderr)


def cmd_complete(args):
    """Complete incomplete code."""
    if not TORCH_AVAILABLE:
        print("[ERROR] 'complete' command requires PyTorch. Install with: pip install torch", file=sys.stderr)
        sys.exit(1)

    from aura.core.inference.engine import InferenceEngine

    code = read_input(args.file)
    engine = InferenceEngine(args.model or get_model_path(), device=args.device)
    result = engine.complete_code(code, language=args.lang)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.output:
            with open(args.output, "w") as f:
                f.write(result["completed"])
            print(f"Completed code written to {args.output}")
        else:
            print(result["completed"])


def cmd_translate(args):
    """Translate code to another language."""
    if not TORCH_AVAILABLE:
        print("[ERROR] 'translate' command requires PyTorch. Install with: pip install torch", file=sys.stderr)
        sys.exit(1)

    from aura.core.inference.engine import InferenceEngine

    code = read_input(args.file)
    engine = InferenceEngine(args.model or get_model_path(), device=args.device)

    from_lang = args.lang
    if from_lang is None:
        from aura.plugins.compiler.middleware import CompilerMiddleware
        from_lang = CompilerMiddleware().detect_language(code)

    result = engine.translate(code, from_lang=from_lang, to_lang=args.to)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.output:
            with open(args.output, "w") as f:
                f.write(result["translated"])
            print(f"Translated code written to {args.output}")
        else:
            print(result["translated"])

        if not result["target_valid"]:
            print(f"\n[WARN] Translation has errors: {result['target_errors']}", file=sys.stderr)


def cmd_analyze(args):
    """Full analysis."""
    code = read_input(args.file)
    engine = _get_engine(args)
    result = engine.analyze(code, language=args.lang)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Language: {result['language']}")
        print(f"Compiles: {'Yes' if result['original_compiles'] else 'No'}")
        if result["compiler_errors"]:
            print(f"Errors: {result['compiler_errors']}")

        for report in result["gaps"]:
            print(f"\nGaps: {report['total_gaps_found']}, Severity: {report['severity']}")
            for gap in report["gaps"]:
                print(f"  [{gap['confidence']:.0%}] {gap['category']} at pos {gap['position']}")

        if result["suggested_fix"]:
            print(f"\n--- Suggested Fix ---")
            print(result["suggested_fix"])
            if result["fix_compiles"] is not None:
                print(f"\nFix compiles: {'Yes' if result['fix_compiles'] else 'No'}")


def cmd_train(args):
    """Train the model."""
    from aura.core.training.train import Trainer

    trainer = Trainer(config_path=args.config, device=args.device)

    if args.esp_only:
        trainer.train_esp32_model(
            max_steps=args.steps,
            checkpoint_dir=args.checkpoint_dir,
        )
    elif args.pc_only:
        trainer.train_pc_model(
            max_steps=args.steps,
            checkpoint_dir=args.checkpoint_dir,
            resume_from=args.resume,
        )
    else:
        trainer.train_all(
            pc_steps=args.steps,
            esp_steps=args.esp_steps,
            checkpoint_dir=args.checkpoint_dir,
        )


def cmd_export(args):
    """Export model bundle."""
    from aura.core.export.exporter import ModelExporter

    checkpoint = args.model or get_model_path()
    if not os.path.exists(checkpoint):
        print(f"No model found at {checkpoint}")
        print("Train one first: aura train")
        sys.exit(1)

    output_dir = args.bundle or "aura_bundle"
    ModelExporter.export_model_bundle(
        checkpoint_path=checkpoint,
        output_dir=output_dir,
        model_name=args.name or "aura",
        include_gguf=not args.no_gguf,
    )


def cmd_ui(args):
    """Launch Gradio web UI."""
    from aura.plugins.ui.app import launch
    launch(
        model_path=args.model or "",
        share=args.share,
        port=args.port,
    )


def cmd_voice(args):
    """Start voice control."""
    from aura.plugins.voice.bridge import start_voice
    start_voice(
        engine=args.engine,
        model_path=args.model or get_model_path(),
        vosk_model=args.vosk_model,
    )


def cmd_process(args):
    """Adaptive processor — auto-detect file type, show options, route to plugin."""
    from aura.process import detect_file_type, get_actions_for_category, run_action, interactive_process

    file_path = args.file
    if not os.path.exists(file_path):
        print("File not found: %s" % file_path, file=sys.stderr)
        sys.exit(1)

    if args.action:
        # Direct mode: skip menu, run the specified action
        file_info = detect_file_type(file_path)
        result = run_action(file_path, args.action, file_info)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_process_result(result)
    else:
        # Interactive mode: show options, ask user
        result = interactive_process(file_path)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_process_result(result)


def _print_process_result(result):
    """Pretty-print adaptive processor results."""
    if not result:
        return

    # Signal decode result
    if 'decoded_word' in result:
        print("\n" + "=" * 50)
        print("  SIGNAL DECODE RESULT")
        print("=" * 50)
        print("  Word:       %s" % result.get('summary', 'N/A'))
        print("  ECL:        %.1f / 7.0" % result.get('ecl', 0))
        print("  Confidence: %s" % result.get('confidence', 'N/A'))
        print("  Signal:     %s" % result.get('signal_type', 'N/A'))
        print("=" * 50)
        if result.get('technical_report'):
            print("\n--- Technical Report ---")
            print(result['technical_report'])
        return

    # Frequency inventory
    if result.get('type') == 'frequency_inventory':
        print("\nFrequency Inventory (%d windows, %d Hz sample rate)" % (
            result['total_windows'], result['sample_rate']))
        for f in result['frequencies']:
            print("  %6.0f Hz  —  %d hits" % (f['freq_hz'], f['count']))
        return

    # Gap detection result
    if 'results' in result:
        for report in result['results']:
            print("\nGaps found: %d" % report.get('total_gaps_found', 0))
            print("Severity: %s" % report.get('severity', 'N/A'))
            for gap in report.get('gaps', []):
                print("  [%.0f%%] pos %d: %s" % (
                    gap['confidence'] * 100, gap['position'], gap['category']))
        return

    # Generic fallback
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 200:
            print("  %s: %s..." % (key, value[:200]))
        else:
            print("  %s: %s" % (key, value))


def cmd_signal(args):
    """Decode an audio signal using the 11-step protocol."""
    file_path = args.file
    if not os.path.exists(file_path):
        print("File not found: %s" % file_path, file=sys.stderr)
        sys.exit(1)

    from aura.plugins.signal.engine import decode_file
    result = decode_file(file_path)

    if args.json:
        # Remove technical_report from JSON for cleaner output unless verbose
        output = dict(result)
        if not args.verbose:
            output.pop('technical_report', None)
        print(json.dumps(output, indent=2, default=str))
    else:
        print("\n" + "=" * 50)
        print("  SIGNAL DECODE RESULT")
        print("=" * 50)
        print("  Word:       %s" % result.get('summary', 'N/A'))
        print("  ECL:        %.1f / 7.0" % result.get('ecl', 0))
        print("  Confidence: %s" % result.get('confidence', 'N/A'))
        print("  Signal:     %s" % result.get('signal_type', 'N/A'))
        print("=" * 50)

        if args.verbose and result.get('technical_report'):
            print("\n--- Technical Report ---")
            print(result['technical_report'])


def cmd_search(args):
    """Search AuRA knowledge base. Easter egg: try 'Greg Turner'."""
    query = args.query.strip()

    # Easter egg: Uncle Greg's GDT formulas
    if query.lower() in ('greg turner', 'uncle greg', 'gdt', 'greg'):
        print()
        print("=" * 60)
        print("  Uncle Greg's Gap Detection Technology (GDT)")
        print("=" * 60)
        print()
        print("  G = |E - O|        Gap magnitude (expected vs observed)")
        print("  C = [L, U]         Confidence interval")
        print("  Classifier         Binary gap / no-gap decision")
        print("  S = 1 - (SumG / N) Soundness score")
        print("  Delta + C Engine   Iterative gap closure")
        print()
        print("  ---")
        print()
        print("  Thank you, Greg, for the ideas and groundwork")
        print("  that helped spark this project.")
        print("  Your thinking opened the gap. We followed it.")
        print()
        print("=" * 60)
        return

    # General search: look through sovereign memory concepts
    try:
        from aura.core.sovereign.brain import create_brain
        brain = create_brain()
        concept = brain.memory.get_concept(query.upper())
        if concept:
            print("\n  %s" % concept['name'])
            print("  %s" % concept['definition'])
            if concept.get('relationships'):
                print("  Related: %s" % ', '.join(concept['relationships']))
        else:
            # Search genix
            value = brain.memory.get_genix(query)
            if value:
                print("\n  %s: %s" % (query, value))
            else:
                print("\n  No results for '%s'" % query)
                print("  Try: ECL, PIM, GDT, Hangman, Loom, Genix, or 'Greg Turner'")
        brain.close()
    except Exception:
        print("\n  No results for '%s'" % query)
        print("  Try: 'Greg Turner', 'GDT', 'ECL', 'PIM', 'Hangman'")


def cmd_info(args):
    """Show model and system info."""
    print("=== AuRA - Autonomous Universal Recognition Agent ===")
    print(f"Version: 0.2.0")

    if TORCH_AVAILABLE:
        print(f"Mode: Full (PyTorch {torch.__version__})")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
        print(f"Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

        model_path = args.model or get_model_path()
        if os.path.exists(model_path):
            ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
            config = ckpt.get("config", {})
            pc = config.get("pc_model", {})
            print(f"\n=== Model Info ===")
            print(f"Path: {model_path}")
            print(f"Size: {os.path.getsize(model_path) / 1e6:.1f} MB")
            print(f"Dim: {pc.get('dim', '?')}")
            print(f"Encoder layers: {pc.get('encoder_layers', '?')}")
            print(f"Decoder layers: {pc.get('decoder_layers', '?')}")
            print(f"Heads: {pc.get('heads', '?')}")
            print(f"Training step: {ckpt.get('step', '?')}")
        else:
            print(f"\nNo model found at {model_path}")
            print("Train one with: aura train")
    else:
        print(f"Mode: Lite (rule-based, no PyTorch)")
        print(f"Note: Install PyTorch for full AI capabilities: pip install torch")

    # Available compilers
    from aura.plugins.compiler.middleware import CompilerMiddleware
    cm = CompilerMiddleware()
    langs = cm.get_available_languages()
    print(f"\n=== Available Compilers ===")
    print(f"Languages: {', '.join(langs) if langs else 'none detected'}")

    # Sovereign brain status
    try:
        from aura.core.sovereign.brain import create_brain
        brain = create_brain()
        ctx = brain.get_context()
        stats = ctx["ecl_stats"]
        print(f"\n=== David's Brain ===")
        print(f"ECL cycles: {stats['total_cycles']}")
        print(f"Validated ratio: {stats['validated_ratio']:.0%}")
        print(f"Context depth: {stats['context_depth']}")
        brain.close()
    except Exception:
        print(f"\n=== David's Brain ===")
        print(f"Status: Not initialized (run any command to start)")

    # Training data stats
    from aura.core.data.generator import PATCH_TEMPLATES, TRANSLATION_TEMPLATES, COMPLETION_TEMPLATES
    print(f"\n=== Training Data ===")
    print(f"Patch templates: {len(PATCH_TEMPLATES)}")
    print(f"Translation templates: {len(TRANSLATION_TEMPLATES)}")
    print(f"Completion templates: {len(COMPLETION_TEMPLATES)}")

    # Lite engine info
    if not TORCH_AVAILABLE:
        from aura.core.inference.lite_engine import LiteEngine
        lite = LiteEngine()
        info = lite.info()
        print(f"\n=== Lite Mode ===")
        print(f"Available: {', '.join(info['capabilities'])}")
        print(f"Limited: {', '.join(info['limited_capabilities'])}")
        print(f"Gap categories: {len(info['gap_categories'])}")


def main():
    parser = argparse.ArgumentParser(
        prog="aura",
        description="AuRA - Offline AI compiler/patcher/translator. No APIs.",
    )
    parser.add_argument("--model", type=str, default=None, help="Path to model .pt file")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda/cpu)")
    parser.add_argument("--lite", action="store_true", help="Force lite mode (rule-based, no PyTorch needed)")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # detect
    p_detect = subparsers.add_parser("detect", help="Detect gaps/bugs in code")
    p_detect.add_argument("file", help="Code file (or - for stdin)")
    p_detect.add_argument("--lang", type=str, default=None, help="Language")
    p_detect.add_argument("--json", action="store_true", help="JSON output")
    p_detect.set_defaults(func=cmd_detect)

    # fix
    p_fix = subparsers.add_parser("fix", help="Fix broken code")
    p_fix.add_argument("file", help="Code file (or - for stdin)")
    p_fix.add_argument("--lang", type=str, default=None, help="Language")
    p_fix.add_argument("--output", "-o", type=str, default=None, help="Output file")
    p_fix.add_argument("--json", action="store_true", help="JSON output")
    p_fix.add_argument("--no-validate", action="store_true", help="Skip compiler validation")
    p_fix.set_defaults(func=cmd_fix)

    # complete
    p_complete = subparsers.add_parser("complete", help="Complete incomplete code")
    p_complete.add_argument("file", help="Code file (or - for stdin)")
    p_complete.add_argument("--lang", type=str, default=None, help="Language")
    p_complete.add_argument("--output", "-o", type=str, default=None, help="Output file")
    p_complete.add_argument("--json", action="store_true", help="JSON output")
    p_complete.set_defaults(func=cmd_complete)

    # translate
    p_translate = subparsers.add_parser("translate", help="Translate code to another language")
    p_translate.add_argument("file", help="Code file (or - for stdin)")
    p_translate.add_argument("--to", required=True, help="Target language")
    p_translate.add_argument("--lang", type=str, default=None, help="Source language")
    p_translate.add_argument("--output", "-o", type=str, default=None, help="Output file")
    p_translate.add_argument("--json", action="store_true", help="JSON output")
    p_translate.set_defaults(func=cmd_translate)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Full code analysis")
    p_analyze.add_argument("file", help="Code file (or - for stdin)")
    p_analyze.add_argument("--lang", type=str, default=None, help="Language")
    p_analyze.add_argument("--json", action="store_true", help="JSON output")
    p_analyze.set_defaults(func=cmd_analyze)

    # train
    p_train = subparsers.add_parser("train", help="Train model from scratch")
    p_train.add_argument("--config", type=str, default=None, help="Config YAML file")
    p_train.add_argument("--steps", type=int, default=None, help="Training steps")
    p_train.add_argument("--esp-steps", type=int, default=None, help="ESP32 model steps")
    p_train.add_argument("--checkpoint-dir", type=str, default="checkpoints")
    p_train.add_argument("--resume", type=str, default=None, help="Resume from checkpoint")
    p_train.add_argument("--pc-only", action="store_true", help="Only train PC model")
    p_train.add_argument("--esp-only", action="store_true", help="Only train ESP32 model")
    p_train.set_defaults(func=cmd_train)

    # export
    p_export = subparsers.add_parser("export", help="Export downloadable model bundle")
    p_export.add_argument("--bundle", type=str, default="aura_bundle", help="Output directory")
    p_export.add_argument("--name", type=str, default="aura", help="Model name")
    p_export.add_argument("--no-gguf", action="store_true", help="Skip GGUF export")
    p_export.set_defaults(func=cmd_export)

    # ui
    p_ui = subparsers.add_parser("ui", help="Launch Gradio web UI")
    p_ui.add_argument("--share", action="store_true", help="Create public URL")
    p_ui.add_argument("--port", type=int, default=7860, help="Port number")
    p_ui.set_defaults(func=cmd_ui)

    # voice
    p_voice = subparsers.add_parser("voice", help="Voice control (Vosk/SUSI)")
    p_voice.add_argument("--engine", type=str, default="vosk", choices=["vosk", "susi"], help="Voice engine")
    p_voice.add_argument("--vosk-model", type=str, default=None, help="Path to Vosk model")
    p_voice.set_defaults(func=cmd_voice)

    # process (adaptive — the cognitive mirror)
    p_process = subparsers.add_parser("process", help="Auto-detect file type and show options")
    p_process.add_argument("file", help="Any file (audio, code, config, text, image, binary)")
    p_process.add_argument("--action", type=str, default=None, help="Skip menu, run this action directly")
    p_process.add_argument("--json", action="store_true", help="JSON output")
    p_process.set_defaults(func=cmd_process)

    # signal (direct signal decode)
    p_signal = subparsers.add_parser("signal", help="Decode audio signal (11-step protocol)")
    p_signal.add_argument("file", help="Audio file (WAV, MP3, M4A, OGG, FLAC)")
    p_signal.add_argument("--json", action="store_true", help="JSON output")
    p_signal.add_argument("--verbose", "-v", action="store_true", help="Include technical report")
    p_signal.set_defaults(func=cmd_signal)

    # search (knowledge base + Easter egg)
    p_search = subparsers.add_parser("search", help="Search AuRA knowledge base")
    p_search.add_argument("query", help="Search term (try 'Greg Turner')")
    p_search.set_defaults(func=cmd_search)

    # info
    p_info = subparsers.add_parser("info", help="Show model and system info")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
