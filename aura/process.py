"""
AuRA Adaptive Processor — The Cognitive Mirror.

Takes any input (file, text, code) and:
1. Auto-detects what it is
2. Presents domain-appropriate options
3. Routes to the right plugin
4. Returns structured results

This is the main interaction loop. Every other capability
(signal decode, code analysis, GDT, etc.) is a plugin it reaches for.

Usage:
    aura process <file>           # auto-detect and show options
    aura process <file> --action <action>  # skip menu, run directly
"""

import os
import json
from typing import Dict, List, Optional, Tuple


# ============================================================
# FILE TYPE DETECTION
# ============================================================

# Extension -> category mapping
FILE_CATEGORIES = {
    # Audio
    '.wav': 'audio', '.mp3': 'audio', '.m4a': 'audio',
    '.ogg': 'audio', '.flac': 'audio', '.aac': 'audio',
    '.wma': 'audio', '.aiff': 'audio', '.opus': 'audio',
    # Code
    '.py': 'code', '.c': 'code', '.cpp': 'code', '.h': 'code',
    '.rs': 'code', '.go': 'code', '.java': 'code',
    '.js': 'code', '.ts': 'code', '.rb': 'code', '.php': 'code',
    '.lua': 'code', '.sh': 'code', '.bash': 'code',
    '.swift': 'code', '.kt': 'code', '.dart': 'code',
    '.zig': 'code', '.hs': 'code', '.ino': 'code',
    # Config
    '.yaml': 'config', '.yml': 'config', '.json': 'config',
    '.toml': 'config', '.xml': 'config', '.ini': 'config',
    '.env': 'config',
    # Text / Document
    '.txt': 'text', '.md': 'text', '.rst': 'text',
    '.csv': 'text', '.tsv': 'text', '.log': 'text',
    # Image
    '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
    '.gif': 'image', '.bmp': 'image', '.svg': 'image',
    '.webp': 'image', '.tiff': 'image',
    # Binary / Data
    '.bin': 'binary', '.dat': 'binary', '.hex': 'binary',
    '.elf': 'binary', '.exe': 'binary',
    # Build / Project
    '.makefile': 'build', '.cmake': 'build',
    'Makefile': 'build', 'CMakeLists.txt': 'build',
    'Dockerfile': 'build',
    # Model / ML
    '.pt': 'model', '.gguf': 'model', '.onnx': 'model',
    '.safetensors': 'model', '.pkl': 'model',
}


def detect_file_type(file_path: str) -> Dict:
    """
    Auto-detect what kind of file this is.

    Returns:
        {
            'category': str (audio, code, config, text, image, binary, model, unknown),
            'extension': str,
            'basename': str,
            'size_bytes': int,
            'language': str or None (for code files),
        }
    """
    basename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # Check by filename for special files
    if basename in ('Makefile', 'CMakeLists.txt', 'Dockerfile', 'Procfile'):
        category = 'build'
    elif basename in ('.env', '.gitignore', '.dockerignore'):
        category = 'config'
    else:
        category = FILE_CATEGORIES.get(ext, 'unknown')

    # Detect programming language for code files
    language = None
    if category == 'code':
        lang_map = {
            '.py': 'python', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
            '.rs': 'rust', '.go': 'go', '.java': 'java',
            '.js': 'javascript', '.ts': 'typescript',
            '.rb': 'ruby', '.php': 'php', '.lua': 'lua',
            '.sh': 'bash', '.bash': 'bash',
            '.swift': 'swift', '.kt': 'kotlin', '.dart': 'dart',
            '.zig': 'zig', '.hs': 'haskell', '.ino': 'arduino_cpp',
        }
        language = lang_map.get(ext)

    size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

    return {
        'category': category,
        'extension': ext,
        'basename': basename,
        'size_bytes': size,
        'language': language,
    }


# ============================================================
# ACTION REGISTRY — what you can do with each file type
# ============================================================

