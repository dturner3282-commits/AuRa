"""
Foundry Space — Gradio Web UI for GapDet.

Browser-based interface for the GapDet offline AI model.
Works locally, on Termux, or as a Hugging Face Space.

Usage:
    python -m aura.ui.app
    # or
    gapdet ui

Opens http://localhost:7860 with a clean interface for:
- Detect gaps/bugs in code
- Fix/patch broken code
- Complete incomplete code
- Translate between languages
- Full analysis (detect + fix + validate)
- Train the model
- View model info

100% offline after pip install. No APIs.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional

# Lazy import gradio — only needed when UI is launched
gradio = None


def _ensure_gradio():
    global gradio
    if gradio is None:
        try:
            import gradio as gr
            gradio = gr
        except ImportError:
            print("Gradio not installed. Install with: pip install gradio")
            print("Then run: gapdet ui")
            sys.exit(1)
    return gradio


def _load_engine(model_path: Optional[str] = None):
    """Load inference engine, return None if no model found."""
    try:
        from aura.core.inference.engine import InferenceEngine
        if model_path and os.path.exists(model_path):
            return InferenceEngine(model_path)
        # Try default locations
        defaults = [
            "checkpoints/pc_model_final.pt",
            os.path.expanduser("~/.davids_brain/model.pt"),
            "gapdet_model.pt",
        ]
        for p in defaults:
            if os.path.exists(p):
                return InferenceEngine(p)
        return None
    except Exception:
        return None


def _load_brain():
    """Load David's Brain for background context."""
    try:
        from aura.core.sovereign.brain import create_brain
        return create_brain()
    except Exception:
        return None


def detect_gaps(code: str, language: str, model_path: str) -> str:
    """Detect gaps/bugs in code."""
    if not code.strip():
        return "Please paste some code to analyze."

    engine = _load_engine(model_path if model_path.strip() else None)
    brain = _load_brain()

    # Run through brain for context
    if brain:
        brain.process("detect gaps", code=code[:200], language=language, auto_validate=True)

    if engine:
        try:
            result = engine.detect_gaps(code, language=language if language != "auto" else None)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error during detection: {e}"
    else:
        # No trained model — show what brain thinks
        from aura.plugins.compiler.middleware import CompilerMiddleware
        mw = CompilerMiddleware()
        lang = language if language != "auto" else mw.detect_language(code)
        ok, msg = mw.check_syntax(code, lang)
        result = {
            "language": lang,
            "compiler_check": {"valid": ok, "message": msg},
            "note": "No trained model loaded. Train with: gapdet train",
        }
        if brain:
            result["brain_context"] = brain.get_context()
        return json.dumps(result, indent=2)


def fix_code(code: str, language: str, model_path: str) -> str:
    """Fix/patch broken code."""
    if not code.strip():
        return "Please paste some code to fix."

    engine = _load_engine(model_path if model_path.strip() else None)
    brain = _load_brain()

    if brain:
        brain.process("fix code", code=code[:200], language=language, auto_validate=True)

    if engine:
        try:
            result = engine.fix_code(code, language=language if language != "auto" else None)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error during fix: {e}"
    else:
        return json.dumps({
            "note": "No trained model loaded. Train with: gapdet train",
            "suggestion": "The model needs training data to generate fixes.",
        }, indent=2)


def complete_code(code: str, language: str, model_path: str) -> str:
    """Complete incomplete code."""
    if not code.strip():
        return "Please paste some code to complete."

    engine = _load_engine(model_path if model_path.strip() else None)
    if engine:
        try:
            result = engine.complete_code(code, language=language if language != "auto" else None)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error during completion: {e}"
    else:
        return json.dumps({
            "note": "No trained model loaded. Train with: gapdet train",
        }, indent=2)


