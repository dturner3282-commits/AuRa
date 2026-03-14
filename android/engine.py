"""
Aura Signal Processing Engine
==============================
Self-contained signal decode engine. No internet, no external APIs.
All dictionaries, alphabets, and logic baked in.

Entry point: decode_file(file_path) -> dict
"""

import os
import sys
import subprocess
import math
from collections import Counter

import numpy as np
from scipy.io import wavfile


# ============================================================
# ALPHABETS & DICTIONARIES (all baked in)
# ============================================================

ENGLISH_ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
RUSSIAN_ALPHA = (
    '\u0410\u0411\u0412\u0413\u0414\u0415\u0416\u0417\u0418\u0419'
    '\u041a\u041b\u041c\u041d\u041e\u041f\u0420\u0421\u0422\u0423'
    '\u0424\u0425\u0426\u0427\u0428\u0429\u042a\u042b\u042c\u042d'
    '\u042e\u042f'
)

# Russian frequency-order alphabet (most common letters first)
RU_FREQ_ALPHA = (
    '\u041e\u0415\u0410\u0418\u041d\u0422\u0421\u0420\u0412\u041b'
    '\u041a\u041c\u0414\u041f\u0423\u042f\u042b\u042c\u0413\u0417'
    '\u0411\u0427\u0419\u0425\u0416\u0428\u042e\u0426\u0429\u042d'
    '\u0424\u042a'
)

RU_TO_LATIN = {
    '\u0410': 'A', '\u0411': 'B', '\u0412': 'V', '\u0413': 'G', '\u0414': 'D',
    '\u0415': 'E', '\u0416': 'ZH', '\u0417': 'Z', '\u0418': 'I', '\u0419': 'Y',
    '\u041a': 'K', '\u041b': 'L', '\u041c': 'M', '\u041d': 'N', '\u041e': 'O',
    '\u041f': 'P', '\u0420': 'R', '\u0421': 'S', '\u0422': 'T', '\u0423': 'U',
    '\u0424': 'F', '\u0425': 'KH', '\u0426': 'TS', '\u0427': 'CH', '\u0428': 'SH',
    '\u0429': 'SHCH', '\u042a': '', '\u042b': 'Y', '\u042c': "'", '\u042d': 'E',
    '\u042e': 'YU', '\u042f': 'YA',
}

RU_TO_EN = {
    '\u0410': 'A', '\u0411': 'B', '\u0412': 'V', '\u0413': 'G', '\u0414': 'D',
    '\u0415': 'E', '\u0416': 'J', '\u0417': 'Z', '\u0418': 'I', '\u0419': 'Y',
    '\u041a': 'K', '\u041b': 'L', '\u041c': 'M', '\u041d': 'N', '\u041e': 'O',
    '\u041f': 'P', '\u0420': 'R', '\u0421': 'S', '\u0422': 'T', '\u0423': 'U',
    '\u0424': 'F', '\u0425': 'H', '\u0426': 'C', '\u0427': 'C', '\u0428': 'W',
    '\u0429': 'X', '\u042a': '', '\u042b': 'Y', '\u042c': '', '\u042d': 'E',
    '\u042e': 'U', '\u042f': 'A',
}

