"""
TTS Studio Local Backend FastAPI Application Server
==================================================
Provides HTTP REST endpoints for the Electron Desktop UI, connecting user commands
to the existing TTS Model Adapters, original reference voice assets, Model Manager, Voice Manager,
Generation Engine, and hardware engine.
"""

import os
import sys
import glob
import time
import sysconfig
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# Add scripts directory to path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import (
    get_base_dir,
    get_voices_dir,
    get_outputs_dir,
    get_model_dir
)
from hardware_detector import inspect_hardware
from tts_adapters import get_adapter
from model_manager import get_model_manager
from voice_manager import get_voice_manager
from generation_engine import get_generation_engine

app = FastAPI(
    title="TTS Studio Local Backend",
    version="1.0.0",
    description="Local inference server for TTS Studio Windows Desktop Application"
)

# Enable CORS for local Electron renderer process
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def resolve_reference_voice(category_or_path: str | None) -> str | None:
    """
    Resolves a voice category name (e.g. 'Narration') or path to an absolute WAV file.
    """
    if not category_or_path:
        return None
    return get_voice_manager().resolve_category_wav(category_or_path)

# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

from backend.schemas import (
    HealthResponse,
    HardwareReport,
    ModelCard,
    ModelsListResponse,
    VoiceCard,
    VoicesListResponse,
    CategoriesListResponse,
    GenerationRequest,
    GenerationResponse,
    DiagnosticsResponse,
    ModelVerificationResponse,
    SmokeTestRequest,
    SmokeTestResponse,
    ModelUnloadResponse,
    ModelDeleteResponse
)

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse()

@app.get("/api/hardware", response_model=HardwareReport)
def get_hardware_report():
    return inspect_hardware()

@app.get("/api/models", response_model=ModelsListResponse)
def get_models_list():
    hw = inspect_hardware()
    mm = get_model_manager()
    manifest = mm.get_manifest()
    models_list = []
    
    for m_id, meta in manifest.items():
        status_str = mm.get_model_status(m_id)

        models_list.append(ModelCard(
            id=m_id,
            name=meta["name"],
            status=status_str,
            device=hw["recommended_device"] if meta.get("gpu_supported", True) else "CPU",
            weights_size_gb=meta.get("expected_size_gb", 1.0),
            gpu_supported=meta.get("gpu_supported", True),
            cpu_supported=meta.get("cpu_supported", True),
            runtime=meta.get("runtime", "main"),
            description=meta.get("description", "")
        ))

    return ModelsListResponse(count=len(models_list), models=models_list)

@app.get("/api/models/{model_id}/status")
def get_model_status(model_id: str):
    mm = get_model_manager()
    status_str = mm.get_model_status(model_id)
    return {"model_id": model_id, "status": status_str}

@app.post("/api/models/{model_id}/verify", response_model=ModelVerificationResponse)
def verify_model_endpoint(model_id: str):
    mm = get_model_manager()
    res = mm.verify_model(model_id)
    return ModelVerificationResponse(
        model_id=model_id,
        valid=res["valid"],
        reason=res["reason"]
    )

@app.post("/api/models/{model_id}/test", response_model=SmokeTestResponse)
def smoke_test_model_endpoint(model_id: str, req: SmokeTestRequest = SmokeTestRequest()):
    mm = get_model_manager()
    ref_wav = resolve_reference_voice(req.voice_category) if req.voice_category else None
    res = mm.smoke_test_model(model_id, reference_voice=ref_wav)
    return SmokeTestResponse(
        model_id=model_id,
        success=res["success"],
        metrics=res.get("metrics"),
        error=res.get("error")
    )

@app.post("/api/models/{model_id}/unload", response_model=ModelUnloadResponse)
def unload_model_endpoint(model_id: str):
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return ModelUnloadResponse(model_id=model_id, status="unloaded", vram_freed=True)

_DOWNLOAD_PROGRESS = {}

@app.post("/api/models/{model_id}/download")
def download_model_endpoint(model_id: str, background_tasks: BackgroundTasks):
    mm = get_model_manager()
    manifest = mm.get_manifest()
    if model_id not in manifest:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in manifest.")

    def _do_download():
        _DOWNLOAD_PROGRESS[model_id] = {
            "status": "downloading",
            "percent": 0.0,
            "speed_mbps": 0.0,
            "downloaded_mb": 0.0,
            "total_mb": round(manifest[model_id].get("expected_size_gb", 1.0) * 1024.0, 1)
        }

        def _cb(data):
            _DOWNLOAD_PROGRESS[model_id] = {
                "status": "downloading",
                "percent": data.get("percent", 0.0),
                "speed_mbps": data.get("speed_mbps", 0.0),
                "downloaded_mb": round(data.get("downloaded_bytes", 0) / (1024 * 1024), 1),
                "total_mb": round(data.get("total_bytes", 0) / (1024 * 1024), 1)
            }

        try:
            ok = mm.download_model(model_id, progress_callback=_cb)
            if ok:
                _DOWNLOAD_PROGRESS[model_id] = {"status": "completed", "percent": 100.0, "speed_mbps": 0.0}
            else:
                _DOWNLOAD_PROGRESS[model_id] = {"status": "failed", "error": "Download failed or interrupted"}
        except Exception as e:
            _DOWNLOAD_PROGRESS[model_id] = {"status": "failed", "error": str(e)}

    background_tasks.add_task(_do_download)
    return {"status": "started", "model_id": model_id}


