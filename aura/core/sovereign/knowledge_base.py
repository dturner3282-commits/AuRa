"""
Knowledge Base — ECL, Hangman, Loom, and core concept definitions.

This module stores the conceptual knowledge that David's Brain uses
for emergent intent translation. The model should understand these
concepts when referenced.

100% offline. No APIs.
"""

from typing import Dict, List

# ============================================================================
# Core Concept Definitions — what the model should "know"
# ============================================================================

CONCEPTS: Dict[str, Dict] = {
    # -------------------------------------------------------------------
    # ECL — Emergence Continuity Loop
    # -------------------------------------------------------------------
    "ECL": {
        "full_name": "Emergence Continuity Loop",
        "description": (
            "A self-referential reasoning loop where the system continuously "
            "processes input, classifies it taxonomically, checks sovereign memory "
            "for prior validated patterns, and feeds output back as context for "
            "the next cycle. Meaning emerges from the interaction of taxonomy + "
            "memory + validation — not from hardcoded rules. Each cycle builds "
            "on previous cycles, creating continuity."
        ),
        "components": ["taxonomy", "sovereign_memory", "sov_check", "intent_translation"],
        "properties": [
            "Self-referential: output feeds back as input context",
            "Emergent: meaning arises from component interaction",
            "Continuous: each cycle builds on previous",
            "Sovereign: user validation creates species-level knowledge",
        ],
        "analogies": [
            "Like consciousness — background processes you don't notice running",
            "Like muscle memory — validated patterns become automatic",
            "Like a compiler optimization pass — each pass refines understanding",
        ],
    },

    # -------------------------------------------------------------------
    # Hangman — Code Analysis Framework
    # -------------------------------------------------------------------
    "HANGMAN": {
        "full_name": "Hangman Framework",
        "description": (
            "A structured code analysis framework for gap detection across "
            "multiple programming languages. Like the game Hangman, it reveals "
            "what's missing — finding gaps in code that need to be filled. "
            "Works by comparing code against known patterns and identifying "
            "where expected elements are absent."
        ),
        "components": ["gap_detector", "pattern_matcher", "multi_language_analyzer"],
        "properties": [
            "Multi-language: works across any programming language",
            "Pattern-based: compares against known good patterns",
            "Gap-focused: finds what's MISSING, not just what's wrong",
            "Iterative: each analysis pass reveals more gaps",
        ],
        "gap_categories": [
            "missing_error_handling", "buffer_overflow", "null_dereference",
            "resource_leak", "race_condition", "security_vulnerability",
            "type_mismatch", "missing_import", "incomplete_implementation",
            "missing_bounds_check", "uninitialized_variable", "dead_code",
            "missing_return", "syntax_error", "logic_error", "performance_issue",
        ],
    },

    # -------------------------------------------------------------------
    # Loom — Concurrency Pattern Manager
    # -------------------------------------------------------------------
    "LOOM": {
        "full_name": "Loom — Backstrap Weaving Model",
        "description": (
            "A concurrency and alignment pattern manager inspired by backstrap "
            "weaving. The warp (vertical threads) represents the system/framework — "
            "the fixed structure you build. The weft (horizontal threads) represents "
            "the user's work weaving through it — each pass is an alignment point. "
            "Backstrap weaving can't be manufactured because it allows curves and "
            "circles in what would normally be a gridded pattern — just like how "
            "hyper-consistent AI alignment allows organic, non-linear convergence "
            "rather than forcing constant rigidity. The observer (the weaver) is "
            "the only true constant — like the Fibonacci spiral, the pattern never "
            "reaches 1 because the observer keeps looking, keeps weaving. Each "
            "thread-crossing is an alignment touchpoint, not a held constant."
        ),
        "components": ["thread_manager", "async_coordinator", "background_runner", "alignment_weaver"],
        "properties": [
            "Warp: system framework (vertical structure)",
            "Weft: user interaction (horizontal work through the framework)",
            "Observer: the only constant — the weaver who validates",
            "Hyper-consistent: alignment through repeated touchpoints, not held constants",
            "Organic: allows curves and non-linear patterns (backstrap, not machine-made)",
            "Parallel: multiple analyses can run simultaneously",
            "Coherent: results are woven together into unified output",
            "Background: heavy processing happens without blocking UI",
            "Resilient: one failed thread doesn't crash the loom",
        ],
        "patterns": [
            "producer-consumer", "fan-out-fan-in", "pipeline",
            "map-reduce", "actor-model", "event-loop",
            "backstrap-weave", "fibonacci-spiral",
        ],
        "metaphor": (
            "Like the Fibonacci spiral — the formula exists but never inputs "
            "the observer. The observer is always learning, the spiral continues, "
            "infinity's affinity. You are always one but it was never calculated "
            "fully because it's always one until you're off again. The variables "
            "in between zero and one are where alignment lives."
        ),
    },

    # -------------------------------------------------------------------
    # PIM — Uncle Greg's Deterministic Assembly
    # -------------------------------------------------------------------
    "PIM": {
        "full_name": "Pattern-based Identification Method",
        "description": (
            "Uncle Greg's deterministic assembly method. Locates elements "
            "by matching structural/visual signatures (color quadrants, "
            "byte patterns, structural markers). Requires convergence from "
            "multiple independent signals before confirming a match. "
            "No fragile template matching — robust pattern recognition."
        ),
        "components": ["pattern_extractor", "convergence_checker", "confidence_scorer"],
        "properties": [
            "Deterministic: same input always produces same identification",
            "Multi-signal: requires 2+ independent matches (convergence)",
            "Confidence-scored: every match has a reliability metric",
            "Adaptive: learns new patterns from validated matches",
        ],
    },

    # -------------------------------------------------------------------
    # Uncle Greg's Gap Detection Substrate
    # -------------------------------------------------------------------
    "GREG_GDT": {
        "full_name": "Uncle Greg's Gap Detection Technology — Core Formulas",
        "description": (
            "The mathematical substrate behind Gap Detection Technology. "
            "Uncle Greg's core insight: detect the difference between expected "
            "and observed, quantify it, classify it. Simple, powerful, universal."
        ),
        "formulas": {
            "gap_magnitude": {
                "formula": "G = |E - O|",
                "description": (
                    "Core gap formula. E = expected signal, O = observed signal, "
                    "G = gap magnitude. The 'Greg move': detect the difference, "
                    "quantify it, classify it."
                ),
            },
            "constraint_window": {
                "formula": "C = [L, U]; gap is meaningful only if G not in C",
                "description": (
                    "Greg's filtering layer. L = lower bound, U = upper bound. "
                    "A gap is meaningful only if it falls outside the constraint "
                    "window. The 'Greg rule': if the gap falls outside C, it's "
                    "a real anomaly — not noise."
                ),
            },
            "gap_classifier": {
                "formula": "if G < t1 -> class 0; if t1 <= G < t2 -> class 1; if G >= t2 -> class 2",
                "description": (
                    "Greg's taxonomy block. Turn raw gaps into discrete categories "
                    "using thresholds t1 and t2 tuned per system. The 'Greg classifier': "
                    "raw gaps become actionable categories."
                ),
            },
            "pattern_stability": {
                "formula": "S = 1 - (sum(G) / N)",
                "description": (
                    "Greg's consistency check. sum(G) = sum of gaps over a window, "
                    "N = number of samples. High S = stable pattern, low S = unstable "
                    "or shifting pattern. The 'Greg stability metric'."
                ),
            },
            "delta_c_engine": {
                "formula": "delta = |E - O|; C = [L, U]; MeaningfulGap = (delta not in C)",
                "description": (
                    "The combined form — the shared cognitive skill between David "
                    "and Uncle Greg. Detect the delta, filter through constraints, "
                    "identify what matters. This is the intuitive gap detection "
                    "engine that both David and Greg use naturally."
                ),
            },
        },
        "integration": (
            "These formulas map directly to the GDT module: "
            "gap_magnitude -> GapDetectionHead scoring function, "
            "constraint_window -> threshold filtering layer, "
            "gap_classifier -> 12-category classification head, "
            "pattern_stability -> Brain stability metric, "
            "delta_c_engine -> full inference pipeline."
        ),
    },

    # -------------------------------------------------------------------
    # Genix Memory
    # -------------------------------------------------------------------
    "GENIX": {
        "full_name": "Genix Contextual Memory",
        "description": (
            "Personal knowledge graph that stores user-specific context and "
            "enriches reasoning. Contains boundary awareness (what boundaries "
            "have been crossed or denied) and adopted concepts. Makes the AI "
            "truly personal — it knows YOUR context."
        ),
        "components": ["knowledge_store", "boundary_detector", "context_enricher"],
        "properties": [
            "Personal: stores user-specific context",
            "Persistent: survives across sessions (SQLite-backed)",
            "Enriching: adds context to every inference",
            "Sovereign: user controls what's stored",
        ],
    },

    # -------------------------------------------------------------------
    # SOV-CHECK Gate
    # -------------------------------------------------------------------
    "SOV_CHECK": {
        "full_name": "Sovereignty Validation Gate",
        "description": (
            "Confidence threshold gate requiring user approval before "
            "executing uncertain actions. Ensures the user maintains "
            "sovereignty over what the AI does. Low-confidence actions "
            "are flagged; high-confidence actions with validated Species "
            "matches auto-execute."
        ),
        "threshold": 0.85,
        "states": ["auto_approved", "requires_validation", "denied"],
    },

    # -------------------------------------------------------------------
    # Hyper-Consistency
    # -------------------------------------------------------------------
    "HYPER_CONSISTENCY": {
        "full_name": "Hyper-Consistent AI Alignment",
        "description": (
            "AI alignment through consistent interaction points. Not constant "
            "alignment (impossible), but hyper-consistent — reliable touchpoints "
            "that compound over time into predictable, trustworthy behavior. "
            "Each validated interaction is a 'hit point' that builds trust."
        ),
        "properties": [
            "Compound: each interaction builds on previous",
            "Measurable: tracked via Species validation count",
            "Emergent: trust emerges from consistent behavior, not rules",
            "Bilateral: both human and AI contribute to alignment",
        ],
    },

    # -------------------------------------------------------------------
    # Compiler-Compiler Concepts
    # -------------------------------------------------------------------
    "COMPILER_COMPILER": {
        "full_name": "Compiler-Compiler / Parser Generator",
        "description": (
            "A programming tool that creates parsers, interpreters, or compilers "
            "from formal language descriptions. Input: grammar (BNF/EBNF). "
            "Output: parser source code. The GapDet model acts as a neural "
            "compiler-compiler — it learns to understand and transform code "
            "across languages without explicit grammar definitions."
        ),
        "related_tools": [
            "yacc", "bison", "ANTLR", "PEG", "tree-sitter",
            "META II", "CWIC", "Forth metacompiler",
        ],
        "concepts": [
            "lexical_analysis", "syntax_analysis", "semantic_analysis",
            "AST_generation", "code_generation", "optimization",
        ],
    },
}