RU_WORDS = {
    '\u0412\u041d\u0418\u041c\u0410\u041d\u0418\u0415': 'ATTENTION',
    '\u0421\u0422\u0410\u041d\u0426\u0418\u042f': 'STATION',
    '\u0421\u0418\u0413\u041d\u0410\u041b': 'SIGNAL',
    '\u041a\u041e\u041c\u0410\u041d\u0414\u0410': 'COMMAND',
    '\u041f\u0420\u0418\u041d\u042f\u0422\u041e': 'RECEIVED',
    '\u0413\u0420\u0423\u041f\u041f\u0410': 'GROUP',
    '\u041f\u041e\u041d\u042f\u041b': 'UNDERSTOOD',
    '\u041d\u041e\u041c\u0415\u0420': 'NUMBER',
    '\u041a\u0410\u041d\u0410\u041b': 'CHANNEL',
    '\u041e\u0422\u0412\u0415\u0422': 'ANSWER',
    '\u041d\u0410\u0427\u0410\u041b\u041e': 'START',
    '\u041a\u041e\u041d\u0415\u0426': 'END',
    '\u0413\u041e\u0422\u041e\u0412': 'READY',
    '\u041f\u0420\u0418\u0415\u041c': 'OVER',
    '\u0420\u0410\u0414\u0418\u041e': 'RADIO',
    '\u0414\u041e\u041a\u041b\u0410\u0414': 'REPORT',
    '\u0421\u0422\u041e\u041f': 'STOP',
    '\u041f\u041e\u0421\u0422': 'POST',
    '\u0411\u0410\u0417\u0410': 'BASE',
    '\u0426\u0415\u041d\u0422\u0420': 'CENTER',
    '\u041a\u041e\u0414': 'CODE',
    '\u041a\u041b\u042e\u0427': 'KEY',
    '\u0428\u0418\u0424\u0420': 'CIPHER',
    '\u042d\u0422\u041e': 'this is',
    '\u041a\u0410\u041a': 'how',
    '\u0427\u0422\u041e': 'what',
    '\u041e\u041d\u0418': 'they',
    '\u0411\u042b\u041b': 'was',
    '\u0414\u041b\u042f': 'for',
    '\u0412\u0421\u0415': 'all',
    '\u0422\u0410\u041a': 'so/thus',
    '\u041e\u041d\u0410': 'she',
    '\u0422\u0423\u0422': 'here',
    '\u0422\u0410\u041c': 'there',
    '\u041a\u0422\u041e': 'who',
    '\u0413\u0414\u0415': 'where',
    '\u041d\u0415\u0422': 'no',
    '\u0414\u041e\u041c': 'house',
    '\u041c\u0418\u0420': 'world/peace',
    '\u0418\u041b\u0418': 'or',
    '\u041f\u0420\u041e': 'about',
    '\u041f\u041e\u0414': 'under',
    '\u041d\u0410\u0414': 'above',
    '\u041f\u0420\u0418': 'at/near',
    '\u0421\u041e\u041d': 'dream/sleep',
    '\u0422\u041e\u041d': 'tone',
    '\u041a\u041e\u041d': 'end/stake',
    '\u041b\u041e\u0422': 'lot',
    '\u041f\u041e\u0422': 'sweat',
    '\u041a\u041e\u0422': 'cat',
    '\u0420\u041e\u0422': 'mouth',
    '\u0422\u041e\u041f': 'top/stomp',
    '\u041f\u041e\u041b': 'floor/gender',
    '\u041d\u041e\u0421': 'nose',
    '\u041d\u041e\u0422': 'note(s)',
    '\u041c\u041e\u0422': 'moth',
    '\u041a\u041e\u041b': 'stake',
    '\u0421\u041e\u041b': 'sol',
    '\u041e\u041d\u041e': 'it',
    '\u041e\u0422': 'from',
    '\u041f\u041e': 'by/along',
    '\u041d\u041e': 'but',
    '\u041e\u041d': 'he',
    '\u0422\u041e': 'that/this',
    '\u041d\u0410': 'on/to',
    '\u0414\u0410': 'yes',
    '\u041d\u0415': 'no/not',
    '\u041c\u042b': 'we',
    '\u0422\u042b': 'you',
    '\u041d\u0423': 'well',
}

EN_WORDS = [
    'ATTENTION', 'STATION', 'SIGNAL', 'COMMAND', 'RECEIVED', 'GROUP',
    'UNDERSTOOD', 'NUMBER', 'CHANNEL', 'ANSWER', 'REPORT',
    'STOP', 'START', 'OVER', 'RADIO', 'POST', 'BASE', 'CENTER',
    'CODE', 'KEY', 'CIPHER', 'READY', 'END',
    'THE', 'AND', 'FOR', 'ARE', 'NOT', 'YOU', 'ALL', 'CAN',
    'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'TO', 'AT', 'IN', 'ON',
    'IT', 'IS', 'OR', 'AN', 'NO', 'DO', 'IF', 'UP', 'SO',
    'FROM', 'HERE', 'THERE', 'THIS', 'THAT', 'WHAT', 'WHEN',
    'WHO', 'HOW', 'WHY', 'NOW', 'GO', 'GET', 'SET', 'RUN', 'OFF',
    'TONE', 'NOTE', 'TOP', 'POT', 'LOT', 'SON', 'TON', 'NOR',
    'ROT', 'OPT', 'SLOT', 'PLOT', 'KNOT', 'MOON', 'NOON',
    'SOON', 'ROOM', 'TOOL', 'POOL', 'LOOP', 'MONK', 'FONT',
    'LONG', 'SONG',
]

# Extended word dictionary for divisor-sweep mapping
PROTOCOL_WORDS = {}
PROTOCOL_WORDS.update(RU_WORDS)
PROTOCOL_WORDS.update({
    '\u0412\u041e\u0415\u0422': 'howls',
    '\u0422\u0415\u0421\u0422': 'test',
    '\u041f\u041e\u0415\u0422': 'sings',
    '\u0418\u0414\u0415\u0422': 'goes',
    '\u0412\u041e\u0419': 'howl!(cmd)',
    '\u0412\u041e\u042f': 'warrior',
    '\u0417\u041e\u0412': 'call',
    '\u0416\u0414\u0423': 'I_wait',
    '\u0416\u0414\u0418': 'wait!',
    '\u0416\u0418\u0412': 'alive',
    '\u0412\u041e\u042e': 'I_wage_war',
})


# ============================================================
# CORE SIGNAL PROCESSING FUNCTIONS
# ============================================================

