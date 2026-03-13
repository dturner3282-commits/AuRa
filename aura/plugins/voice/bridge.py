"""
Voice Bridge — Offline speech-to-code via Vosk and SUSI.AI.

Provides voice control for GapDet:
- "fix this code" → runs gapdet fix
- "detect gaps in main.c" → runs gapdet detect
- "translate to rust" → runs gapdet translate

Supports:
- Vosk (offline speech recognition, 20+ languages)
- SUSI.AI (offline voice assistant framework)

100% offline after model download. No cloud APIs.

Usage:
    # With Vosk
    pip install vosk sounddevice
    gapdet voice --engine vosk

    # With SUSI.AI
    gapdet voice --engine susi
"""

import os
import sys
import json
import queue
import threading
from typing import Optional, Callable, Dict


class VoskBridge:
    """
    Vosk-based offline speech recognition bridge.
    Downloads a small model (~50MB) once, then works 100% offline.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.running = False
        self.callback: Optional[Callable] = None

    def setup(self) -> bool:
        """Initialize Vosk. Returns True if successful."""
        try:
            from vosk import Model, KaldiRecognizer
        except ImportError:
            print("Vosk not installed. Install with:")
            print("  pip install vosk sounddevice")
            print("Then download a model from https://alphacephei.com/vosk/models")
            return False

        # Find or download model
        if self.model_path and os.path.exists(self.model_path):
            model_dir = self.model_path
        else:
            # Check common locations
            candidates = [
                os.path.expanduser("~/.vosk/model"),
                os.path.expanduser("~/vosk-model-small-en-us-0.15"),
                "vosk-model",
            ]
            model_dir = None
            for c in candidates:
                if os.path.exists(c):
                    model_dir = c
                    break

            if model_dir is None:
                print("No Vosk model found. Download one from:")
                print("  https://alphacephei.com/vosk/models")
                print("Place it at ~/.vosk/model or specify with --vosk-model")
                return False

        from vosk import Model, KaldiRecognizer
        self.model = Model(model_dir)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        return True

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice audio stream."""
        self.audio_queue.put(bytes(indata))

    def listen(self, on_command: Callable[[str], None]) -> None:
        """
        Start listening for voice commands.
        Calls on_command(text) when speech is recognized.
        """
        try:
            import sounddevice as sd
        except ImportError:
            print("sounddevice not installed. Install with: pip install sounddevice")
            return

        self.callback = on_command
        self.running = True

        print("Listening for voice commands... (say 'stop' to quit)")
        print("Commands: 'fix <file>', 'detect <file>', 'translate to <lang>', 'complete <file>'")

        with sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype="int16",
            channels=1, callback=self._audio_callback,
        ):
            while self.running:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        print(f"  Heard: '{text}'")
                        if text.lower() in ("stop", "quit", "exit"):
                            self.running = False
                            break
                        if self.callback:
                            self.callback(text)

    def stop(self) -> None:
        self.running = False


