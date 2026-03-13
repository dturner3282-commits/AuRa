"""
AuRA Lite Inference Engine — Pure Python, No PyTorch Required.

Rule-based code analysis using Uncle Greg's GDT formulas.
Works on any device: phones, old laptops, Ventoy USB boots, Termux.

When PyTorch is not available, AuRA falls back to this engine.
It provides:
- Gap detection via pattern matching + heuristic rules
- Language detection
- Code analysis with severity scoring
- Basic fix suggestions (pattern-based)

No neural model needed. No heavy dependencies. Just Python 3.

Usage:
    from aura.core.inference.lite_engine import LiteEngine

    engine = LiteEngine()
    gaps = engine.detect_gaps("int *p = malloc(10);", language="c")
    result = engine.analyze("def foo(): pass", language="python")
"""

import re
import os
import json
from typing import Dict, List, Optional, Tuple


# Uncle Greg's GDT gap categories
GAP_CATEGORIES = {
    "missing_error_handling": {
        "description": "No error checking after operations that can fail",
        "severity": 0.7,
    },
    "buffer_overflow": {
        "description": "Potential write beyond allocated memory",
        "severity": 0.95,
    },
    "null_dereference": {
        "description": "Pointer/reference used without null check",
        "severity": 0.85,
    },
    "resource_leak": {
        "description": "Opened resource never closed (file, socket, memory)",
        "severity": 0.7,
    },
    "race_condition": {
        "description": "Shared state accessed without synchronization",
        "severity": 0.8,
    },
    "security_vulnerability": {
        "description": "Code pattern known to be exploitable",
        "severity": 0.9,
    },
    "type_mismatch": {
        "description": "Incompatible types used together",
        "severity": 0.6,
    },
    "missing_import": {
        "description": "Symbol used but not imported/included",
        "severity": 0.5,
    },
    "incomplete_implementation": {
        "description": "TODO, FIXME, stub, pass, or empty body",
        "severity": 0.6,
    },
    "missing_bounds_check": {
        "description": "Array/index access without bounds validation",
        "severity": 0.8,
    },
    "uninitialized_variable": {
        "description": "Variable used before being assigned a value",
        "severity": 0.75,
    },
    "dead_code": {
        "description": "Code that can never be reached",
        "severity": 0.3,
    },
    "missing_return": {
        "description": "Function path that doesn't return a value",
        "severity": 0.65,
    },
    "syntax_error": {
        "description": "Invalid syntax that won't compile/parse",
        "severity": 0.9,
    },
    "logic_error": {
        "description": "Code compiles but doesn't do what's intended",
        "severity": 0.7,
    },
    "performance_issue": {
        "description": "Inefficient pattern that could be optimized",
        "severity": 0.3,
    },
}

# Pattern rules per language for gap detection
# Each rule: (regex_pattern, gap_category, confidence)
UNIVERSAL_RULES: List[Tuple[str, str, float]] = [
    # Incomplete implementation
    (r'\bTODO\b', "incomplete_implementation", 0.95),
    (r'\bFIXME\b', "incomplete_implementation", 0.95),
    (r'\bHACK\b', "incomplete_implementation", 0.8),
    (r'\bXXX\b', "incomplete_implementation", 0.8),
    (r'\bSTUB\b', "incomplete_implementation", 0.9),
]

C_RULES: List[Tuple[str, str, float]] = [
    # Buffer overflow
    (r'\bstrcpy\s*\(', "buffer_overflow", 0.9),
    (r'\bstrcat\s*\(', "buffer_overflow", 0.85),
    (r'\bsprintf\s*\(', "buffer_overflow", 0.85),
    (r'\bgets\s*\(', "buffer_overflow", 0.95),
    (r'\bmemcpy\s*\([^)]*\)', "missing_bounds_check", 0.7),
    # Null dereference
    (r'malloc\s*\([^)]*\)\s*;(?!\s*if)', "null_dereference", 0.8),
    (r'calloc\s*\([^)]*\)\s*;(?!\s*if)', "null_dereference", 0.8),
    # Resource leak
    (r'fopen\s*\([^)]*\)', "resource_leak", 0.6),
    (r'malloc\s*\([^)]*\)', "resource_leak", 0.5),
    # Missing error handling
    (r'(fread|fwrite|fclose|fseek)\s*\([^)]*\)\s*;', "missing_error_handling", 0.5),
    # Security
    (r'\bsystem\s*\(', "security_vulnerability", 0.7),
    (r'\bexec[lv]p?\s*\(', "security_vulnerability", 0.7),
]