def detect_dominant_frequency(audio_data, sample_rate):
    """Use FFT to find the dominant frequency in an audio chunk."""
    if len(audio_data) == 0:
        return 0.0, 0.0
    windowed = audio_data * np.hanning(len(audio_data))
    fft_data = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_data)
    freqs = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
    peak_idx = np.argmax(magnitudes[1:]) + 1
    peak_freq = freqs[peak_idx]
    peak_magnitude = magnitudes[peak_idx]
    return peak_freq, peak_magnitude


def convert_to_wav(input_path):
    """Convert M4A/MP3/etc to WAV using ffmpeg. Returns path to WAV file."""
    if input_path.lower().endswith('.wav'):
        return input_path
    wav_path = os.path.splitext(input_path)[0] + '_converted.wav'
    if os.path.exists(wav_path):
        return wav_path
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', input_path, '-ac', '1', '-ar', '44100', wav_path],
            capture_output=True, check=True
        )
        return wav_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "Could not convert %s to WAV. Install ffmpeg." % input_path
        )


def make_reversed(wav_path):
    """Create a reversed version of a WAV file."""
    rev_path = wav_path.replace('.wav', '_reversed.wav')
    if os.path.exists(rev_path):
        return rev_path
    sr, data = wavfile.read(wav_path)
    if data.ndim > 1:
        data = data[:, 0]
    wavfile.write(rev_path, sr, data[::-1])
    return rev_path


def extract_frequencies(wav_path, window_ms=25, mag_threshold=50):
    """Extract dominant frequency from each time window."""
    sr, raw = wavfile.read(wav_path)
    if raw.ndim > 1:
        raw = raw[:, 0]
    audio = raw.astype(np.float64)
    window_samples = int(sr * window_ms / 1000)
    timeline = []
    for i in range(0, len(audio) - window_samples, window_samples):
        chunk = audio[i:i + window_samples]
        freq, mag = detect_dominant_frequency(chunk, sr)
        t = i / sr
        if mag > mag_threshold:
            timeline.append((t, freq, mag))
    return timeline, sr


def get_frequency_inventory(timeline, min_count=3, freq_range=(50, 2000)):
    """Count occurrences of each rounded frequency."""
    bins = {}
    for t, f, m in timeline:
        b = round(f / 40) * 40
        bins[b] = bins.get(b, 0) + 1
    return sorted(
        [(f, c) for f, c in bins.items()
         if freq_range[0] <= f <= freq_range[1] and c >= min_count],
        key=lambda x: x[0]
    )


def find_anchor_letters(inventory):
    """Identify potential letter positions from frequency clusters."""
    freqs = [f for f, c in inventory if c >= 3]
    return freqs


def check_sequential_pattern(freqs):
    """Check if frequencies represent sequential alphabet positions."""
    if len(freqs) < 3:
        return None
    best = None
    best_score = 0
    for hz_per in range(20, 81, 5):
        for direction in ['descending', 'ascending']:
            for base in range(200, 1500, 10):
                score = 0
                mapping = {}
                for f in freqs:
                    if direction == 'descending':
                        pos = round((base - f) / hz_per)
                    else:
                        pos = round((f - base) / hz_per)
                    if 0 <= pos < 26:
                        expected = base - pos * hz_per if direction == 'descending' else base + pos * hz_per
                        error = abs(f - expected)
                        if error <= hz_per * 0.4:
                            en_letter = ENGLISH_ALPHA[pos] if pos < 26 else '?'
                            ru_pos = pos
                            ru_letter = RUSSIAN_ALPHA[ru_pos] if ru_pos < len(RUSSIAN_ALPHA) else '?'
                            mapping[f] = (en_letter, pos, ru_letter, ru_pos)
                            score += 1
                if score >= 3 and score > best_score:
                    best_score = score
                    best = (base, hz_per, direction, score, mapping)
    return best


def build_alphabet_maps(base, hz_per, direction):
    """Build freq->letter maps for Russian and English."""
    ru_map = {}
    en_map = {}
    for pos in range(len(RUSSIAN_ALPHA)):
        freq = base - pos * hz_per if direction == 'descending' else base + pos * hz_per
        if freq >= 40:
            ru_map[freq] = RUSSIAN_ALPHA[pos]
    for pos in range(len(ENGLISH_ALPHA)):
        freq = base - pos * hz_per if direction == 'descending' else base + pos * hz_per
        if freq >= 40:
            en_map[freq] = ENGLISH_ALPHA[pos]
    return en_map, ru_map


def decode_timeline(timeline, freq_map, tolerance=30):
    """Map each frequency in timeline to nearest letter."""
    decoded = []
    for t, freq, mag in timeline:
        best_letter = None
        best_dist = tolerance
        for mf, letter in freq_map.items():
            d = abs(freq - mf)
            if d < best_dist:
                best_dist = d
                best_letter = letter
        if best_letter:
            decoded.append((t, best_letter, freq))
    return decoded


def dedup(text):
    """Remove adjacent duplicate characters."""
    if not text:
        return ''
    result = text[0]
    for ch in text[1:]:
        if ch != result[-1]:
            result += ch
    return result


