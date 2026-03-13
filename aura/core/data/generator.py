"""
Synthetic training data generator.

Generates training pairs for:
1. Code completion: code with gaps -> completed code
2. Patch generation: broken code -> fixed code
3. Gap detection: code -> gap labels (position + category)
4. Cross-language translation: code in lang A -> code in lang B

All data is generated locally. No APIs, no internet needed.
Uses 100+ code templates with realistic patterns across 30+ languages.
"""

import random
from typing import List, Dict, Tuple, Optional
from aura.core.tokenizer.byte_tokenizer import ByteTokenizer
from aura.core.data.expanded_templates import (
    EXPANDED_PATCH_TEMPLATES,
    EXPANDED_TRANSLATION_TEMPLATES,
    EXPANDED_COMPLETION_TEMPLATES,
)


# ---------------------------------------------------------------------------
# Code templates by language - realistic patterns with intentional gaps/bugs
# ---------------------------------------------------------------------------

# (broken_code, fixed_code, gap_category, language)
PATCH_TEMPLATES: List[Tuple[str, str, str, str]] = [
    # C - missing null check
    (
        'char *buf = malloc(size);\nmemcpy(buf, src, size);',
        'char *buf = malloc(size);\nif (buf == NULL) return -1;\nmemcpy(buf, src, size);',
        "null_dereference", "c",
    ),
    # C - buffer overflow
    (
        'char buf[64];\nstrcpy(buf, user_input);',
        'char buf[64];\nstrncpy(buf, user_input, sizeof(buf) - 1);\nbuf[sizeof(buf) - 1] = \'\\0\';',
        "buffer_overflow", "c",
    ),
    # C - missing free (resource leak)
    (
        'int *data = malloc(n * sizeof(int));\nprocess(data);\nreturn 0;',
        'int *data = malloc(n * sizeof(int));\nprocess(data);\nfree(data);\nreturn 0;',
        "resource_leak", "c",
    ),
    # C - uninitialized variable
    (
        'int result;\nif (x > 0) result = x * 2;\nreturn result;',
        'int result = 0;\nif (x > 0) result = x * 2;\nreturn result;',
        "uninitialized_variable", "c",
    ),
    # C - missing bounds check
    (
        'int get_element(int *arr, int idx) {\n    return arr[idx];\n}',
        'int get_element(int *arr, int idx, int len) {\n    if (idx < 0 || idx >= len) return -1;\n    return arr[idx];\n}',
        "missing_bounds_check", "c",
    ),
    # Python - missing error handling
    (
        'def read_config(path):\n    f = open(path)\n    data = json.load(f)\n    return data',
        'def read_config(path):\n    try:\n        with open(path) as f:\n            data = json.load(f)\n        return data\n    except (FileNotFoundError, json.JSONDecodeError) as e:\n        logging.error(f"Config error: {e}")\n        return {}',
        "missing_error_handling", "python",
    ),
    # Python - missing import
    (
        'def parse_date(s):\n    return datetime.strptime(s, "%Y-%m-%d")',
        'from datetime import datetime\n\ndef parse_date(s):\n    return datetime.strptime(s, "%Y-%m-%d")',
        "missing_import", "python",
    ),
    # Python - incomplete implementation
    (
        'class DataProcessor:\n    def process(self, data):\n        pass  # TODO: implement',
        'class DataProcessor:\n    def process(self, data):\n        if not data:\n            return []\n        return [self._transform(item) for item in data]\n\n    def _transform(self, item):\n        return item.strip().lower()',
        "incomplete_implementation", "python",
    ),
    # Python - missing return
    (
        'def calculate(x, y, op):\n    if op == "add":\n        return x + y\n    elif op == "sub":\n        return x - y',
        'def calculate(x, y, op):\n    if op == "add":\n        return x + y\n    elif op == "sub":\n        return x - y\n    else:\n        raise ValueError(f"Unknown op: {op}")',
        "missing_return", "python",
    ),
    # Rust - missing error handling
    (
        'fn read_file(path: &str) -> String {\n    std::fs::read_to_string(path).unwrap()\n}',
        'fn read_file(path: &str) -> Result<String, std::io::Error> {\n    std::fs::read_to_string(path)\n}',
        "missing_error_handling", "rust",
    ),
    # JavaScript - missing error handling
    (
        'async function fetchData(url) {\n    const res = await fetch(url);\n    return res.json();\n}',
        'async function fetchData(url) {\n    try {\n        const res = await fetch(url);\n        if (!res.ok) throw new Error(`HTTP ${res.status}`);\n        return await res.json();\n    } catch (err) {\n        console.error("Fetch failed:", err);\n        return null;\n    }\n}',
        "missing_error_handling", "javascript",
    ),
    # Go - missing error check
    (
        'func readFile(path string) []byte {\n    data, _ := os.ReadFile(path)\n    return data\n}',
        'func readFile(path string) ([]byte, error) {\n    data, err := os.ReadFile(path)\n    if err != nil {\n        return nil, fmt.Errorf("read %s: %w", path, err)\n    }\n    return data, nil\n}',
        "missing_error_handling", "go",
    ),
    # Java - resource leak
    (
        'FileInputStream fis = new FileInputStream(file);\nbyte[] data = fis.readAllBytes();\nreturn data;',
        'try (FileInputStream fis = new FileInputStream(file)) {\n    return fis.readAllBytes();\n}',
        "resource_leak", "java",
    ),
    # C++ - missing bounds check
    (
        'int getValue(std::vector<int>& v, int i) {\n    return v[i];\n}',
        'int getValue(std::vector<int>& v, int i) {\n    if (i < 0 || i >= static_cast<int>(v.size())) {\n        throw std::out_of_range("index out of bounds");\n    }\n    return v[i];\n}',
        "missing_bounds_check", "cpp",
    ),
    # Bash - missing error handling
    (
        '#!/bin/bash\ncd $1\nrm -rf build/\nmake',
        '#!/bin/bash\nset -euo pipefail\ncd "$1" || exit 1\nrm -rf build/\nmake',
        "missing_error_handling", "bash",
    ),
    # Arduino/ESP32 - missing null check
    (
        'void setup() {\n    WiFi.begin(ssid, password);\n    Serial.println(WiFi.localIP());\n}',
        'void setup() {\n    WiFi.begin(ssid, password);\n    int retries = 0;\n    while (WiFi.status() != WL_CONNECTED && retries < 20) {\n        delay(500);\n        retries++;\n    }\n    if (WiFi.status() == WL_CONNECTED) {\n        Serial.println(WiFi.localIP());\n    } else {\n        Serial.println("WiFi connection failed");\n    }\n}',
        "missing_error_handling", "arduino_cpp",
    ),
    # SQL - SQL injection vulnerability
    (
        'query = f"SELECT * FROM users WHERE name = \'{username}\'"',
        'query = "SELECT * FROM users WHERE name = ?"\ncursor.execute(query, (username,))',
        "security_vulnerability", "python",
    ),
    # TypeScript - type mismatch
    (
        'function add(a, b) {\n    return a + b;\n}',
        'function add(a: number, b: number): number {\n    return a + b;\n}',
        "type_mismatch", "typescript",
    ),
] + EXPANDED_PATCH_TEMPLATES

