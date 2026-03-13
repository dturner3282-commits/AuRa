"""
Offline inference engine for the GapDetector model.

Load a trained model and use it for:
- Code gap detection (find bugs, missing code, vulnerabilities)
- Code patching (fix broken code)
- Code completion (fill in missing parts)
- Cross-language translation

100% offline. No APIs. No internet.

Usage:
    from aura.inference import InferenceEngine

    engine = InferenceEngine("checkpoints/pc_model_final.pt")
    result = engine.detect_gaps("int *p = malloc(10); memcpy(p, src, 10);", language="c")
    result = engine.fix_code("def foo():\\n    pass  # TODO", language="python")
    result = engine.translate("def add(a,b): return a+b", from_lang="python", to_lang="c")
"""

import torch
from typing import Dict, List, Optional
from pathlib import Path

from aura.core.model.architecture import GapDetectorModel
from aura.core.gdt.engine import GapDetectionHead, decode_gap_results, NUM_GAP_CATEGORIES
from aura.core.tokenizer.byte_tokenizer import ByteTokenizer
from aura.plugins.compiler.middleware import CompilerMiddleware


class InferenceEngine:
    """
    Main inference engine. Load a model, pass it code, get results.
    Everything runs locally.
    """

    def __init__(
        self,
        model_path: str,
        device: Optional[str] = None,
    ) -> None:
        """
        Load a trained model from a .pt file.

        Args:
            model_path: path to the saved model checkpoint
            device: "cuda", "cpu", or None for auto-detect
        """
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = ByteTokenizer()
        self.compiler = CompilerMiddleware()

        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        config = checkpoint.get("config", {})
        pc_cfg = config.get("pc_model", {})

        # Build model from saved config
        self.model = GapDetectorModel(
            vocab_size=pc_cfg.get("vocab_size", 512),
            dim=pc_cfg.get("dim", 512),
            encoder_layers=pc_cfg.get("encoder_layers", 8),
            decoder_layers=pc_cfg.get("decoder_layers", 8),
            heads=pc_cfg.get("heads", 8),
            ff_dim=pc_cfg.get("ff_dim", 2048),
            max_seq_len=pc_cfg.get("max_seq_len", 1024),
            dropout=0.0,  # no dropout at inference
        ).to(self.device)

        self.gdt_head = GapDetectionHead(
            dim=pc_cfg.get("dim", 512),
            num_categories=NUM_GAP_CATEGORIES,
        ).to(self.device)

        # Load weights
        self.model.load_state_dict(checkpoint["pc_model"])
        if "gdt_head" in checkpoint:
            self.gdt_head.load_state_dict(checkpoint["gdt_head"])

        self.model.eval()
        self.gdt_head.eval()

        print(f"Model loaded from {model_path}")
        print(f"Parameters: {self.model.count_parameters():,}")
        print(f"Device: {self.device}")

    def detect_gaps(
        self,
        code: str,
        language: Optional[str] = None,
        threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Detect gaps/bugs/vulnerabilities in code.

        Args:
            code: source code string
            language: programming language (auto-detected if None)
            threshold: confidence threshold for gap detection

        Returns:
            List of gap reports with position, category, confidence, severity
        """
        if language is None:
            language = self.compiler.detect_language(code)

        tokens = self.tokenizer.encode(code, language=language)
        max_len = self.model.max_seq_len
        tokens = self.tokenizer.pad_sequence(tokens, max_len)
        src = torch.tensor([tokens], dtype=torch.long, device=self.device)

        with torch.no_grad():
            encoder_out = self.model.encode(src)
            pad_mask = (src != 0)
            gdt_output = self.gdt_head(encoder_out, pad_mask)

        results = decode_gap_results(
            token_gap_probs=gdt_output["token_gap_probs"][0],
            token_gap_categories=gdt_output["token_gap_categories"][0],
            sequence_gaps=gdt_output["sequence_gaps"][0],
            severity=gdt_output["severity"][0],
            threshold=threshold,
        )
        return results

    def fix_code(
        self,
        code: str,
        language: Optional[str] = None,
        max_output_len: int = 512,
        temperature: float = 0.7,
        validate: bool = True,
    ) -> Dict:
        """
        Fix/patch broken code.

        Args:
            code: broken source code
            language: programming language (auto-detected if None)
            max_output_len: maximum output length in tokens
            temperature: generation temperature
            validate: run compiler validation on output

        Returns:
            Dict with fixed_code, gaps_found, compiler_valid, etc.
        """
        if language is None:
            language = self.compiler.detect_language(code)

        # First detect gaps
        gaps = self.detect_gaps(code, language)

        # Encode as patch task: [PATCH_START] broken [PATCH_END] [SEP] -> fixed
        tokens = self.tokenizer.encode_patch(code, "")
        # Remove the empty target - we'll generate it
        sep_idx = tokens.index(self.tokenizer.SEP)
        src_tokens = tokens[:sep_idx + 1]
        src_tokens = self.tokenizer.pad_sequence(src_tokens, self.model.max_seq_len)
        src = torch.tensor([src_tokens], dtype=torch.long, device=self.device)

        # Generate fix
        with torch.no_grad():
            generated = self.model.generate(
                src,
                max_len=max_output_len,
                temperature=temperature,
            )

        fixed_code = self.tokenizer.decode(generated[0].tolist())

        result = {
            "original": code,
            "fixed": fixed_code,
            "language": language,
            "gaps_found": gaps,
        }

        # Compiler validation
        if validate:
            validation = self.compiler.validate_patch(code, fixed_code, language)
            result["validation"] = validation

        return result

    def complete_code(
        self,
        code: str,
        language: Optional[str] = None,
        max_output_len: int = 256,
        temperature: float = 0.7,
    ) -> Dict:
        """
        Complete incomplete code (fill in TODOs, stubs, gaps).

        Args:
            code: incomplete source code
            language: programming language
            max_output_len: maximum output length
            temperature: generation temperature

        Returns:
            Dict with completed code
        """
        if language is None:
            language = self.compiler.detect_language(code)

        tokens = self.tokenizer.encode(code, language=language)
        tokens.append(self.tokenizer.SEP)
        tokens = self.tokenizer.pad_sequence(tokens, self.model.max_seq_len)
        src = torch.tensor([tokens], dtype=torch.long, device=self.device)

        with torch.no_grad():
            generated = self.model.generate(
                src,
                max_len=max_output_len,
                temperature=temperature,
            )

        completed = self.tokenizer.decode(generated[0].tolist())
        return {
            "original": code,
            "completed": completed,
            "language": language,
        }

    def translate(
        self,
        code: str,
        from_lang: str,
        to_lang: str,
        max_output_len: int = 512,
        temperature: float = 0.7,
    ) -> Dict:
        """
        Translate code from one language to another.

        Args:
            code: source code
            from_lang: source language
            to_lang: target language
            max_output_len: maximum output length
            temperature: generation temperature

        Returns:
            Dict with translated code
        """
        tokens = self.tokenizer.encode_pair(code, "", from_lang, to_lang)
        sep_idx = tokens.index(self.tokenizer.SEP)
        src_tokens = tokens[:sep_idx + 1]

        # Add target language marker
        if to_lang in self.tokenizer.LANG_IDS:
            src_tokens.append(self.tokenizer.LANG_MARKER)
            src_tokens.append(self.tokenizer.LANG_IDS[to_lang])

        src_tokens = self.tokenizer.pad_sequence(src_tokens, self.model.max_seq_len)
        src = torch.tensor([src_tokens], dtype=torch.long, device=self.device)

        with torch.no_grad():
            generated = self.model.generate(
                src,
                max_len=max_output_len,
                temperature=temperature,
            )

        translated = self.tokenizer.decode(generated[0].tolist())

        result = {
            "original": code,
            "translated": translated,
            "from_language": from_lang,
            "to_language": to_lang,
        }

        # Validate translation compiles
        is_valid, errors = self.compiler.check_syntax(translated, to_lang)
        result["target_valid"] = is_valid
        result["target_errors"] = errors

        return result

    def analyze(self, code: str, language: Optional[str] = None) -> Dict:
        """
        Full analysis: detect gaps + suggest fixes + compiler validation.
        One-stop command for analyzing any code.
        """
        if language is None:
            language = self.compiler.detect_language(code)

        gaps = self.detect_gaps(code, language)
        fix_result = self.fix_code(code, language, validate=True)
        compiler_check = self.compiler.check_syntax(code, language)

        return {
            "language": language,
            "original_compiles": compiler_check[0],
            "compiler_errors": compiler_check[1],
            "gaps": gaps,
            "suggested_fix": fix_result["fixed"],
            "fix_compiles": fix_result.get("validation", {}).get("patched_valid", None),
        }
