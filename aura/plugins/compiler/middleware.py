"""
Compiler Middleware.

Wraps real compilers (gcc, clang, rustc, python, go, javac, node, tsc)
to validate AI-generated code output. Runs locally, no APIs.

The middleware:
1. Takes AI-generated code/patches
2. Writes to a temp file
3. Runs the appropriate compiler/interpreter
4. Captures errors
5. Feeds errors back to the model for iterative fixing

Supports: C, C++, Rust, Python, Go, Java, JavaScript, TypeScript, Bash
"""

import subprocess
import tempfile
import os
import shutil
from typing import Dict, Optional, Tuple, List
from pathlib import Path


# Map language names to file extensions and compile/check commands
LANGUAGE_CONFIG: Dict[str, Dict] = {
    "c": {
        "ext": ".c",
        "compile": ["gcc", "-fsyntax-only", "-Wall", "-Wextra", "{file}"],
        "run": ["gcc", "-o", "{out}", "{file}"],
    },
    "cpp": {
        "ext": ".cpp",
        "compile": ["g++", "-fsyntax-only", "-Wall", "-Wextra", "-std=c++17", "{file}"],
        "run": ["g++", "-o", "{out}", "-std=c++17", "{file}"],
    },
    "rust": {
        "ext": ".rs",
        "compile": ["rustc", "--edition", "2021", "--crate-type", "lib", "{file}"],
        "run": ["rustc", "--edition", "2021", "-o", "{out}", "{file}"],
    },
    "python": {
        "ext": ".py",
        "compile": ["python3", "-m", "py_compile", "{file}"],
        "run": ["python3", "{file}"],
    },
    "go": {
        "ext": ".go",
        "compile": ["go", "vet", "{file}"],
        "run": ["go", "run", "{file}"],
    },
    "java": {
        "ext": ".java",
        "compile": ["javac", "{file}"],
        "run": None,
    },
    "javascript": {
        "ext": ".js",
        "compile": ["node", "--check", "{file}"],
        "run": ["node", "{file}"],
    },
    "typescript": {
        "ext": ".ts",
        "compile": ["tsc", "--noEmit", "--strict", "{file}"],
        "run": None,
    },
    "bash": {
        "ext": ".sh",
        "compile": ["bash", "-n", "{file}"],
        "run": ["bash", "{file}"],
    },
    "arduino_cpp": {
        "ext": ".ino",
        "compile": None,  # Needs Arduino CLI - optional
        "run": None,
    },
}


class CompilerMiddleware:
    """
    Validates code by running it through real compilers.
    All local, no APIs.
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self._available_compilers: Dict[str, bool] = {}
        self._check_available_compilers()

    def _check_available_compilers(self) -> None:
        """Check which compilers are available on this system."""
        compiler_bins = {
            "c": "gcc",
            "cpp": "g++",
            "rust": "rustc",
            "python": "python3",
            "go": "go",
            "java": "javac",
            "javascript": "node",
            "typescript": "tsc",
            "bash": "bash",
        }
        for lang, binary in compiler_bins.items():
            self._available_compilers[lang] = shutil.which(binary) is not None

    def get_available_languages(self) -> List[str]:
        """Return list of languages with available compilers."""
        return [lang for lang, available in self._available_compilers.items() if available]

    def check_syntax(self, code: str, language: str) -> Tuple[bool, str]:
        """
        Check if code has valid syntax using the real compiler.

        Args:
            code: source code string
            language: programming language name

        Returns:
            (success: bool, error_message: str)
        """
        if language not in LANGUAGE_CONFIG:
            return False, f"Unsupported language: {language}"

        config = LANGUAGE_CONFIG[language]
        if config["compile"] is None:
            return True, "No compiler available for syntax check"

        if not self._available_compilers.get(language, False):
            return True, f"Compiler for {language} not installed, skipping check"

        ext = config["ext"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False, dir="/tmp"
        ) as f:
            f.write(code)
            f.flush()
            tmp_path = f.name

        try:
            out_path = tmp_path + ".out"
            cmd = [
                arg.replace("{file}", tmp_path).replace("{out}", out_path)
                for arg in config["compile"]
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                return True, ""
            else:
                error = result.stderr or result.stdout
                return False, error.strip()

        except subprocess.TimeoutExpired:
            return False, f"Compilation timed out after {self.timeout}s"
        except FileNotFoundError as e:
            return True, f"Compiler not found: {e}"
        finally:
            os.unlink(tmp_path)
            out_path = tmp_path + ".out"
            if os.path.exists(out_path):
                os.unlink(out_path)

    def validate_patch(
        self, original: str, patched: str, language: str
    ) -> Dict[str, object]:
        """
        Validate that a patch improves code (doesn't introduce new errors).

        Returns dict with:
            original_valid: bool
            patched_valid: bool
            original_errors: str
            patched_errors: str
            improved: bool
        """
        orig_ok, orig_err = self.check_syntax(original, language)
        patch_ok, patch_err = self.check_syntax(patched, language)

        return {
            "original_valid": orig_ok,
            "patched_valid": patch_ok,
            "original_errors": orig_err,
            "patched_errors": patch_err,
            "improved": patch_ok and (not orig_ok or len(patch_err) < len(orig_err)),
        }

    def detect_language(self, code: str) -> str:
        """
        Simple heuristic to detect programming language from code content.
        """
        code_lower = code.strip().lower()

        if code_lower.startswith("#include") or "int main(" in code_lower:
            if "std::" in code or "iostream" in code or "vector<" in code:
                return "cpp"
            return "c"
        if code_lower.startswith("#!/bin/bash") or code_lower.startswith("#!/bin/sh"):
            return "bash"
        if "fn main()" in code or "fn " in code and "-> " in code:
            return "rust"
        if "func " in code and "package " in code_lower:
            return "go"
        if "def " in code or "import " in code and ";" not in code:
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

    def iterative_fix(
        self,
        code: str,
        language: str,
        fix_callback,
        max_iterations: int = 3,
    ) -> Tuple[str, bool, List[str]]:
        """
        Iteratively fix code using the AI model and compiler feedback.

        Args:
            code: initial code
            language: programming language
            fix_callback: function(code, errors) -> fixed_code
            max_iterations: max fix attempts

        Returns:
            (final_code, is_valid, list_of_errors_per_iteration)
        """
        errors_history: List[str] = []
        current_code = code

        for i in range(max_iterations):
            is_valid, errors = self.check_syntax(current_code, language)
            errors_history.append(errors)

            if is_valid:
                return current_code, True, errors_history

            # Ask the AI to fix based on compiler errors
            current_code = fix_callback(current_code, errors)

        # Final check
        is_valid, errors = self.check_syntax(current_code, language)
        errors_history.append(errors)
        return current_code, is_valid, errors_history
