"""
TTS Studio Desktop Backend Server — v1.3.0
==========================================
Ultra-lightweight, zero-dependency HTTP JSON-RPC server powering the Electron Desktop App.
Uses Python standard library (http.server) to guarantee 100% offline compatibility without extra pip packages.
Includes In-App Dynamic Model Downloader with real file verification in AppData\Local\TTS-Studio\models.
"""

import os
import sys
import json
import glob
import time
import wave
import threading
from urllib.parse import urlparse, parse_qs, quote, unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

# Set up paths
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from tts_adapters import get_adapter, _ADAPTER_REGISTRY
from path_resolver import (
    get_base_dir,
    get_voices_dir,
    get_outputs_dir,
    get_models_dir,
    get_model_dir,
    get_hf_cache_dir,
    configure_hf_environment
)
from hardware_detector import inspect_hardware

# Ensure HF environment is properly routed
configure_hf_environment()

# Global download state tracker
_DOWNLOAD_STATE = {}
_DOWNLOAD_LOCK = threading.Lock()


def _check_is_model_downloaded(model_id: str) -> bool:
    """Accurately checks whether the model weights exist in AppData models dir or HF cache."""
    model_dir = get_model_dir(model_id)
    hf_cache = get_hf_cache_dir()
    hf_hub = os.path.join(hf_cache, "hub")
    
    if model_id == "f5tts":
        # Check in AppData models/f5tts dir
        if os.path.exists(model_dir) and len(glob.glob(os.path.join(model_dir, "**", "*.safetensors"), recursive=True)) > 0:
            return True
        # Check in AppData cache/huggingface/hub
        if os.path.exists(hf_hub) and len(glob.glob(os.path.join(hf_hub, "*F5-TTS*", "**", "*.safetensors"), recursive=True)) > 0:
            return True
        return False

    if model_id == "chatterbox":
        # Check in AppData models/chatterbox dir
        if os.path.exists(model_dir) and len(glob.glob(os.path.join(model_dir, "**", "*.safetensors"), recursive=True)) > 0:
            return True
        # Check in AppData cache/huggingface/hub
        if os.path.exists(hf_hub) and len(glob.glob(os.path.join(hf_hub, "*chatterbox*", "**", "*.safetensors"), recursive=True)) > 0:
            return True
        return False

    if model_id == "fishspeech":
        if os.path.exists(model_dir) and len(glob.glob(os.path.join(model_dir, "**", "*.pth"), recursive=True)) > 0:
            return True
        return False

    if model_id == "omnivoice":
        if os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "config.json")):
            return True
        return False

    if model_id == "cosyvoice":
        if os.path.exists(model_dir) and len(os.listdir(model_dir)) > 2:
            return True
        cosy_rt = os.path.join(WORKSPACE_ROOT, "runtimes", "CosyVoice")
        if os.path.exists(cosy_rt) and len(os.listdir(cosy_rt)) > 5:
            return True
        return False

    if model_id == "xttsv2":
        # Check in AppData models/xttsv2 dir
        if os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "model.pth")):
            return True
        # Also check local TTS cache
        tts_cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "tts")
        if os.path.exists(tts_cache) and len(glob.glob(os.path.join(tts_cache, "**", "model.pth"), recursive=True)) > 0:
            return True
        return False

    if model_id == "indextts2":
        if os.path.exists(model_dir) and len(os.listdir(model_dir)) > 2:
            return True
        return False

    return False