def get_actions_for_category(category: str, language: Optional[str] = None) -> List[Dict]:
    """
    Return available actions for a given file category.
    Each action is a dict with key, label, description, and plugin.
    """
    actions = []

    if category == 'audio':
        actions.extend([
            {
                'key': 'decode',
                'label': 'Decode signal (11-step protocol)',
                'description': 'FFT, alphabet mapping, word matching, ECL scoring',
                'plugin': 'signal',
            },
            {
                'key': 'frequencies',
                'label': 'Extract frequency inventory',
                'description': 'Show all detected frequencies and counts',
                'plugin': 'signal',
            },
            {
                'key': 'spectrogram',
                'label': 'Generate frequency timeline',
                'description': 'Map dominant frequencies across time',
                'plugin': 'signal',
            },
        ])

    if category == 'code':
        actions.extend([
            {
                'key': 'detect',
                'label': 'Detect gaps / bugs',
                'description': 'Find missing error handling, vulnerabilities, etc.',
                'plugin': 'core',
            },
            {
                'key': 'fix',
                'label': 'Fix broken code',
                'description': 'Auto-patch detected issues (requires PyTorch)',
                'plugin': 'core',
            },
            {
                'key': 'complete',
                'label': 'Complete code',
                'description': 'Fill in TODOs, stubs, partial implementations',
                'plugin': 'core',
            },
            {
                'key': 'translate',
                'label': 'Translate to another language',
                'description': 'Cross-language translation (requires PyTorch)',
                'plugin': 'core',
            },
            {
                'key': 'analyze',
                'label': 'Full analysis',
                'description': 'Detect + fix + compiler validation',
                'plugin': 'core',
            },
        ])

    if category == 'config':
        actions.extend([
            {
                'key': 'detect',
                'label': 'Detect issues',
                'description': 'Check for missing fields, syntax problems',
                'plugin': 'core',
            },
            {
                'key': 'analyze',
                'label': 'Analyze structure',
                'description': 'Parse and validate config format',
                'plugin': 'core',
            },
        ])

    if category == 'text':
        actions.extend([
            {
                'key': 'analyze',
                'label': 'Analyze content',
                'description': 'Structure analysis and pattern detection',
                'plugin': 'core',
            },
        ])

    if category == 'image':
        actions.extend([
            {
                'key': 'info',
                'label': 'Show image info',
                'description': 'Dimensions, format, size',
                'plugin': 'builtin',
            },
        ])

    if category == 'binary':
        actions.extend([
            {
                'key': 'hexdump',
                'label': 'Hex dump',
                'description': 'Show raw bytes',
                'plugin': 'builtin',
            },
            {
                'key': 'detect',
                'label': 'Detect patterns',
                'description': 'Look for known signatures and structures',
                'plugin': 'core',
            },
        ])

    if category == 'model':
        actions.extend([
            {
                'key': 'info',
                'label': 'Show model info',
                'description': 'Architecture, size, training step',
                'plugin': 'builtin',
            },
        ])

    # Universal actions available for any file
    actions.append({
        'key': 'info',
        'label': 'Show file info',
        'description': 'Type, size, metadata',
        'plugin': 'builtin',
    })

    # Deduplicate by key (keep first occurrence)
    seen = set()
    unique = []
    for a in actions:
        if a['key'] not in seen:
            seen.add(a['key'])
            unique.append(a)

    return unique


# ============================================================
# ACTION DISPATCHER — route to the right plugin
# ============================================================

def run_action(file_path: str, action_key: str, file_info: Optional[Dict] = None, **kwargs) -> Dict:
    """
    Execute an action on a file by routing to the appropriate plugin.

    Args:
        file_path: path to the input file
        action_key: which action to run
        file_info: pre-computed file type info (optional)
        **kwargs: extra arguments passed to the plugin

    Returns:
        dict with results from the plugin
    """
    if file_info is None:
        file_info = detect_file_type(file_path)

    category = file_info['category']

    # Route to signal plugin for audio files
    if category == 'audio':
        from aura.plugins.signal.processor import run_action as signal_run
        return signal_run(file_path, action_key)

    # Route to core engine for code files
    if category == 'code' and action_key in ('detect', 'fix', 'complete', 'translate', 'analyze'):
        return _run_core_action(file_path, action_key, file_info, **kwargs)

    # Route to core for config/text analysis
    if category in ('config', 'text') and action_key in ('detect', 'analyze'):
        return _run_core_action(file_path, action_key, file_info, **kwargs)

    # Builtin actions
    if action_key == 'info':
        return _file_info(file_path, file_info)

    if action_key == 'hexdump':
        return _hexdump(file_path)

    raise ValueError("No handler for action '%s' on category '%s'" % (action_key, category))