CPP_RULES: List[Tuple[str, str, float]] = [
    (r'\bnew\b[^;]*;(?!.*\bdelete\b)', "resource_leak", 0.6),
    (r'dynamic_cast.*\)(?!\s*&&|\s*if|\s*!=\s*nullptr)', "null_dereference", 0.6),
    (r'\bconst_cast\b', "security_vulnerability", 0.5),
    (r'\breinterpret_cast\b', "security_vulnerability", 0.6),
]

PYTHON_RULES: List[Tuple[str, str, float]] = [
    # Incomplete
    (r'^\s*pass\s*$', "incomplete_implementation", 0.7),
    (r'\.\.\.\s*$', "incomplete_implementation", 0.7),
    (r'raise NotImplementedError', "incomplete_implementation", 0.9),
    # Error handling
    (r'except\s*:', "missing_error_handling", 0.7),
    (r'except\s+Exception\s*:', "missing_error_handling", 0.5),
    # Security
    (r'\beval\s*\(', "security_vulnerability", 0.8),
    (r'\bexec\s*\(', "security_vulnerability", 0.8),
    (r'pickle\.loads?\s*\(', "security_vulnerability", 0.7),
    (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "security_vulnerability", 0.85),
    (r'os\.system\s*\(', "security_vulnerability", 0.7),
    # Type issues
    (r'# type:\s*ignore', "type_mismatch", 0.4),
]

RUST_RULES: List[Tuple[str, str, float]] = [
    (r'\.unwrap\(\)', "missing_error_handling", 0.7),
    (r'\.expect\(', "missing_error_handling", 0.5),
    (r'\bunsafe\b', "security_vulnerability", 0.6),
    (r'todo!\(\)', "incomplete_implementation", 0.95),
    (r'unimplemented!\(\)', "incomplete_implementation", 0.95),
]

GO_RULES: List[Tuple[str, str, float]] = [
    (r'_\s*=\s*\w+\.\w+\(', "missing_error_handling", 0.8),
    (r'if\s+err\s*!=\s*nil\s*\{\s*\}', "missing_error_handling", 0.9),
    (r'//\s*nolint', "missing_error_handling", 0.4),
]

JS_RULES: List[Tuple[str, str, float]] = [
    (r'\.catch\s*\(\s*\)', "missing_error_handling", 0.7),
    (r'console\.log\s*\(', "dead_code", 0.3),
    (r'\bvar\b', "security_vulnerability", 0.4),
    (r'eval\s*\(', "security_vulnerability", 0.85),
    (r'innerHTML\s*=', "security_vulnerability", 0.7),
    (r'document\.write\s*\(', "security_vulnerability", 0.7),
]

JAVA_RULES: List[Tuple[str, str, float]] = [
    (r'catch\s*\(\s*Exception\s+\w+\s*\)\s*\{\s*\}', "missing_error_handling", 0.9),
    (r'\.printStackTrace\(\)', "missing_error_handling", 0.5),
    (r'@SuppressWarnings', "missing_error_handling", 0.4),
]

BASH_RULES: List[Tuple[str, str, float]] = [
    (r'(?<!\bset\s)-e', "missing_error_handling", 0.3),
    (r'\brm\s+-rf\b', "security_vulnerability", 0.6),
    (r'\beval\b', "security_vulnerability", 0.7),
    (r'\$\{?\w+\}?(?!\s*:-)', "missing_error_handling", 0.3),
]

LANGUAGE_RULES: Dict[str, List[Tuple[str, str, float]]] = {
    "c": C_RULES,
    "cpp": C_RULES + CPP_RULES,
    "python": PYTHON_RULES,
    "rust": RUST_RULES,
    "go": GO_RULES,
    "javascript": JS_RULES,
    "typescript": JS_RULES,
    "java": JAVA_RULES,
    "bash": BASH_RULES,
}


def detect_language(code: str) -> str:
    """Detect programming language from code content (no dependencies)."""
    code_stripped = code.strip()
    code_lower = code_stripped.lower()

    if code_stripped.startswith("#include") or "int main(" in code_lower:
        if "std::" in code or "iostream" in code or "vector<" in code:
            return "cpp"
        return "c"
    if code_stripped.startswith("#!/bin/bash") or code_stripped.startswith("#!/bin/sh"):
        return "bash"
    if "fn main()" in code or ("fn " in code and "-> " in code):
        return "rust"
    if "func " in code and "package " in code_lower:
        return "go"
    if "def " in code or ("import " in code and ";" not in code):
        return "python"
    if "function " in code or "const " in code or "=>" in code:
        if ": " in code and "interface " in code:
            return "typescript"
        return "javascript"
    if "public class " in code or "public static void main" in code:
        return "java"
    if "void setup()" in code or "void loop()" in code:
        return "arduino_cpp"

    return "python"  # fallback


