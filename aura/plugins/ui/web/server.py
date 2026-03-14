"""
AuRA Minimal Web UI — The Mirror.

One big empty box. Drag a file or type. That's it.
Routes to aura.process under the hood.
"""

import os
import sys
import json
import tempfile
import http.server
import socketserver
from urllib.parse import parse_qs
from pathlib import Path

PORT = 7860
UPLOAD_DIR = tempfile.mkdtemp(prefix="aura_")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AuRA</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
#title {
    font-size: 14px;
    color: #555;
    margin-bottom: 12px;
    letter-spacing: 4px;
}
#drop-zone {
    width: 80vw;
    max-width: 700px;
    height: 50vh;
    min-height: 300px;
    border: 1px solid #333;
    background: #111;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    cursor: text;
    transition: border-color 0.2s;
}
#drop-zone:hover { border-color: #555; }
#drop-zone.drag-over { border-color: #888; background: #1a1a1a; }
#input-area {
    width: 100%;
    height: 100%;
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-size: 15px;
    padding: 20px;
    resize: none;
    outline: none;
}
#input-area::placeholder { color: #333; }
#file-label {
    position: absolute;
    bottom: 10px;
    right: 14px;
    font-size: 11px;
    color: #444;
}
#output-area {
    width: 80vw;
    max-width: 700px;
    margin-top: 8px;
    min-height: 0;
    max-height: 40vh;
    overflow-y: auto;
    font-size: 13px;
    color: #aaa;
    white-space: pre-wrap;
    line-height: 1.5;
    padding: 0 4px;
}
#output-area.has-content { padding: 12px; border: 1px solid #222; background: #0d0d0d; }
#spinner {
    display: none;
    margin-top: 12px;
    font-size: 12px;
    color: #555;
}
#actions-bar {
    width: 80vw;
    max-width: 700px;
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.action-btn {
    background: #1a1a1a;
    border: 1px solid #333;
    color: #ccc;
    padding: 6px 14px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
}
.action-btn:hover { border-color: #666; color: #fff; }
</style>
</head>
<body>

<div id="title">AURA</div>
<div id="drop-zone">
    <textarea id="input-area" placeholder="drop a file or type"></textarea>
    <div id="file-label"></div>
</div>
<div id="actions-bar"></div>
<div id="spinner">processing...</div>
<div id="output-area"></div>

<script>
const dropZone = document.getElementById('drop-zone');
const inputArea = document.getElementById('input-area');
const fileLabel = document.getElementById('file-label');
const actionsBar = document.getElementById('actions-bar');
const spinner = document.getElementById('spinner');
const outputArea = document.getElementById('output-area');

let currentFile = null;
let currentFilePath = null;

// Drag and drop
['dragenter','dragover'].forEach(e => {
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('drag-over'); });
});
['dragleave','drop'].forEach(e => {
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('drag-over'); });
});

dropZone.addEventListener('drop', async (ev) => {
    const files = ev.dataTransfer.files;
    if (files.length === 0) return;
    currentFile = files[0];
    fileLabel.textContent = currentFile.name;
    inputArea.value = '';
    inputArea.placeholder = currentFile.name;

    // Upload and detect
    const formData = new FormData();
    formData.append('file', currentFile);
    spinner.style.display = 'block';
    actionsBar.innerHTML = '';
    outputArea.textContent = '';
    outputArea.className = '';

    try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const data = await resp.json();
        currentFilePath = data.path;
        showActions(data.actions);
    } catch (err) {
        outputArea.textContent = 'Error: ' + err.message;
        outputArea.className = 'has-content';
    }
    spinner.style.display = 'none';
});

// Enter key on text input
inputArea.addEventListener('keydown', async (ev) => {
    if (ev.key === 'Enter' && !ev.shiftKey) {
        ev.preventDefault();
        const text = inputArea.value.trim();
        if (!text) return;

        spinner.style.display = 'block';
        actionsBar.innerHTML = '';
        outputArea.textContent = '';
        outputArea.className = '';

        try {
            const resp = await fetch('/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await resp.json();
            if (data.actions) {
                currentFilePath = data.path;
                showActions(data.actions);
            } else if (data.result) {
                showResult(data.result);
            }
        } catch (err) {
            outputArea.textContent = 'Error: ' + err.message;
            outputArea.className = 'has-content';
        }
        spinner.style.display = 'none';
    }
});

function showActions(actions) {
    actionsBar.innerHTML = '';
    actions.forEach(a => {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = a.label;
        btn.title = a.description;
        btn.onclick = () => runAction(a.key);
        actionsBar.appendChild(btn);
    });
}

async function runAction(key) {
    spinner.style.display = 'block';
    outputArea.textContent = '';
    outputArea.className = '';

    try {
        const resp = await fetch('/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentFilePath, action: key })
        });
        const data = await resp.json();
        showResult(data);
    } catch (err) {
        outputArea.textContent = 'Error: ' + err.message;
        outputArea.className = 'has-content';
    }
    spinner.style.display = 'none';
}