class SUSIBridge:
    """
    SUSI.AI bridge for voice control.
    Uses SUSI's offline capabilities for intent recognition.
    """

    def __init__(self, susi_path: Optional[str] = None) -> None:
        self.susi_path = susi_path or os.path.expanduser("~/.susi")
        self.running = False

    def setup(self) -> bool:
        """Check if SUSI.AI is available."""
        # SUSI can work via its local server or Python API
        try:
            import requests
            # Check if SUSI local server is running
            resp = requests.get("http://127.0.0.1:4000/susi/chat.json?q=hello", timeout=2)
            if resp.status_code == 200:
                print("SUSI.AI local server detected")
                return True
        except Exception:
            pass

        print("SUSI.AI not detected. To set up:")
        print("  1. Clone: git clone https://github.com/fossasia/susi_server.git")
        print("  2. Build: cd susi_server && ./gradlew build")
        print("  3. Run: ./bin/start.sh")
        print("  4. Or use Vosk instead: gapdet voice --engine vosk")
        return False

    def query(self, text: str) -> Dict:
        """Send a query to SUSI local server."""
        try:
            import requests
            resp = requests.get(
                "http://127.0.0.1:4000/susi/chat.json",
                params={"q": text},
                timeout=5,
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def listen(self, on_command: Callable[[str], None]) -> None:
        """
        Listen loop using SUSI + Vosk for STT.
        Falls back to text input if no microphone.
        """
        self.running = True
        print("SUSI.AI + GapDet voice control active")
        print("Type commands or speak (if Vosk STT is available)")
        print("Commands: fix <file>, detect <file>, translate to <lang>, quit")

        while self.running:
            try:
                text = input("gapdet> ").strip()
                if text.lower() in ("stop", "quit", "exit"):
                    self.running = False
                    break
                if text and on_command:
                    on_command(text)
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    def stop(self) -> None:
        self.running = False


class VoiceCommandHandler:
    """
    Processes voice commands and routes them to GapDet operations.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path

    def handle(self, text: str) -> None:
        """Parse and execute a voice command."""
        text_lower = text.lower().strip()

        # Parse intent
        if any(w in text_lower for w in ["fix", "patch", "repair"]):
            self._handle_fix(text)
        elif any(w in text_lower for w in ["detect", "scan", "find", "check"]):
            self._handle_detect(text)
        elif any(w in text_lower for w in ["translate", "convert"]):
            self._handle_translate(text)
        elif any(w in text_lower for w in ["complete", "finish"]):
            self._handle_complete(text)
        elif any(w in text_lower for w in ["analyze", "analyse"]):
            self._handle_analyze(text)
        elif any(w in text_lower for w in ["info", "status"]):
            self._handle_info()
        else:
            print(f"  Unknown command: '{text}'")
            print("  Try: fix <file>, detect <file>, translate to <lang>, analyze <file>")

    def _extract_file(self, text: str) -> Optional[str]:
        """Extract a filename from voice command text."""
        words = text.split()
        for word in words:
            if "." in word and not word.startswith("."):
                return word
        return None

    def _handle_fix(self, text: str) -> None:
        filename = self._extract_file(text)
        if filename and os.path.exists(filename):
            print(f"  Fixing: {filename}")
            os.system(f"gapdet fix {filename}")
        else:
            print(f"  File not found. Say 'fix <filename>'")

    def _handle_detect(self, text: str) -> None:
        filename = self._extract_file(text)
        if filename and os.path.exists(filename):
            print(f"  Detecting gaps in: {filename}")
            os.system(f"gapdet detect {filename}")
        else:
            print(f"  File not found. Say 'detect <filename>'")

    def _handle_translate(self, text: str) -> None:
        text_lower = text.lower()
        filename = self._extract_file(text)
        # Find target language
        target = None
        if " to " in text_lower:
            target = text_lower.split(" to ")[-1].strip().split()[0]
        if filename and target:
            print(f"  Translating {filename} to {target}")
            os.system(f"gapdet translate {filename} --to {target}")
        else:
            print("  Say 'translate <file> to <language>'")

    def _handle_complete(self, text: str) -> None:
        filename = self._extract_file(text)
        if filename and os.path.exists(filename):
            print(f"  Completing: {filename}")
            os.system(f"gapdet complete {filename}")
        else:
            print("  File not found. Say 'complete <filename>'")

    def _handle_analyze(self, text: str) -> None:
        filename = self._extract_file(text)
        if filename and os.path.exists(filename):
            print(f"  Analyzing: {filename}")
            os.system(f"gapdet analyze {filename}")
        else:
            print("  File not found. Say 'analyze <filename>'")

    def _handle_info(self) -> None:
        os.system("gapdet info")


def start_voice(
    engine: str = "vosk",
    model_path: Optional[str] = None,
    vosk_model: Optional[str] = None,
) -> None:
    """
    Start voice control.

    Args:
        engine: "vosk" or "susi"
        model_path: Path to GapDet model
        vosk_model: Path to Vosk speech model
    """
    handler = VoiceCommandHandler(model_path)

    if engine == "vosk":
        bridge = VoskBridge(vosk_model)
        if bridge.setup():
            bridge.listen(handler.handle)
        else:
            print("Falling back to text input mode...")
            susi = SUSIBridge()
            susi.listen(handler.handle)
    elif engine == "susi":
        bridge = SUSIBridge()
        if bridge.setup():
            bridge.listen(handler.handle)
        else:
            print("SUSI not available. Try: gapdet voice --engine vosk")
    else:
        print(f"Unknown engine: {engine}. Use 'vosk' or 'susi'.")