def translate_code(code: str, from_lang: str, to_lang: str, model_path: str) -> str:
    """Translate code between languages."""
    if not code.strip():
        return "Please paste some code to translate."
    if to_lang == "auto":
        return "Please select a target language."

    engine = _load_engine(model_path if model_path.strip() else None)
    if engine:
        try:
            result = engine.translate(
                code,
                from_lang=from_lang if from_lang != "auto" else None,
                to_lang=to_lang,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error during translation: {e}"
    else:
        return json.dumps({
            "note": "No trained model loaded. Train with: gapdet train",
        }, indent=2)


def full_analysis(code: str, language: str, model_path: str) -> str:
    """Full analysis: detect + fix + validate."""
    if not code.strip():
        return "Please paste some code to analyze."

    engine = _load_engine(model_path if model_path.strip() else None)
    brain = _load_brain()

    if brain:
        brain.process("full analysis", code=code[:200], language=language, auto_validate=True)

    if engine:
        try:
            result = engine.analyze(code, language=language if language != "auto" else None)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error during analysis: {e}"
    else:
        from aura.plugins.compiler.middleware import CompilerMiddleware
        mw = CompilerMiddleware()
        lang = language if language != "auto" else mw.detect_language(code)
        ok, msg = mw.check_syntax(code, lang)
        result = {
            "language": lang,
            "compiler_check": {"valid": ok, "message": msg},
            "available_compilers": list(mw.available_compilers()),
            "note": "No trained model loaded. Train first: gapdet train",
        }
        if brain:
            result["brain_context"] = brain.get_context()
        return json.dumps(result, indent=2)


def get_info(model_path: str) -> str:
    """Show model and system info."""
    from aura.plugins.compiler.middleware import CompilerMiddleware
    mw = CompilerMiddleware()

    info = {
        "system": "GapDet — Offline AI Compiler/Patcher/Translator/Gap-Detector",
        "version": "0.2.0",
        "codename": "David's Brain",
        "available_compilers": list(mw.available_compilers()),
        "model_loaded": False,
    }

    engine = _load_engine(model_path if model_path.strip() else None)
    if engine:
        info["model_loaded"] = True

    brain = _load_brain()
    if brain:
        info["brain"] = brain.get_context()

    return json.dumps(info, indent=2)


LANGUAGES = [
    "auto", "c", "cpp", "python", "rust", "go", "java", "javascript",
    "typescript", "bash", "arduino_cpp", "kotlin", "swift", "ruby",
    "php", "lua", "assembly", "sql", "dockerfile", "yaml", "json",
    "toml", "makefile", "cmake", "perl", "lisp", "zig", "haskell",
    "dart", "terraform", "graphql", "protobuf",
]


def create_ui(model_path: str = "") -> "gradio.Blocks":
    """Create the Gradio UI."""
    gr = _ensure_gradio()

    with gr.Blocks(
        title="GapDet — David's Brain",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown("""
# GapDet — David's Brain
### Offline AI Compiler / Patcher / Translator / Gap Detector
100% offline. No APIs. No cloud. Your code stays on your machine.
        """)

        model_input = gr.Textbox(
            label="Model Path (leave empty for default)",
            value=model_path,
            placeholder="path/to/model.pt (optional)",
        )

        with gr.Tabs():
            # Tab 1: Detect
            with gr.Tab("Detect Gaps"):
                with gr.Row():
                    detect_code = gr.Code(label="Paste your code", language="python", lines=15)
                    detect_lang = gr.Dropdown(LANGUAGES, value="auto", label="Language")
                detect_btn = gr.Button("Detect Gaps", variant="primary")
                detect_out = gr.Code(label="Results", language="json", lines=15)
                detect_btn.click(detect_gaps, [detect_code, detect_lang, model_input], detect_out)

            # Tab 2: Fix
            with gr.Tab("Fix Code"):
                with gr.Row():
                    fix_input = gr.Code(label="Broken code", language="python", lines=15)
                    fix_lang = gr.Dropdown(LANGUAGES, value="auto", label="Language")
                fix_btn = gr.Button("Fix Code", variant="primary")
                fix_out = gr.Code(label="Fixed code", language="json", lines=15)
                fix_btn.click(fix_code, [fix_input, fix_lang, model_input], fix_out)

            # Tab 3: Complete
            with gr.Tab("Complete Code"):
                with gr.Row():
                    comp_input = gr.Code(label="Incomplete code", language="python", lines=15)
                    comp_lang = gr.Dropdown(LANGUAGES, value="auto", label="Language")
                comp_btn = gr.Button("Complete", variant="primary")
                comp_out = gr.Code(label="Completed code", language="json", lines=15)
                comp_btn.click(complete_code, [comp_input, comp_lang, model_input], comp_out)

            # Tab 4: Translate
            with gr.Tab("Translate"):
                with gr.Row():
                    trans_input = gr.Code(label="Source code", language="python", lines=15)
                    with gr.Column():
                        trans_from = gr.Dropdown(LANGUAGES, value="auto", label="From")
                        trans_to = gr.Dropdown(LANGUAGES[1:], value="rust", label="To")
                trans_btn = gr.Button("Translate", variant="primary")
                trans_out = gr.Code(label="Translated code", language="json", lines=15)
                trans_btn.click(translate_code, [trans_input, trans_from, trans_to, model_input], trans_out)

            # Tab 5: Full Analysis
            with gr.Tab("Full Analysis"):
                with gr.Row():
                    anal_input = gr.Code(label="Code to analyze", language="python", lines=15)
                    anal_lang = gr.Dropdown(LANGUAGES, value="auto", label="Language")
                anal_btn = gr.Button("Analyze", variant="primary")
                anal_out = gr.Code(label="Analysis results", language="json", lines=15)
                anal_btn.click(full_analysis, [anal_input, anal_lang, model_input], anal_out)

            # Tab 6: Info
            with gr.Tab("System Info"):
                info_btn = gr.Button("Show Info")
                info_out = gr.Code(label="System Info", language="json", lines=15)
                info_btn.click(get_info, [model_input], info_out)

        gr.Markdown("""
---
*GapDet v0.2.0 "David's Brain" — Built from scratch. No APIs. No cloud. Fully sovereign.*
        """)

    return demo


def launch(model_path: str = "", share: bool = False, port: int = 7860) -> None:
    """Launch the Gradio UI."""
    demo = create_ui(model_path)
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share,
        show_error=True,
    )


if __name__ == "__main__":
    launch()