function showResult(data) {
    outputArea.className = 'has-content';

    // Signal decode
    if (data.decoded_word) {
        let s = data.summary || (data.decoded_word + ' = ' + (data.decoded_meaning || ''));
        outputArea.textContent = s + '\\nECL: ' + (data.ecl||0).toFixed(1) + ' / 7.0'
            + '\\nConfidence: ' + (data.confidence||'?')
            + '\\nSignal: ' + (data.signal_type||'?');
        if (data.technical_report) {
            outputArea.textContent += '\\n\\n' + data.technical_report;
        }
        return;
    }

    // Frequency inventory
    if (data.type === 'frequency_inventory') {
        let lines = data.frequencies.map(f => f.freq_hz + ' Hz  —  ' + f.count + ' hits');
        outputArea.textContent = lines.join('\\n');
        return;
    }

    // File info
    if (data.category) {
        let lines = Object.entries(data).map(([k,v]) => k + ': ' + v);
        outputArea.textContent = lines.join('\\n');
        return;
    }

    // Search/Easter egg result
    if (typeof data === 'string') {
        outputArea.textContent = data;
        return;
    }

    // Generic
    outputArea.textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>"""


class AuraHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # quiet

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path == "/upload":
            self._handle_upload()
        elif self.path == "/text":
            self._handle_text()
        elif self.path == "/run":
            self._handle_run()
        else:
            self._json_response({"error": "not found"}, 404)

    def _handle_upload(self):
        content_type = self.headers.get("Content-Type", "")
        boundary = content_type.split("boundary=")[-1].encode()
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        # Parse multipart manually (simple)
        parts = body.split(b"--" + boundary)
        for part in parts:
            if b'filename="' in part:
                # Extract filename
                header_end = part.find(b"\r\n\r\n")
                header = part[:header_end].decode(errors="replace")
                fname_start = header.find('filename="') + len('filename="')
                fname_end = header.find('"', fname_start)
                filename = header[fname_start:fname_end]

                file_data = part[header_end + 4:]
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]

                # Save
                save_path = os.path.join(UPLOAD_DIR, filename)
                with open(save_path, "wb") as f:
                    f.write(file_data)

                # Detect type and get actions
                from aura.process import detect_file_type, get_actions_for_category
                file_info = detect_file_type(save_path)
                actions = get_actions_for_category(file_info["category"], file_info.get("language"))

                self._json_response({
                    "path": save_path,
                    "info": file_info,
                    "actions": actions,
                })
                return

        self._json_response({"error": "no file found"}, 400)

    def _handle_text(self):
        body = json.loads(self._read_body())
        text = body.get("text", "").strip()

        # Easter egg: chicken butt
        if text.lower().strip().rstrip("?!. ") in ("guess what",):
            self._json_response({"result": "chicken butt"})
            return

        # Check for search/Easter egg
        if text.lower() in ("greg turner", "uncle greg", "gdt", "greg"):
            lines = [
                "Uncle Greg's Gap Detection Technology (GDT)",
                "",
                "G = |E - O|        Gap magnitude (expected vs observed)",
                "C = [L, U]         Confidence interval",
                "Classifier         Binary gap / no-gap decision",
                "S = 1 - (SumG / N) Soundness score",
                "Delta + C Engine   Iterative gap closure",
                "",
                "Thank you, Greg, for the ideas and groundwork",
                "that helped spark this project.",
                "Your thinking opened the gap. We followed it.",
            ]
            self._json_response({"result": "\n".join(lines)})
            return

        # Check if it looks like a file path
        if os.path.exists(text):
            from aura.process import detect_file_type, get_actions_for_category
            file_info = detect_file_type(text)
            actions = get_actions_for_category(file_info["category"], file_info.get("language"))
            self._json_response({
                "path": text,
                "info": file_info,
                "actions": actions,
            })
            return

        # Generic text — just echo back for now
        self._json_response({"result": text})

    def _handle_run(self):
        body = json.loads(self._read_body())
        file_path = body.get("path", "")
        action_key = body.get("action", "")

        if not file_path or not os.path.exists(file_path):
            self._json_response({"error": "file not found"}, 400)
            return

        from aura.process import run_action
        try:
            result = run_action(file_path, action_key)
            self._json_response(result)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode()

    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())


def launch(port=PORT):
    print("AuRA — http://localhost:%d" % port)
    with socketserver.TCPServer(("", port), AuraHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    launch(p)