# Cross-language translation pairs
TRANSLATION_TEMPLATES: List[Tuple[str, str, str, str]] = [
    # Python -> C
    (
        'def add(a, b):\n    return a + b',
        'int add(int a, int b) {\n    return a + b;\n}',
        "python", "c",
    ),
    # Python -> Rust
    (
        'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)',
        'fn factorial(n: u64) -> u64 {\n    if n <= 1 {\n        return 1;\n    }\n    n * factorial(n - 1)\n}',
        "python", "rust",
    ),
    # Python -> JavaScript
    (
        'def greet(name):\n    return f"Hello, {name}!"',
        'function greet(name) {\n    return `Hello, ${name}!`;\n}',
        "python", "javascript",
    ),
    # C -> Python
    (
        'int max(int a, int b) {\n    return a > b ? a : b;\n}',
        'def max_val(a, b):\n    return a if a > b else b',
        "c", "python",
    ),
    # JavaScript -> Python
    (
        'const arr = [1, 2, 3];\nconst doubled = arr.map(x => x * 2);',
        'arr = [1, 2, 3]\ndoubled = [x * 2 for x in arr]',
        "javascript", "python",
    ),
    # Bash -> Python
    (
        'for f in *.txt; do\n    wc -l "$f"\ndone',
        'import glob\nfor f in glob.glob("*.txt"):\n    with open(f) as fh:\n        print(len(fh.readlines()), f)',
        "bash", "python",
    ),
    # Python -> Go
    (
        'def contains(lst, item):\n    return item in lst',
        'func contains(lst []string, item string) bool {\n    for _, v := range lst {\n        if v == item {\n            return true\n        }\n    }\n    return false\n}',
        "python", "go",
    ),
] + EXPANDED_TRANSLATION_TEMPLATES