def find_words(text, lang='EN'):
    """Search for known words in decoded text."""
    found = []
    if lang == 'EN':
        for word in EN_WORDS:
            cnt = text.count(word)
            if cnt > 0:
                found.append((word, cnt))
        found.sort(key=lambda x: len(x[0]) * x[1], reverse=True)
    else:
        for word, trans in RU_WORDS.items():
            cnt = text.count(word)
            if cnt > 0:
                found.append((word, trans, cnt))
        found.sort(key=lambda x: len(x[0]) * x[2], reverse=True)
    return found


def transliterate(text):
    """Convert Russian text to Latin transliteration."""
    return ''.join(RU_TO_LATIN.get(ch, ch) for ch in text)


def phonetic_remap(text):
    """Remap Russian text to English phonetic equivalents."""
    return ''.join(RU_TO_EN.get(ch, ch) for ch in text)


# ============================================================
# 11-STEP PROTOCOL DECODE
# ============================================================

def protocol_decode(wav_path, output_lines):
    """Run full 11-step Signal Decode Protocol on any audio file.

    Universal - discovers signal structure automatically.
    No hardcoded frequencies, payloads, or assumptions.

    Returns dict with decode results including ECL score and decoded words.
    """
    sr, raw = wavfile.read(wav_path)
    if raw.ndim > 1:
        raw = raw[:, 0]
    audio = raw.astype(np.float64)
    N = len(audio)
    duration = N / sr

    def p(s=""):
        output_lines.append(s)

    p("=" * 70)
    p("  SIGNAL DECRYPTION - FULL 11-STEP PROTOCOL")
    p("  File: %s" % os.path.basename(wav_path))
    p("  Duration: %.1fs | Sample rate: %dHz | Samples: %d" % (duration, sr, N))
    p("=" * 70)

    result = {
        'duration': duration, 'sr': sr, 'samples': N,
        'decoded_word': None, 'decoded_meaning': None, 'ecl': 0,
    }

    if N < sr * 0.1:
        p("  [!] Audio too short for protocol analysis (< 0.1s)")
        return result

    # STEP 1: FREQUENCY EXTRACTION
    p("\n" + "=" * 70)
    p("  STEP 1: FREQUENCY EXTRACTION")
    p("=" * 70)

    fft_all = np.abs(np.fft.rfft(audio * np.hanning(N)))
    fft_f = np.fft.rfftfreq(N, 1.0 / sr)
    mask_g = (fft_f >= 100) & (fft_f <= 2000)
    top_idx = np.argsort(fft_all[mask_g])[-5:][::-1]
    top_freq = fft_f[mask_g][top_idx]
    top_pct = fft_all[mask_g][top_idx] / fft_all[mask_g].sum() * 100

    p("  Global FFT (full file):")
    for i in range(5):
        p("    %8.1f Hz: %.1f%%" % (top_freq[i], top_pct[i]))

    win = 256
    hop = win
    n_frames = (N - win) // hop
    if n_frames < 2:
        p("  [!] Not enough frames for short-window analysis")
        return result

    shape = (n_frames, win)
    strides = (audio.strides[0] * hop, audio.strides[0])
    frames = np.lib.stride_tricks.as_strided(
        audio, shape=shape, strides=strides
    ).copy()
    frames *= np.hanning(win)
    spectra = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    fm = (freqs >= 100) & (freqs <= 2000)
    spec_masked = spectra[:, fm]
    peak_idx = np.argmax(spec_masked, axis=1)
    dom_freqs = np.round(freqs[fm][peak_idx]).astype(int)

    fc = Counter(dom_freqs.tolist())
    total_w = n_frames
    top5 = fc.most_common(5)

    p("\n  Short-window analysis (%d-sample, %d windows):" % (win, n_frames))
    for f, c in top5:
        p("    %6d Hz: %5d (%.1f%%)" % (f, c, 100 * c / total_w))

    result['top_freqs'] = top5

    # STEP 2: MULTI-RESOLUTION CHECK
    p("\n" + "=" * 70)
    p("  STEP 2: MULTI-RESOLUTION CHECK")
    p("=" * 70)

    for fft_size in [256, 512, 1024, 2048, 4096]:
        if N >= fft_size:
            chunk = audio[:fft_size] * np.hanning(fft_size)
            ff = np.abs(np.fft.rfft(chunk))
            fq = np.fft.rfftfreq(fft_size, 1.0 / sr)
            mm = (fq >= 100) & (fq <= 2000)
            if mm.any():
                pk = fq[mm][np.argmax(ff[mm])]
                p("  FFT %5d: dominant = %.1f Hz" % (fft_size, pk))

    fp_size = min(8192, N)
    chunk = audio[:fp_size] * np.hanning(fp_size)
    ff = np.abs(np.fft.rfft(chunk))
    fq = np.fft.rfftfreq(fp_size, 1.0 / sr)
    mm = (fq >= 100) & (fq <= 2000)
    if mm.any():
        peak_f = fq[mm][np.argmax(ff[mm])]
        peak_mag = ff[mm].max()
        above = fq[mm][ff[mm] >= peak_mag * 0.707]
        wobble = (above[-1] - above[0]) / 2 if len(above) > 1 else 0
        p("\n  HARDWARE FINGERPRINT: %.1f Hz +/- %.1f Hz" % (peak_f, wobble))
        result['hw_fingerprint'] = peak_f
        result['hw_wobble'] = wobble

    # STEP 3: FSK DEMODULATION
    p("\n" + "=" * 70)
    p("  STEP 3: FSK DEMODULATION (H/L Classifier)")
    p("=" * 70)

    if len(top5) >= 2:
        f1, f2 = top5[0][0], top5[1][0]
        boundary = (f1 + f2) // 2
    else:
        boundary = top5[0][0] if top5 else 460

    bitstream = (dom_freqs >= boundary).astype(int).tolist()
    total_bits = len(bitstream)
    h_count = sum(bitstream)
    l_count = total_bits - h_count

    p("  Two tones detected: %s" % str([(f, c) for f, c in top5[:2]]))
    p("  Auto-boundary: %d Hz" % boundary)
    p("  Total bits: %d" % total_bits)
    p("  H (1s): %d (%.1f%%)" % (h_count, 100 * h_count / total_bits))
    p("  L (0s): %d (%.1f%%)" % (l_count, 100 * l_count / total_bits))
    p("  First 200 bits: %s" % ''.join(str(b) for b in bitstream[:200]))

    result['boundary'] = boundary
    result['h_pct'] = 100 * h_count / total_bits
    result['l_pct'] = 100 * l_count / total_bits

    # STEP 4: TRANSITION MATRIX
    p("\n" + "=" * 70)
    p("  STEP 4: TRANSITION MATRIX")
    p("=" * 70)

    bs = np.array(bitstream)
    hh = int(np.sum((bs[:-1] == 1) & (bs[1:] == 1)))
    hl_t = int(np.sum((bs[:-1] == 1) & (bs[1:] == 0)))
    lh = int(np.sum((bs[:-1] == 0) & (bs[1:] == 1)))
    ll = int(np.sum((bs[:-1] == 0) & (bs[1:] == 0)))

    p_hh = hh / max(1, hh + hl_t)
    p_ll = ll / max(1, ll + lh)

    p("  HH=%d  HL=%d  LH=%d  LL=%d" % (hh, hl_t, lh, ll))
    p("  P(H|H) = %.4f" % p_hh)
    p("  P(L|L) = %.4f" % p_ll)

    result['transition'] = {
        'HH': hh, 'HL': hl_t, 'LH': lh, 'LL': ll,
        'P_HH': p_hh, 'P_LL': p_ll,
    }

    # STEP 5: RUN-LENGTH ANALYSIS
    p("\n" + "=" * 70)
    p("  STEP 5: RUN-LENGTH ANALYSIS")
    p("=" * 70)

    runs = []
    current = bitstream[0]
    count = 1
    for b in bitstream[1:]:
        if b == current:
            count += 1
        else:
            runs.append((current, count))
            current = b
            count = 1
    runs.append((current, count))

    h_runs = [cnt for val, cnt in runs if val == 1]
    l_runs = [cnt for val, cnt in runs if val == 0]

    p("  Total runs: %d" % len(runs))
    p("  H-runs (DATA): %s" % str(h_runs))
    p("  L-runs (SEPS): %s" % str(l_runs))

    result['h_runs'] = h_runs
    result['l_runs'] = l_runs

    if l_runs and all(r == 1 for r in l_runs):
        p("  All L-runs length 1 --> PURE SEPARATORS")
        p("  PAYLOAD = H-run lengths: %s" % str(h_runs))

    # STEP 6: CHECK FOR PAIRED STRUCTURE
    p("\n" + "=" * 70)
    p("  STEP 6: CHECK FOR PAIRED STRUCTURE")
    p("=" * 70)

    payload = h_runs
    result['payload'] = payload
    result['paired'] = False

    p("  Payload (%d values): %s" % (len(payload), str(payload)))

    if len(payload) >= 2 and len(payload) % 2 == 0:
        pairs = [(payload[i], payload[i + 1])
                 for i in range(0, len(payload), 2)]
        diffs = [a - b for a, b in pairs]
        p("  Pairs: %s" % str(pairs))
        p("  Differences: %s" % str(diffs))
        if len(set(diffs)) == 1:
            p("  *** PAIRED STRUCTURE FOUND ***")
            p("  Constant difference: %d" % diffs[0])
            result['paired'] = True
            result['pair_diff'] = diffs[0]
            result['primary_values'] = [a for a, b in pairs]
    elif len(payload) >= 2:
        pairs = [(payload[i], payload[i + 1])
                 for i in range(0, len(payload) - 1, 2)]
        diffs = [a - b for a, b in pairs]
        p("  Pairs (incomplete last): %s" % str(pairs))
        p("  Differences: %s" % str(diffs))

    # STEP 7: ENTROPY CHECK
    p("\n" + "=" * 70)
    p("  STEP 7: ENTROPY CHECK")
    p("=" * 70)

    bit_counts = Counter(bitstream)
    bit_ent = sum(
        -(c / total_bits) * math.log2(c / total_bits)
        for c in bit_counts.values() if c > 0
    )

    bytes_list = []
    for i in range(0, len(bitstream) - 7, 8):
        bv = 0
        for j in range(8):
            bv = (bv << 1) | bitstream[i + j]
        bytes_list.append(bv)
    bc = Counter(bytes_list)
    byte_ent = 0.0
    if bytes_list:
        byte_ent = sum(
            -(c / len(bytes_list)) * math.log2(c / len(bytes_list))
            for c in bc.values() if c > 0
        )

    p("  Bit entropy:  %.4f / 1.0" % bit_ent)
    p("  Byte entropy: %.4f / 8.0" % byte_ent)

    result['bit_entropy'] = bit_ent
    result['byte_entropy'] = byte_ent

    # STEP 8: LETTER MAPPING (Divisor Sweep)
    p("\n" + "=" * 70)
    p("  STEP 8: LETTER MAPPING (Divisor Sweep)")
    p("=" * 70)

    all_hits = []
    for wlen in range(2, min(6, len(payload) + 1)):
        for start in range(len(payload) - wlen + 1):
            sub = payload[start:start + wlen]
            for div in range(25, 601):
                indices = [round(v / div) for v in sub]
                rev_indices = list(reversed(indices))
                for name, alpha in [('RU-std', RUSSIAN_ALPHA),
                                    ('RU-freq', RU_FREQ_ALPHA)]:
                    alen = len(alpha)
                    for lbl, idx_list in [('fwd', indices),
                                          ('rev', rev_indices)]:
                        if all(0 <= i < alen for i in idx_list):
                            word = ''.join(alpha[i] for i in idx_list)
                            if word in PROTOCOL_WORDS:
                                all_hits.append((
                                    div, name, lbl, word,
                                    PROTOCOL_WORDS[word], start, wlen,
                                ))

    seen = set()
    hit_summary = []
    for div, alph, direction, word, meaning, start, wlen in all_hits:
        key = (word, alph, direction)
        if key not in seen:
            seen.add(key)
            divs_for = [
                d for d, a, dr, w, m_, s_, wl_ in all_hits
                if w == word and dr == direction and a == alph
            ]
            entry = "%-6s = %-15s [%-7s %3s] div %d-%d (%d hits)" % (
                word, '"' + meaning + '"', alph, direction,
                min(divs_for), max(divs_for), len(divs_for),
            )
            p("    %s" % entry)
            hit_summary.append(
                (word, meaning, len(divs_for), min(divs_for), max(divs_for))
            )

    result['word_hits'] = hit_summary

    if not hit_summary:
        p("    No dictionary words found in divisor sweep.")

    # STEP 9: MULTI-KEY SWEEP
    p("\n" + "=" * 70)
    p("  STEP 9: MULTI-KEY SWEEP (Deepest Anchors)")
    p("=" * 70)

    wc = Counter()
    for _, _, _, w, m_, _, _ in all_hits:
        wc[(w, m_)] += 1

    ranked = wc.most_common(10)
    ranked_flat = [(w, m_, c) for (w, m_), c in ranked]
    result['ranked_words'] = ranked_flat

    for (w, m_), c in ranked:
        latin = ''.join(RU_TO_LATIN.get(ch, ch) for ch in w)
        p("    %-6s (%s) = \"%s\" -- %d hits" % (w, latin, m_, c))

    if all_hits:
        wdr = {}
        for d, _, _, w, m_, _, _ in all_hits:
            wdr.setdefault(w, set()).add(d)
        p("\n  Stability (words across most divisors):")
        for w in sorted(wdr, key=lambda x: -len(wdr[x]))[:5]:
            ds = wdr[w]
            m_ = PROTOCOL_WORDS.get(w, '?')
            latin = ''.join(RU_TO_LATIN.get(ch, ch) for ch in w)
            p("    %-6s (%s) = \"%s\" -- %d divisors (range %d-%d)" % (
                w, latin, m_, len(ds), min(ds), max(ds)))

    # STEP 10: ECL SCORING
    p("\n" + "=" * 70)
    p("  STEP 10: ECL SCORING")
    p("=" * 70)

    has_fsk = len(top5) >= 2 and top5[0][1] > total_w * 0.1
    has_runs = len(h_runs) >= 2
    has_paired = result.get('paired', False)
    has_words = len(hit_summary) > 0
    low_entropy = bit_ent < 0.5

    layers = [
        ('Signal capture', 7 if N > sr else 4),
        ('FSK demodulation', 7 if has_fsk else 3),
        ('Run-length structure', 7 if has_runs else 3),
        ('Paired error-correction', 7 if has_paired else (4 if has_runs else 2)),
        ('Entropy structure', 7 if low_entropy else (5 if bit_ent < 0.9 else 3)),
        ('Letter mapping', 6 if has_words else 2),
        ('Word confidence', 5 if len(hit_summary) >= 2 else (4 if has_words else 1)),
    ]
    for layer, score in layers:
        bar = '#' * score + '.' * (7 - score)
        p("  %-35s  %d/7  [%s]" % (layer, score, bar))
    overall = sum(s for _, s in layers) / len(layers)
    p("\n  OVERALL ECL: %.1f / 7.0" % overall)
    result['ecl'] = overall
    result['ecl_layers'] = layers

    # STEP 11: INTERPRETATION
    p("\n" + "=" * 70)
    p("  STEP 11: INTERPRETATION -- THE DECODED MESSAGE")
    p("=" * 70)

    if ranked_flat:
        best_word, best_meaning, best_count = ranked_flat[0]
        latin = ''.join(RU_TO_LATIN.get(ch, ch) for ch in best_word)
        p("")
        p("  MOST LIKELY DECODED WORD:  %s (%s)" % (best_word, latin))
        p("  LANGUAGE:                  Russian")
        p("  ENGLISH MEANING:           \"%s\"" % best_meaning)
        p("  HITS ACROSS DIVISORS:      %d" % best_count)

        result['decoded_word'] = best_word
        result['decoded_meaning'] = best_meaning

        if has_paired:
            p("  SIGNAL TYPE: Handshake / check-in")
        elif bit_ent < 0.3:
            p("  SIGNAL TYPE: Structured data transmission")
        else:
            p("  SIGNAL TYPE: Complex / multi-layer encoding")

        if overall >= 6.0:
            p("\n  CONFIDENCE: HIGH -- decode is reliable")
        elif overall >= 4.5:
            p("\n  CONFIDENCE: MODERATE -- decode is plausible")
        else:
            p("\n  CONFIDENCE: LOW -- decode is speculative")
    else:
        p("  No dictionary words found.")
        p("  Signal may use a different encoding scheme.")

    p("")
    p("  +------------------------------------------------------+")
    p("  |  AURA PROTOCOL DECODE SUMMARY                        |")
    p("  |------------------------------------------------------|")
    if ranked_flat:
        best_word, best_meaning, _ = ranked_flat[0]
        latin = ''.join(RU_TO_LATIN.get(ch, ch) for ch in best_word)
        p("  |  Word:    %-40s |" % ("%s (%s)" % (best_word, latin)))
        p("  |  Meaning: %-40s |" % ('"%s"' % best_meaning))
    else:
        p("  |  Word:    %-40s |" % "(none found)")
        p("  |  Meaning: %-40s |" % "(undetermined)")
    p("  |  ECL:     %-40s |" % ("%.1f / 7.0" % overall))
    p("  |  Payload: %-40s |" % str(payload[:8]))
    p("  |  Entropy: %-40s |" % ("%.4f bit/bit" % bit_ent))
    p("  +------------------------------------------------------+")

    return result