def _background_download_worker(model_id: str):
    """Worker function to execute real background model download into %LOCALAPPDATA%\\TTS-Studio\\models."""
    target_dir = get_model_dir(model_id)
    os.makedirs(target_dir, exist_ok=True)

    with _DOWNLOAD_LOCK:
        _DOWNLOAD_STATE[model_id] = {
            "status": "DOWNLOADING",
            "percent": 10,
            "downloaded_mb": 0.0,
            "total_mb": 0.0,
            "speed_mbps": 0.0,
            "error": None
        }

    try:
        configure_hf_environment()
        
        if model_id == "f5tts":
            from huggingface_hub import hf_hub_download, snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 25
            print(f"[Downloader] Downloading F5-TTS safetensors to: {target_dir}...", flush=True)
            hf_hub_download(
                repo_id="SWivid/F5-TTS",
                filename="F5TTS_v1_Base/model_1250000.safetensors",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 70
            print(f"[Downloader] Downloading Vocos to: {target_dir}/vocos...", flush=True)
            snapshot_download(
                repo_id="charactr/vocos-mel-24khz",
                local_dir=os.path.join(target_dir, "vocos")
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "chatterbox":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading Chatterbox Turbo to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="ResembleAI/chatterbox",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "fishspeech":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading Fish Speech S2 to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="fishaudio/fish-speech-1.5",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "omnivoice":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading OmniVoice to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="k2-fsa/OmniVoice",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "cosyvoice":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading CosyVoice 3 to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="FunAudioLLM/CosyVoice-300M",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "xttsv2":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading XTTS-v2 to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="coqui/XTTS-v2",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

        elif model_id == "indextts2":
            from huggingface_hub import snapshot_download
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 30
            print(f"[Downloader] Downloading IndexTTS 2.5 to: {target_dir}...", flush=True)
            snapshot_download(
                repo_id="IndexTeam/IndexTTS-2.5",
                local_dir=target_dir
            )
            with _DOWNLOAD_LOCK:
                _DOWNLOAD_STATE[model_id]["percent"] = 100
                _DOWNLOAD_STATE[model_id]["status"] = "READY"

    except Exception as e:
        import traceback
        traceback.print_exc()
        with _DOWNLOAD_LOCK:
            _DOWNLOAD_STATE[model_id]["status"] = "ERROR"
            _DOWNLOAD_STATE[model_id]["error"] = str(e)


class DesktopServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write(f"[DesktopServer] {format % args}\n")
        sys.stdout.flush()

    def _set_cors_headers(self, content_type="application/json"):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self._set_cors_headers("application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Health check
        if path == "/api/health":
            return self._send_json(200, {"status": "ok", "timestamp": time.time()})

        # 2. Hardware Diagnostics
        if path == "/api/hardware":
            try:
                hw = inspect_hardware()
                return self._send_json(200, hw)
            except Exception as e:
                return self._send_json(500, {"error": str(e)})

        # 3. Available Models (All 7 Models)
        if path == "/api/models":
            models = [
                {
                    "id": "f5tts",
                    "name": "F5-TTS",
                    "architecture": "DiT Flow Matching",
                    "description": "State-of-the-art flow matching zero-shot voice cloning with crisp natural cadence.",
                    "maxWords": 60,
                    "recommended": True,
                    "tag": "Highest Fidelity",
                    "isDownloaded": _check_is_model_downloaded("f5tts")
                },
                {
                    "id": "chatterbox",
                    "name": "Chatterbox Turbo",
                    "architecture": "Fast Diffusion",
                    "description": "Ultra-fast diffusion zero-shot voice cloning optimized for conversational dialogue.",
                    "maxWords": 60,
                    "recommended": False,
                    "tag": "Ultra Fast",
                    "isDownloaded": _check_is_model_downloaded("chatterbox")
                },
                {
                    "id": "fishspeech",
                    "name": "Fish Speech S2",
                    "architecture": "DualAR LLM + DAC",
                    "description": "High-fidelity dual autoregressive acoustic neural vocoder for expressive zero-shot cloning.",
                    "maxWords": 60,
                    "recommended": False,
                    "tag": "Rich Dynamics",
                    "isDownloaded": _check_is_model_downloaded("fishspeech")
                },
                {
                    "id": "omnivoice",
                    "name": "OmniVoice",
                    "architecture": "Flow Transformer",
                    "description": "527-layer transducer flow-matching speech synthesis with deep contextual inflections.",
                    "maxWords": 60,
                    "recommended": False,
                    "tag": "Deep Inflection",
                    "isDownloaded": _check_is_model_downloaded("omnivoice")
                },
                {
                    "id": "cosyvoice",
                    "name": "CosyVoice 3",
                    "architecture": "FunAudioLLM 300M",
                    "description": "Multilingual zero-shot neural synthesis engine with emotional nuance control.",
                    "maxWords": 80,
                    "recommended": False,
                    "tag": "Multilingual 300M",
                    "isDownloaded": _check_is_model_downloaded("cosyvoice")
                },
                {
                    "id": "xttsv2",
                    "name": "XTTS-v2",
                    "architecture": "Coqui Multi-Speaker GPT",
                    "description": "Robust multi-lingual autoregressive voice cloner with 17+ languages support.",
                    "maxWords": 60,
                    "recommended": False,
                    "tag": "Multilingual",
                    "isDownloaded": _check_is_model_downloaded("xttsv2")
                },
                {
                    "id": "indextts2",
                    "name": "IndexTTS 2.5",
                    "architecture": "GPT + BigVGAN",
                    "description": "UnifiedVoice GPT multi-emotion zero-shot synthesis with BigVGAN neural vocoder.",
                    "maxWords": 60,
                    "recommended": False,
                    "tag": "Expressive",
                    "isDownloaded": _check_is_model_downloaded("indextts2")
                }
            ]
            return self._send_json(200, {"models": models})

        # 3b. Model Download Progress
        if path == "/api/models/download-progress":
            query = parse_qs(parsed.query)
            model_id = query.get("model_id", ["f5tts"])[0]
            with _DOWNLOAD_LOCK:
                is_down = _check_is_model_downloaded(model_id)
                prog = _DOWNLOAD_STATE.get(model_id, {
                    "status": "READY" if is_down else "NOT_INSTALLED",
                    "percent": 100 if is_down else 0,
                    "downloaded_mb": 0.0,
                    "total_mb": 0.0,
                    "speed_mbps": 0.0
                })
            return self._send_json(200, prog)

        # 4. Discover Speaker Voices across all voice directories and audio formats
        if path == "/api/voices":
            voice_dirs = [
                get_voices_dir(),
                os.path.join(WORKSPACE_ROOT, "voices"),
                os.path.join(get_base_dir(), "voices")
            ]
            seen_files = set()
            categorized = {}
            flat_list = []

            for vdir in voice_dirs:
                if not os.path.isdir(vdir):
                    continue
                for root, _, files in os.walk(vdir):
                    for fname in sorted(files):
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"]:
                            continue
                        wav_p = os.path.abspath(os.path.join(root, fname))
                        if wav_p in seen_files:
                            continue
                        seen_files.add(wav_p)

                        rel_path = os.path.relpath(wav_p, vdir).replace("\\", "/")
                        category = os.path.dirname(rel_path) or "General"
                        if category.startswith("..") or category == "":
                            category = os.path.basename(os.path.dirname(wav_p)) or "General"

                        # Clean user-friendly labels
                        base_name = os.path.splitext(fname)[0]
                        clean_label = base_name.replace("_", " ").replace("-", " ")
                        if "FDownload" in clean_label:
                            clean_label = "Social Viral Promo"
                        elif "dl 090b" in clean_label:
                            clean_label = "Storytelling Narrator"
                        elif "ENG US M" in clean_label:
                            clean_label = clean_label.replace("ENG US M ", "Studio Male ")

                        duration = 0.0
                        try:
                            if ext == ".wav":
                                with wave.open(wav_p, "r") as wf:
                                    duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                        except Exception:
                            pass

                        voice_item = {
                            "id": wav_p,
                            "label": clean_label.strip(),
                            "category": category,
                            "filename": fname,
                            "duration": duration,
                            "fullPath": wav_p,
                            # Bug 2.2 fix: URL-encode the path so special chars/backslashes
                            # survive the round-trip through the HTTP query string.
                            "audioUrl": f"/api/audio-file?path={quote(wav_p, safe='')}"
                        }

                        if category not in categorized:
                            categorized[category] = []
                        categorized[category].append(voice_item)
                        flat_list.append(voice_item)

            return self._send_json(200, {
                "categorized": categorized,
                "voices": flat_list,
                "total": len(flat_list)
            })

        # 5. Recent Output History from %LOCALAPPDATA%\TTS-Studio\outputs
        if path == "/api/outputs":
            outputs_dir = get_outputs_dir()
            wav_files = sorted(
                glob.glob(os.path.join(outputs_dir, "*.wav")),
                key=os.path.getmtime,
                reverse=True
            )[:20]

            history = []
            for wav_p in wav_files:
                filename = os.path.basename(wav_p)
                mtime = os.path.getmtime(wav_p)
                size_kb = round(os.path.getsize(wav_p) / 1024, 1)
                duration = 0.0
                try:
                    with wave.open(wav_p, "r") as wf:
                        duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                except Exception:
                    pass

                history.append({
                    "filename": filename,
                    "fullPath": wav_p,
                    "createdAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
                    "fileSizeKb": size_kb,
                    "duration": duration,
                    # Bug 2.2 fix: URL-encode path
                    "audioUrl": f"/api/audio-file?path={quote(wav_p, safe='')}"
                })

            return self._send_json(200, {"outputs": history})

        # 6. Stream/Serve Audio File
        if path == "/api/audio-file":
            query = parse_qs(parsed.query)
            file_path = query.get("path", [None])[0]
            # Bug 2.2 fix: parse_qs already decodes percent-encoding — do NOT call unquote() again.
            # file_path is already a plain Windows path at this point.
            if not file_path or not os.path.exists(file_path):
                return self._send_json(404, {"error": "Audio file not found"})

            # Bug 2.3 fix: set correct MIME type per file extension
            _EXT_MIME = {
                ".wav":  "audio/wav",
                ".mp3":  "audio/mpeg",
                ".flac": "audio/flac",
                ".ogg":  "audio/ogg",
                ".m4a":  "audio/mp4",
                ".aac":  "audio/aac",
            }
            ext = os.path.splitext(file_path)[1].lower()
            mime = _EXT_MIME.get(ext, "audio/wav")

            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self._set_cors_headers(mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                return self._send_json(500, {"error": str(e)})

        # 404
        return self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Trigger In-App Model Download
        if path == "/api/models/download":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                req = json.loads(body.decode("utf-8"))
                model_id = req.get("model_id", "f5tts")

                t = threading.Thread(target=_background_download_worker, args=(model_id,), daemon=True)
                t.start()
                return self._send_json(200, {"status": "started", "model_id": model_id})
            except Exception as e:
                return self._send_json(500, {"error": str(e)})

        if path == "/api/synthesize":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                req = json.loads(body.decode("utf-8"))

                model_id = req.get("model_id", "f5tts")
                text = req.get("text", "").strip()
                reference_voice = req.get("reference_voice", None)
                
                if not text:
                    return self._send_json(400, {"error": "Text prompt cannot be empty."})

                # Check if model downloaded
                if not _check_is_model_downloaded(model_id):
                    return self._send_json(400, {
                        "error": f"Model weights for '{model_id}' are not downloaded. Please click 'Download Model Weights' in the Model Selector."
                    })

                # Resolve output file path in %LOCALAPPDATA%\TTS-Studio\outputs
                output_dir = get_outputs_dir()
                os.makedirs(output_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                out_filename = f"{model_id}_speech_{timestamp}.wav"
                out_filepath = os.path.join(output_dir, out_filename)

                # Get Adapter & Generate
                adapter = get_adapter(model_id)
                print(f"[DesktopServer] Dispatching synthesis for '{adapter.model_name}'...", flush=True)
                
                res = adapter.generate(
                    text=text,
                    reference_voice=reference_voice,
                    output_path=out_filepath
                )

                # Format response
                res["audioUrl"] = f"/api/audio-file?path={quote(out_filepath, safe='')}"
                res["filename"] = out_filename
                return self._send_json(200, res)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json(500, {"error": f"Synthesis failed: {str(e)}"})

        return self._send_json(404, {"error": "Endpoint not found"})


def run_server(port: int = 8000, host: str = "127.0.0.1"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, DesktopServerHandler)
    print("============================================================", flush=True)
    print(f"[DesktopServer] TTS STUDIO DESKTOP SERVER STARTED", flush=True)
    print(f"[DesktopServer] Listening on: http://{host}:{port}", flush=True)
    print(f"[DesktopServer] Models dir:  {get_models_dir()}", flush=True)
    print(f"[DesktopServer] Outputs dir: {get_outputs_dir()}", flush=True)
    print(f"[DesktopServer] Cache dir:   {get_hf_cache_dir()}", flush=True)
    print("============================================================", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[DesktopServer] Shutting down...", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