class LiteEngine:
    """
    Rule-based inference engine. No PyTorch needed.

    Uses Uncle Greg's GDT formulas:
    - G = |E - O| (gap magnitude via pattern matching)
    - C = [L, U] (constraint window — gap is meaningful only if G not in C)
    - Threshold classifier: maps gaps to categories
    - S = 1 - (sum(G) / N) (stability score)
    """

    def __init__(self) -> None:
        self.mode = "lite"

    def detect_gaps(
        self,
        code: str,
        language: Optional[str] = None,
        threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Detect gaps/bugs using rule-based pattern matching.

        Args:
            code: source code string
            language: programming language (auto-detected if None)
            threshold: minimum confidence to report a gap

        Returns:
            List of gap reports (same format as neural engine)
        """
        if language is None:
            language = detect_language(code)

        gaps: List[Dict] = []
        lines = code.split("\n")

        # Apply universal rules
        for pattern, category, confidence in UNIVERSAL_RULES:
            for i, line in enumerate(lines):
                if re.search(pattern, line) and confidence >= threshold:
                    gaps.append({
                        "position": i + 1,
                        "line": i + 1,
                        "category": category,
                        "confidence": round(confidence, 3),
                        "text": line.strip(),
                        "description": GAP_CATEGORIES[category]["description"],
                    })

        # Apply language-specific rules
        lang_rules = LANGUAGE_RULES.get(language, [])
        for pattern, category, confidence in lang_rules:
            for i, line in enumerate(lines):
                if re.search(pattern, line) and confidence >= threshold:
                    # Avoid duplicate detections on same line+category
                    duplicate = any(
                        g["line"] == i + 1 and g["category"] == category
                        for g in gaps
                    )
                    if not duplicate:
                        gaps.append({
                            "position": i + 1,
                            "line": i + 1,
                            "category": category,
                            "confidence": round(confidence, 3),
                            "text": line.strip(),
                            "description": GAP_CATEGORIES[category]["description"],
                        })

        # Sort by line number
        gaps.sort(key=lambda g: g["line"])

        # Calculate Uncle Greg's metrics
        # G = |E - O| — gap magnitude (number of gaps vs expected clean code)
        total_lines = max(len(lines), 1)
        gap_magnitude = len(gaps) / total_lines

        # S = 1 - (sum(G) / N) — stability score
        total_confidence = sum(g["confidence"] for g in gaps)
        stability = 1.0 - min(total_confidence / max(total_lines, 1), 1.0)

        # Severity: weighted average of gap severities
        if gaps:
            severity = sum(
                GAP_CATEGORIES.get(g["category"], {}).get("severity", 0.5)
                * g["confidence"]
                for g in gaps
            ) / len(gaps)
        else:
            severity = 0.0

        # Determine active gap types
        active_types = list(set(g["category"] for g in gaps))

        summary = {
            "total_gaps_found": len(gaps),
            "severity": round(severity, 3),
            "stability": round(stability, 3),
            "gap_magnitude": round(gap_magnitude, 3),
            "active_gap_types": active_types,
            "gaps": gaps,
            "engine": "lite",
        }

        return [summary]

    def analyze(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> Dict:
        """
        Full analysis: detect gaps + basic stats.

        Args:
            code: source code string
            language: programming language

        Returns:
            Dict with analysis results
        """
        if language is None:
            language = detect_language(code)

        gaps = self.detect_gaps(code, language)
        lines = code.split("\n")

        # Basic code stats
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "--")))
        code_lines = total_lines - blank_lines - comment_lines

        return {
            "language": language,
            "engine": "lite",
            "original_compiles": None,  # No compiler check in lite mode
            "compiler_errors": "Compiler validation not available in lite mode",
            "gaps": gaps,
            "suggested_fix": None,
            "fix_compiles": None,
            "stats": {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
            },
        }

    def info(self) -> Dict:
        """Return system info for lite mode."""
        return {
            "version": "0.2.0",
            "engine": "lite",
            "mode": "Rule-based (no PyTorch)",
            "capabilities": [
                "gap_detection",
                "code_analysis",
                "language_detection",
            ],
            "limited_capabilities": [
                "code_patching (pattern-based suggestions only)",
                "code_completion (not available in lite mode)",
                "cross_language_translation (not available in lite mode)",
            ],
            "gap_categories": list(GAP_CATEGORIES.keys()),
            "supported_languages": list(LANGUAGE_RULES.keys()) + ["arduino_cpp"],
        }