@app.get("/api/models/{model_id}/download/progress")
def get_download_progress(model_id: str):
    return _DOWNLOAD_PROGRESS.get(model_id, {"status": "idle", "percent": 0.0, "speed_mbps": 0.0})


@app.delete("/api/models/{model_id}", response_model=ModelDeleteResponse)
def delete_model_endpoint(model_id: str):
    mm = get_model_manager()
    ok = mm.delete_model(model_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete model weights.")
    return ModelDeleteResponse(model_id=model_id, status="deleted")

@app.get("/api/voices", response_model=VoicesListResponse)
def get_voices_catalog():
    vm = get_voice_manager()
    indexed = vm.index_voices()
    
    voices_list = [
        VoiceCard(
            category=item["category"],
            filename=item["filename"],
            relative_path=item["relative_path"],
            duration_sec=item["duration_sec"],
            sample_rate=item["sample_rate"],
            channels=item["channels"],
            bit_depth=item["bit_depth"],
            file_size_bytes=item["file_size_bytes"],
            file_size_mb=item["file_size_mb"],
            format=item["format"]
        )
        for item in indexed
    ]

    return VoicesListResponse(count=len(voices_list), voices=voices_list)

@app.get("/api/voices/categories", response_model=CategoriesListResponse)
def get_voice_categories():
    vm = get_voice_manager()
    categories = vm.get_categories()
    return CategoriesListResponse(count=len(categories), categories=categories)

@app.get("/api/voices/audio/{category}")
def stream_voice_audio(category: str):
    vm = get_voice_manager()
    wav_path = vm.resolve_category_wav(category)
    if not wav_path or not os.path.exists(wav_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice audio for category or file '{category}' not found."
        )
    return FileResponse(path=wav_path, media_type="audio/wav", filename=os.path.basename(wav_path))

@app.get("/api/outputs/audio/{filename}")
def stream_output_audio(filename: str):
    outputs_dir = get_outputs_dir()
    wav_path = os.path.join(outputs_dir, filename)
    if not os.path.exists(wav_path):
        # Also check relative to workspace
        wav_path = os.path.join(WORKSPACE_ROOT, "outputs", filename)
    if not os.path.exists(wav_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated output audio file '{filename}' not found."
        )
    return FileResponse(path=wav_path, media_type="audio/wav", filename=filename)

@app.post("/api/generate", response_model=GenerationResponse)
def generate_speech(req: GenerationRequest):
    engine = get_generation_engine()
    result = engine.generate(
        text=req.text,
        model_id=req.model_id,
        voice_category=req.voice_category,
        output_path=req.output_path,
        pitch=req.pitch or 0.0,
        speed=req.speed or 1.0,
        trim_sec=req.trim_sec
    )

    if result.get("error") in ["VOICE_NOT_FOUND"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", f"Voice category '{req.voice_category}' not found.")
        )

    is_success = result.get("status") == "success" and result.get("backend") not in ["DEPENDENCY_MISSING", "none", "f5tts-error", "chatterbox-error"]

    return GenerationResponse(
        status="success" if is_success else "error",
        model=result.get("model", req.model_id),
        model_name=result.get("model_name", req.model_id),
        backend=result.get("backend", "none"),
        cloning_active=result.get("cloning_active", False),
        gen_time=result.get("gen_time", 0.0),
        duration=result.get("duration", 0.0),
        rtf=result.get("rtf", 0.0),
        file_size_kb=result.get("file_size_kb", 0.0),
        output_path=result.get("output_path", ""),
        device=result.get("device", "cpu"),
        error=result.get("error") or (result.get("backend") if not is_success else None)
    )

@app.get("/api/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics():
    import torch
    hw = inspect_hardware()
    models_res = get_models_list()
    voices_res = get_voices_catalog()

    return DiagnosticsResponse(
        hardware=HardwareReport(**hw),
        models=models_res.models,
        voice_count=voices_res.count,
        base_dir=get_base_dir(),
        outputs_dir=get_outputs_dir(),
        python_version=sys.version.split()[0],
        torch_version=torch.__version__
    )

@app.get("/api/benchmark")
def get_benchmark_history():
    """
    Returns historical benchmark metrics from outputs/synthesis_benchmark.csv.
    """
    import csv
    csv_path = os.path.join(get_outputs_dir(), "synthesis_benchmark.csv")
    if not os.path.exists(csv_path):
        return {"count": 0, "benchmarks": []}

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to read benchmark log: {err}")

    return {"count": len(rows), "benchmarks": rows}


@app.post("/api/regression-test")
def trigger_golden_regression_test(background_tasks: BackgroundTasks):
    """
    Triggers an automated golden regression pass across all 7 zero-shot models.
    """
    from golden_regression_test import run_golden_regression
    
    def _run():
        run_golden_regression()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Golden regression test pass initiated in background."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