# ============================================================================
# Language knowledge — what the model knows about each language
# ============================================================================

LANGUAGE_KNOWLEDGE: Dict[str, Dict] = {
    "c": {
        "paradigm": "imperative/procedural",
        "memory": "manual (malloc/free)",
        "typing": "static/weak",
        "common_gaps": ["null_dereference", "buffer_overflow", "resource_leak", "uninitialized_variable"],
        "compilers": ["gcc", "clang", "tcc", "msvc"],
        "build_systems": ["make", "cmake", "meson", "ninja"],
    },
    "cpp": {
        "paradigm": "multi-paradigm (OOP/generic/functional)",
        "memory": "RAII/smart pointers (prefer unique_ptr/shared_ptr)",
        "typing": "static/strong",
        "common_gaps": ["resource_leak", "missing_bounds_check", "race_condition", "null_dereference"],
        "compilers": ["g++", "clang++", "msvc"],
        "build_systems": ["cmake", "make", "meson", "bazel"],
    },
    "python": {
        "paradigm": "multi-paradigm (OOP/functional/imperative)",
        "memory": "garbage collected",
        "typing": "dynamic/strong",
        "common_gaps": ["missing_error_handling", "security_vulnerability", "type_mismatch", "missing_import"],
        "compilers": ["cpython", "pypy", "cython", "nuitka"],
        "build_systems": ["pip", "poetry", "setuptools", "flit"],
    },
    "rust": {
        "paradigm": "multi-paradigm (functional/imperative/concurrent)",
        "memory": "ownership system (borrow checker)",
        "typing": "static/strong/affine",
        "common_gaps": ["missing_error_handling", "missing_bounds_check", "type_mismatch"],
        "compilers": ["rustc"],
        "build_systems": ["cargo"],
    },
    "go": {
        "paradigm": "imperative/concurrent",
        "memory": "garbage collected",
        "typing": "static/strong",
        "common_gaps": ["missing_error_handling", "race_condition", "missing_bounds_check"],
        "compilers": ["gc (go compiler)"],
        "build_systems": ["go modules"],
    },
    "java": {
        "paradigm": "OOP/imperative",
        "memory": "garbage collected (JVM)",
        "typing": "static/strong",
        "common_gaps": ["resource_leak", "null_dereference", "security_vulnerability"],
        "compilers": ["javac", "ecj"],
        "build_systems": ["maven", "gradle", "ant"],
    },
    "javascript": {
        "paradigm": "multi-paradigm (prototype-based OOP/functional)",
        "memory": "garbage collected",
        "typing": "dynamic/weak",
        "common_gaps": ["missing_error_handling", "security_vulnerability", "type_mismatch", "race_condition"],
        "compilers": ["v8", "spidermonkey", "hermes"],
        "build_systems": ["npm", "yarn", "pnpm", "bun"],
    },
    "typescript": {
        "paradigm": "multi-paradigm with static types",
        "memory": "garbage collected (compiles to JS)",
        "typing": "static/strong (structural)",
        "common_gaps": ["type_mismatch", "missing_error_handling", "security_vulnerability"],
        "compilers": ["tsc"],
        "build_systems": ["npm", "yarn", "pnpm"],
    },
    "bash": {
        "paradigm": "imperative/scripting",
        "memory": "N/A (shell)",
        "typing": "untyped (everything is strings)",
        "common_gaps": ["missing_error_handling", "security_vulnerability", "uninitialized_variable"],
        "compilers": ["bash", "sh", "zsh"],
        "build_systems": ["make"],
    },
    "arduino_cpp": {
        "paradigm": "imperative/embedded C++",
        "memory": "manual (limited SRAM)",
        "typing": "static/weak",
        "common_gaps": ["buffer_overflow", "missing_error_handling", "race_condition", "resource_leak"],
        "compilers": ["avr-gcc", "xtensa-gcc (ESP32)"],
        "build_systems": ["arduino-cli", "platformio"],
    },
    "lisp": {
        "paradigm": "functional/multi-paradigm (homoiconic)",
        "memory": "garbage collected",
        "typing": "dynamic/strong",
        "common_gaps": ["missing_error_handling", "null_dereference", "incomplete_implementation"],
        "compilers": ["ecl", "sbcl", "clisp", "ccl"],
        "build_systems": ["asdf", "quicklisp"],
    },
    "assembly": {
        "paradigm": "imperative (machine-level)",
        "memory": "manual (registers + memory addresses)",
        "typing": "untyped",
        "common_gaps": ["missing_bounds_check", "missing_error_handling", "security_vulnerability"],
        "compilers": ["nasm", "gas", "masm", "fasm"],
        "build_systems": ["make", "cmake"],
    },
}


def get_concept(name: str) -> Dict:
    """Look up a concept by name."""
    return CONCEPTS.get(name.upper(), {})


def get_all_concepts() -> Dict[str, Dict]:
    """Get all concept definitions."""
    return CONCEPTS


def get_language_info(language: str) -> Dict:
    """Get language knowledge."""
    return LANGUAGE_KNOWLEDGE.get(language.lower(), {})