# Code completion templates: code with <GAP> -> complete code
COMPLETION_TEMPLATES: List[Tuple[str, str, str]] = [
    (
        'def fibonacci(n):\n    if n <= 1:\n        return n\n    <GAP>',
        'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)',
        "python",
    ),
    (
        '#include <stdio.h>\n\nint main() {\n    <GAP>\n    return 0;\n}',
        '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
        "c",
    ),
    (
        'fn main() {\n    let nums = vec![1, 2, 3, 4, 5];\n    <GAP>\n    println!("{}", sum);\n}',
        'fn main() {\n    let nums = vec![1, 2, 3, 4, 5];\n    let sum: i32 = nums.iter().sum();\n    println!("{}", sum);\n}',
        "rust",
    ),
    (
        'class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, item):\n        <GAP>\n\n    def pop(self):\n        <GAP>',
        'class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, item):\n        self.items.append(item)\n\n    def pop(self):\n        if not self.items:\n            raise IndexError("pop from empty stack")\n        return self.items.pop()',
        "python",
    ),
    (
        'void bubbleSort(int arr[], int n) {\n    <GAP>\n}',
        'void bubbleSort(int arr[], int n) {\n    for (int i = 0; i < n - 1; i++) {\n        for (int j = 0; j < n - i - 1; j++) {\n            if (arr[j] > arr[j + 1]) {\n                int temp = arr[j];\n                arr[j] = arr[j + 1];\n                arr[j + 1] = temp;\n            }\n        }\n    }\n}',
        "c",
    ),
] + EXPANDED_COMPLETION_TEMPLATES


