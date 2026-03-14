"""
Signal Processing Adapter for the AuRA process pipeline.

Handles audio file detection and provides signal decode capabilities
as one of AuRA's peripheral sensory modules.
"""

import os

# Audio extensions this plugin can handle
AUDIO_EXTENSIONS = {
    '.wav', '.mp3', '.m4a', '.ogg', '.flac',
    '.aac', '.wma', '.aiff', '.opus',
}


def can_handle(file_path):
    """Return True if this plugin can process the given file."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in AUDIO_EXTENSIONS


def get_actions():
    """Return the list of actions this plugin supports."""
    return [
        {
            "key": "decode",
            "label": "Decode signal (11-step protocol)",
            "description": "FFT frequency analysis, alphabet mapping, word matching, ECL scoring",
        },
        {
            "key": "frequencies",
            "label": "Extract frequency inventory",
            "description": "Show all detected frequencies and their occurrence counts",
        },
        {
            "key": "spectrogram",
            "label": "Generate frequency timeline",
            "description": "Map dominant frequencies across time windows",
        },
    ]


def run_action(file_path, action_key):
    """Execute a signal processing action on the given file."""
    if action_key == "decode":
        from .engine import decode_file
        return decode_file(file_path)

    elif action_key == "frequencies":
        from .engine import convert_to_wav, extract_frequencies, get_frequency_inventory
        wav_path = convert_to_wav(file_path)
        timeline, sr = extract_frequencies(wav_path)
        inventory = get_frequency_inventory(timeline)
        return {
            "type": "frequency_inventory",
            "total_windows": len(timeline),
            "sample_rate": sr,
            "frequencies": [
                {"freq_hz": f, "count": c} for f, c in inventory
            ],
        }

    elif action_key == "spectrogram":
        from .engine import convert_to_wav, extract_frequencies
        wav_path = convert_to_wav(file_path)
        timeline, sr = extract_frequencies(wav_path)
        return {
            "type": "frequency_timeline",
            "sample_rate": sr,
            "total_points": len(timeline),
            "timeline": [
                {"time": round(t, 4), "freq_hz": round(f, 1), "magnitude": round(m, 1)}
                for t, f, m in timeline[:200]  # cap at 200 for readability
            ],
        }

    else:
        raise ValueError("Unknown action: %s" % action_key)