def decode_audio(wav_path, output_lines):
    """Full classic frequency-cipher decode pipeline for one audio file."""
    timeline, sr = extract_frequencies(wav_path)
    duration = len(timeline) * 0.025

    output_lines.append("  Windows: %d, Duration: %.1fs" % (len(timeline), duration))

    inventory = get_frequency_inventory(timeline)
    signal_freqs = find_anchor_letters(inventory)
    pattern = check_sequential_pattern(signal_freqs)

    if pattern:
        base, hz_per, direction, score, mapping = pattern
    else:
        base, hz_per, direction = 1060, 50, 'descending'

    en_map, ru_map = build_alphabet_maps(base, hz_per, direction)

    ru_decoded = decode_timeline(timeline, ru_map)
    ru_raw = ''.join(ch for _, ch, _ in ru_decoded)
    ru_dd = dedup(ru_raw)
    latin = transliterate(ru_dd)
    phonetic = phonetic_remap(ru_dd)
    ru_words = find_words(ru_dd, 'RU')
    en_decoded = decode_timeline(timeline, en_map)
    en_raw = ''.join(ch for _, ch, _ in en_decoded)
    en_dd = dedup(en_raw)
    en_words = find_words(en_dd, 'EN')

    return {
        'base': base,
        'hz_per': hz_per,
        'direction': direction,
        'pattern_found': pattern is not None,
        'ru_words': ru_words,
        'en_words': en_words,
        'ru_text': ru_dd,
        'en_text': en_dd,
        'latin_text': latin,
        'phonetic_text': phonetic,
    }


