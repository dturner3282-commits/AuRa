"""
Byte-level tokenizer for the universal compiler/translator/AI/GDT system.

Works at the raw byte level so it can handle ANY language, binary format,
config file, patch, or data format. No external dependencies.

Every byte (0-255) is a token. Special tokens (256+) mark structure:
- BOS/EOS: sequence boundaries
- SEP: separates input from expected output
- GAP: marks where the model should fill in code
- PATCH_START/END: marks patch regions
- LANG_MARKER: followed by language ID byte
- ERR_MARKER: marks detected errors/gaps
"""

from typing import List, Optional, Dict


class ByteTokenizer:
    """Byte-level tokenizer that handles any input format."""

    # Special token IDs
    PAD = 0
    BOS = 256
    EOS = 257
    SEP = 258
    GAP = 259
    PATCH_START = 260
    PATCH_END = 261
    LANG_MARKER = 262
    ERR_MARKER = 263

    # Language IDs (used after LANG_MARKER token)
    LANG_IDS: Dict[str, int] = {
        "c": 1, "cpp": 2, "python": 3, "rust": 4, "go": 5,
        "java": 6, "javascript": 7, "typescript": 8, "bash": 9,
        "assembly_x86": 10, "assembly_arm": 11, "arduino_cpp": 12,
        "kotlin": 13, "swift": 14, "ruby": 15, "lua": 16,
        "html": 17, "css": 18, "json": 19, "yaml": 20,
        "toml": 21, "xml": 22, "sql": 23, "makefile": 24,
        "cmake": 25, "diff": 26, "binary": 27, "ini": 28,
        "powershell": 29, "perl": 30, "php": 31, "dart": 32,
        "zig": 33, "llvm_ir": 34, "micropython": 35, "esp_idf": 36,
    }

    VOCAB_SIZE = 512  # 256 bytes + special tokens + room to grow

    def __init__(self) -> None:
        self.vocab_size = self.VOCAB_SIZE

    def encode(
        self,
        text: str,
        add_bos: bool = True,
        add_eos: bool = True,
        language: Optional[str] = None,
    ) -> List[int]:
        """Encode text to byte-level token IDs."""
        tokens: List[int] = []

        if add_bos:
            tokens.append(self.BOS)

        if language and language in self.LANG_IDS:
            tokens.append(self.LANG_MARKER)
            tokens.append(self.LANG_IDS[language])

        raw_bytes = text.encode("utf-8", errors="replace")
        tokens.extend(int(b) for b in raw_bytes)

        if add_eos:
            tokens.append(self.EOS)

        return tokens

    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs back to text."""
        raw_bytes: List[int] = []
        skip_next = False

        for tid in token_ids:
            if skip_next:
                skip_next = False
                continue
            if tid == self.LANG_MARKER:
                skip_next = True
                continue
            if tid in (self.PAD, self.BOS, self.EOS, self.SEP,
                       self.GAP, self.PATCH_START, self.PATCH_END,
                       self.ERR_MARKER):
                continue
            if 1 <= tid <= 255:
                raw_bytes.append(tid)

        return bytes(raw_bytes).decode("utf-8", errors="replace")

    def encode_pair(
        self,
        source: str,
        target: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> List[int]:
        """Encode an input/output pair with SEP token between them.

        Used for training translation, patching, and completion tasks.
        Format: [BOS] [LANG src] <source bytes> [SEP] [LANG tgt] <target bytes> [EOS]
        """
        tokens: List[int] = [self.BOS]

        if source_lang and source_lang in self.LANG_IDS:
            tokens.append(self.LANG_MARKER)
            tokens.append(self.LANG_IDS[source_lang])

        tokens.extend(int(b) for b in source.encode("utf-8", errors="replace"))

        tokens.append(self.SEP)

        if target_lang and target_lang in self.LANG_IDS:
            tokens.append(self.LANG_MARKER)
            tokens.append(self.LANG_IDS[target_lang])

        tokens.extend(int(b) for b in target.encode("utf-8", errors="replace"))

        tokens.append(self.EOS)
        return tokens

    def encode_with_gaps(self, text: str, gap_positions: List[tuple]) -> List[int]:
        """Encode text with GAP markers at specified byte positions.

        gap_positions: list of (start, end) byte offsets to mark as gaps.
        """
        raw_bytes = text.encode("utf-8", errors="replace")
        tokens: List[int] = [self.BOS]
        i = 0

        for start, end in sorted(gap_positions):
            tokens.extend(int(b) for b in raw_bytes[i:start])
            tokens.append(self.GAP)
            i = end

        tokens.extend(int(b) for b in raw_bytes[i:])
        tokens.append(self.EOS)
        return tokens

    def encode_patch(self, original: str, patched: str) -> List[int]:
        """Encode original code + patched version for patch training.

        Format: [BOS] [PATCH_START] <original> [PATCH_END] [SEP] <patched> [EOS]
        """
        tokens: List[int] = [self.BOS, self.PATCH_START]
        tokens.extend(int(b) for b in original.encode("utf-8", errors="replace"))
        tokens.append(self.PATCH_END)
        tokens.append(self.SEP)
        tokens.extend(int(b) for b in patched.encode("utf-8", errors="replace"))
        tokens.append(self.EOS)
        return tokens

    def pad_sequence(self, tokens: List[int], max_len: int) -> List[int]:
        """Pad or truncate a token sequence to max_len."""
        if len(tokens) >= max_len:
            return tokens[:max_len]
        return tokens + [self.PAD] * (max_len - len(tokens))

    def get_special_token_name(self, tid: int) -> Optional[str]:
        """Get human-readable name for a special token."""
        names = {
            self.PAD: "<PAD>", self.BOS: "<BOS>", self.EOS: "<EOS>",
            self.SEP: "<SEP>", self.GAP: "<GAP>",
            self.PATCH_START: "<PATCH_START>", self.PATCH_END: "<PATCH_END>",
            self.LANG_MARKER: "<LANG>", self.ERR_MARKER: "<ERR>",
        }
        return names.get(tid)