class SyntheticDataGenerator:
    """
    Generates synthetic training data for the gap detection model.

    Creates tokenized training pairs for:
    - Patch training (broken -> fixed)
    - Gap detection (code -> gap labels)
    - Code completion (incomplete -> complete)
    - Cross-language translation (lang A -> lang B)

    All offline, no APIs.
    """

    def __init__(self, seed: int = 42) -> None:
        self.tokenizer = ByteTokenizer()
        self.rng = random.Random(seed)

    def generate_patch_sample(self) -> Dict:
        """Generate a single patch training sample."""
        broken, fixed, category, lang = self.rng.choice(PATCH_TEMPLATES)

        # Add some variation: random whitespace, variable names
        broken = self._add_variation(broken)
        fixed = self._add_variation(fixed)

        src_tokens = self.tokenizer.encode(broken, language=lang)
        tgt_tokens = self.tokenizer.encode(fixed, language=lang)

        return {
            "type": "patch",
            "src_tokens": src_tokens,
            "tgt_tokens": tgt_tokens,
            "language": lang,
            "gap_category": category,
            "src_text": broken,
            "tgt_text": fixed,
        }

    def generate_gap_detection_sample(self) -> Dict:
        """Generate a gap detection training sample with per-token labels."""
        broken, fixed, category, lang = self.rng.choice(PATCH_TEMPLATES)

        tokens = self.tokenizer.encode(broken, language=lang)

        # Create per-token gap labels: simple heuristic -
        # mark tokens that differ between broken and fixed as "gap"
        broken_bytes = broken.encode("utf-8")
        fixed_bytes = fixed.encode("utf-8")

        # Find differing regions
        gap_labels = [0] * len(tokens)  # 0 = no gap

        # Mark all tokens as potentially gapped (simplified)
        # In a real system, you'd do proper diff alignment
        min_len = min(len(broken_bytes), len(fixed_bytes))
        diff_start = min_len
        for i in range(min_len):
            if broken_bytes[i] != fixed_bytes[i]:
                diff_start = i
                break

        # Map byte offset to token offset (accounting for special tokens at start)
        from aura.core.tokenizer.byte_tokenizer import ByteTokenizer
        special_prefix_len = 1  # BOS
        if lang:
            special_prefix_len += 2  # LANG_MARKER + lang_id

        gap_token_start = special_prefix_len + diff_start
        gap_token_end = min(gap_token_start + 10, len(tokens) - 1)

        from aura.core.data.generator import GAP_CATEGORIES_TO_ID
        cat_id = GAP_CATEGORIES_TO_ID.get(category, 0)

        for i in range(gap_token_start, gap_token_end):
            if i < len(gap_labels):
                gap_labels[i] = cat_id

        return {
            "type": "gap_detection",
            "tokens": tokens,
            "gap_labels": gap_labels,
            "language": lang,
            "gap_category": category,
        }

    def generate_completion_sample(self) -> Dict:
        """Generate a code completion training sample."""
        incomplete, complete, lang = self.rng.choice(COMPLETION_TEMPLATES)

        src_tokens = self.tokenizer.encode(
            incomplete.replace("<GAP>", "\x00"),  # Use null byte as gap placeholder
            language=lang,
        )
        tgt_tokens = self.tokenizer.encode(complete, language=lang)

        return {
            "type": "completion",
            "src_tokens": src_tokens,
            "tgt_tokens": tgt_tokens,
            "language": lang,
            "src_text": incomplete,
            "tgt_text": complete,
        }

    def generate_translation_sample(self) -> Dict:
        """Generate a cross-language translation training sample."""
        src_code, tgt_code, src_lang, tgt_lang = self.rng.choice(TRANSLATION_TEMPLATES)

        src_tokens = self.tokenizer.encode(src_code, language=src_lang)
        tgt_tokens = self.tokenizer.encode(tgt_code, language=tgt_lang)

        return {
            "type": "translation",
            "src_tokens": src_tokens,
            "tgt_tokens": tgt_tokens,
            "src_language": src_lang,
            "tgt_language": tgt_lang,
            "src_text": src_code,
            "tgt_text": tgt_code,
        }

    def generate_batch(
        self,
        batch_size: int = 32,
        max_seq_len: int = 512,
        task_weights: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Generate a mixed training batch.

        task_weights: relative weights for each task type.
            Default: {"patch": 0.4, "gap_detection": 0.2, "completion": 0.2, "translation": 0.2}
        """
        import torch

        if task_weights is None:
            task_weights = {
                "patch": 0.4,
                "gap_detection": 0.2,
                "completion": 0.2,
                "translation": 0.2,
            }

        tasks = list(task_weights.keys())
        weights = list(task_weights.values())

        generators = {
            "patch": self.generate_patch_sample,
            "gap_detection": self.generate_gap_detection_sample,
            "completion": self.generate_completion_sample,
            "translation": self.generate_translation_sample,
        }

        src_batch: List[List[int]] = []
        tgt_batch: List[List[int]] = []
        task_types: List[str] = []

        for _ in range(batch_size):
            task = self.rng.choices(tasks, weights=weights, k=1)[0]
            sample = generators[task]()
            task_types.append(task)

            if task == "gap_detection":
                # For gap detection, source = tokens, target = gap labels
                src = self.tokenizer.pad_sequence(sample["tokens"], max_seq_len)
                tgt = sample["gap_labels"]
                tgt = (tgt + [0] * max_seq_len)[:max_seq_len]
            else:
                src = self.tokenizer.pad_sequence(sample["src_tokens"], max_seq_len)
                tgt = self.tokenizer.pad_sequence(sample["tgt_tokens"], max_seq_len)

            src_batch.append(src)
            tgt_batch.append(tgt)

        return {
            "src": torch.tensor(src_batch, dtype=torch.long),
            "tgt": torch.tensor(tgt_batch, dtype=torch.long),
            "task_types": task_types,
        }

    def _add_variation(self, code: str) -> str:
        """Add minor random variations to code for diversity."""
        if self.rng.random() < 0.3:
            code = code.replace("    ", "\t")
        if self.rng.random() < 0.2:
            code = code + "\n"
        return code


# Category name -> ID mapping
GAP_CATEGORIES_TO_ID: Dict[str, int] = {
    "no_gap": 0,
    "missing_error_handling": 1,
    "incomplete_implementation": 2,
    "security_vulnerability": 3,
    "missing_import": 4,
    "type_mismatch": 5,
    "buffer_overflow": 6,
    "null_dereference": 7,
    "resource_leak": 8,
    "race_condition": 9,
    "missing_bounds_check": 10,
    "incomplete_switch": 11,
    "dead_code": 12,
    "missing_return": 13,
    "uninitialized_variable": 14,
    "syntax_error": 15,
}