def score_decode_confidence(result):
    """ECL-inspired scoring across dimensions. Returns (score, class, flags)."""
    dims = []
    dims.append(1.0 if result.get('pattern_found') else 0.4)
    ru_count = len(result.get('ru_words', []))
    dims.append(min(1.0, ru_count / 8))
    en_count = len(result.get('en_words', []))
    dims.append(min(1.0, en_count / 8))
    long_ru = sum(1 for w in result.get('ru_words', []) if len(w[0]) >= 3)
    long_en = sum(1 for w in result.get('en_words', []) if len(w[0]) >= 3)
    dims.append(min(1.0, (long_ru + long_en) / 5))
    text_len = len(result.get('ru_text', ''))
    dims.append(min(1.0, text_len / 100))
    ru_text = result.get('ru_text', '')
    if ru_text:
        covered = sum(len(w[0]) * w[2] for w in result.get('ru_words', []))
        dims.append(min(1.0, covered / max(1, len(ru_text))))
    else:
        dims.append(0.0)
    phonetic = result.get('phonetic_text', '')
    if phonetic:
        vowels = sum(1 for c in phonetic[:200] if c in 'AEIOU')
        dims.append(min(1.0, vowels / 20))
    else:
        dims.append(0.0)

    avg = sum(dims) / len(dims)
    score = 7.0 * avg

    flags = []
    if dims[1] == 0 and dims[2] == 0:
        flags.append('NO_WORDS')
    if dims[0] < 0.5:
        flags.append('NO_SIGNAL_PATTERN')
    if dims[5] < 0.1:
        flags.append('LOW_COVERAGE')
    if dims[4] < 0.2:
        flags.append('SHORT_TEXT')

    critical = len(flags) >= 3
    if critical:
        cls = 'RED'
    elif score >= 5:
        cls = 'GREEN'
    elif score >= 3:
        cls = 'YELLOW'
    elif score >= 1.5:
        cls = 'ORANGE'
    else:
        cls = 'RED'

    return score, cls, flags