def _run_core_action(file_path: str, action_key: str, file_info: Dict, **kwargs) -> Dict:
    """Route to AuRA's core inference engine."""
    code = open(file_path, 'r').read()
    language = file_info.get('language') or kwargs.get('lang')

    # Try full engine first, fall back to lite
    try:
        import torch
        torch_available = True
    except ImportError:
        torch_available = False

    if torch_available and action_key in ('fix', 'complete', 'translate'):
        from aura.core.inference.engine import InferenceEngine
        model_path = kwargs.get('model')
        if model_path and os.path.exists(model_path):
            engine = InferenceEngine(model_path)
        else:
            # Fall through to lite
            torch_available = False

    if not torch_available or action_key in ('detect', 'analyze'):
        from aura.core.inference.lite_engine import LiteEngine
        engine = LiteEngine()

    if action_key == 'detect':
        return {"results": engine.detect_gaps(code, language=language)}
    elif action_key == 'fix':
        return engine.fix_code(code, language=language)
    elif action_key == 'complete':
        return engine.complete_code(code, language=language)
    elif action_key == 'translate':
        to_lang = kwargs.get('to', 'python')
        return engine.translate(code, from_lang=language, to_lang=to_lang)
    elif action_key == 'analyze':
        return engine.analyze(code, language=language)

    raise ValueError("Unknown core action: %s" % action_key)


def _file_info(file_path: str, file_info: Dict) -> Dict:
    """Return basic file metadata."""
    result = dict(file_info)
    result['path'] = file_path
    result['exists'] = os.path.exists(file_path)
    if result['exists']:
        stat = os.stat(file_path)
        result['size_human'] = _human_size(stat.st_size)
    return result


def _hexdump(file_path: str, max_bytes: int = 256) -> Dict:
    """Return hex dump of first N bytes."""
    with open(file_path, 'rb') as f:
        data = f.read(max_bytes)
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join('%02x' % b for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append('%08x  %-48s  %s' % (i, hex_part, ascii_part))
    return {
        'type': 'hexdump',
        'total_bytes': os.path.getsize(file_path),
        'shown_bytes': len(data),
        'dump': '\n'.join(lines),
    }


def _human_size(size: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return '%.1f %s' % (size, unit)
        size /= 1024
    return '%.1f TB' % size


# ============================================================
# INTERACTIVE MODE — the cognitive mirror prompt
# ============================================================

def interactive_process(file_path: str) -> Dict:
    """
    Interactive mode: detect file, show options, ask user what to do.
    This is the cognitive mirror main loop.

    Returns the result of the chosen action.
    """
    if not os.path.exists(file_path):
        print("File not found: %s" % file_path)
        return {"error": "File not found"}

    file_info = detect_file_type(file_path)
    actions = get_actions_for_category(file_info['category'], file_info.get('language'))

    # Show what we detected
    print()
    print("=" * 60)
    print("  AuRA — Adaptive Processor")
    print("=" * 60)
    print("  File:     %s" % file_info['basename'])
    print("  Type:     %s" % file_info['category'].upper())
    if file_info.get('language'):
        print("  Language: %s" % file_info['language'])
    print("  Size:     %s" % _human_size(file_info['size_bytes']))
    print("=" * 60)
    print()

    if not actions:
        print("  No actions available for this file type.")
        return {"error": "No actions available"}

    # Present options
    print("  What do you want to do?")
    print()
    for i, action in enumerate(actions, 1):
        print("  [%d] %s" % (i, action['label']))
        print("      %s" % action['description'])
        print()

    # Get user choice
    while True:
        try:
            choice = input("  Choose [1-%d]: " % len(actions)).strip()
            if not choice:
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(actions):
                break
            print("  Invalid choice. Try again.")
        except (ValueError, EOFError):
            print("  Invalid input.")
            return {"error": "No selection made"}

    selected = actions[idx]
    print()
    print("  Running: %s..." % selected['label'])
    print()

    # Execute
    result = run_action(file_path, selected['key'], file_info)
    return result