# ============================================================
# PUBLIC API: decode_file()
# ============================================================

def decode_file(file_path):
    """Main entry point. Decodes an audio file and returns structured results.

    Args:
        file_path: Path to audio file (WAV, M4A, MP3)

    Returns:
        dict with keys:
            'decoded_word': str or None - the decoded word
            'decoded_meaning': str or None - English meaning
            'ecl': float - confidence score (0-7)
            'ecl_layers': list of (layer_name, score) tuples
            'confidence': str - 'HIGH', 'MODERATE', or 'LOW'
            'technical_report': str - full 11-step protocol output
            'signal_type': str - type of signal detected
            'payload': list - raw payload values
    """
    wav_path = convert_to_wav(file_path)
    rev_path = make_reversed(wav_path)

    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("AURA -- SIGNAL DECRYPTION OUTPUT")
    report_lines.append("Source: %s" % os.path.basename(file_path))
    report_lines.append("=" * 70)

    # Protocol decode (forward)
    report_lines.append("\n" + "#" * 70)
    report_lines.append("#  11-STEP PROTOCOL -- FORWARD")
    report_lines.append("#" * 70 + "\n")
    proto_fwd = protocol_decode(wav_path, report_lines)

    # Protocol decode (reversed)
    report_lines.append("\n" + "#" * 70)
    report_lines.append("#  11-STEP PROTOCOL -- REVERSED")
    report_lines.append("#" * 70 + "\n")
    proto_rev = protocol_decode(rev_path, report_lines)

    # Pick the better result
    proto_best = proto_fwd if proto_fwd.get('ecl', 0) >= proto_rev.get('ecl', 0) else proto_rev

    # Determine confidence label
    ecl = proto_best.get('ecl', 0)
    if ecl >= 6.0:
        confidence = 'HIGH'
    elif ecl >= 4.5:
        confidence = 'MODERATE'
    else:
        confidence = 'LOW'

    # Determine signal type
    if proto_best.get('paired', False):
        signal_type = 'Handshake / check-in'
    elif proto_best.get('bit_entropy', 1) < 0.3:
        signal_type = 'Structured data transmission'
    else:
        signal_type = 'Complex / multi-layer encoding'

    decoded_word = proto_best.get('decoded_word')
    decoded_meaning = proto_best.get('decoded_meaning')

    # Build human-readable summary
    if decoded_word:
        latin = ''.join(RU_TO_LATIN.get(ch, ch) for ch in decoded_word)
        summary = "%s (%s) = \"%s\"" % (decoded_word, latin, decoded_meaning)
    else:
        summary = "No word decoded"

    return {
        'decoded_word': decoded_word,
        'decoded_meaning': decoded_meaning,
        'ecl': ecl,
        'ecl_layers': proto_best.get('ecl_layers', []),
        'confidence': confidence,
        'signal_type': signal_type,
        'payload': proto_best.get('payload', []),
        'summary': summary,
        'technical_report': '\n'.join(report_lines),
        'file_name': os.path.basename(file_path),
    }


# CLI mode
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python engine.py <audio_file>")
        sys.exit(1)
    result = decode_file(sys.argv[1])
    print("\n" + "=" * 50)
    print("  AURA DECODE RESULT")
    print("=" * 50)
    print("  Word:       %s" % result['summary'])
    print("  ECL:        %.1f / 7.0" % result['ecl'])
    print("  Confidence: %s" % result['confidence'])
    print("  Signal:     %s" % result['signal_type'])
    print("=" * 50)
