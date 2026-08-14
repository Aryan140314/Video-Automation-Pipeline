"""
TTS Studio — Automated Synthesis Benchmark System
=================================================
Executes performance benchmark passes for zero-shot TTS models
and logs results to E:\\TTS\\outputs\\synthesis_benchmark.csv.
"""

import os
import sys
import csv
import time
import wave
import json
from datetime import datetime
import torch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")
CSV_PATH = os.path.join(OUTPUTS_DIR, "synthesis_benchmark.csv")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from tts_adapters import get_adapter

CSV_HEADERS = [
    "timestamp",
    "model_id",
    "model_name",
    "backend",
    "cloning_active",
    "gen_time_s",
    "audio_duration_s",
    "rtf",
    "file_size_kb",
    "device",
    "status",
    "output_path"
]

def init_benchmark_csv():
    """Ensure outputs/synthesis_benchmark.csv exists with headers."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def log_synthesis_result(result_dict: dict) -> str:
    """Appends a synthesis benchmark result dict to CSV."""
    init_benchmark_csv()

    timestamp = datetime.now().isoformat()
    model_id = result_dict.get("model", result_dict.get("model_id", "unknown"))
    model_name = result_dict.get("model_name", model_id)
    backend = result_dict.get("backend", "unknown")
    cloning_active = result_dict.get("cloning_active", True)
    gen_time = round(float(result_dict.get("gen_time", result_dict.get("wall_time", 0.0))), 3)
    duration = round(float(result_dict.get("duration", 0.0)), 3)
    rtf = round(float(result_dict.get("rtf", gen_time / max(duration, 0.1))), 4)
    file_size_kb = round(float(result_dict.get("file_size_kb", 0.0)), 2)
    device = result_dict.get("device", "CUDA" if torch.cuda.is_available() else "CPU")
    status = "SUCCESS" if ("error" not in result_dict and file_size_kb > 1.0) else "FAILED"
    output_path = result_dict.get("output_path", "")

    row = [
        timestamp,
        model_id,
        model_name,
        backend,
        cloning_active,
        gen_time,
        duration,
        rtf,
        file_size_kb,
        device,
        status,
        output_path
    ]

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    return CSV_PATH

def run_benchmark(model_id: str, text: str, ref_wav: str) -> dict:
    """Executes a single synthesis benchmark run and logs it."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    out_name = f"benchmark_{model_id}_{int(time.time())}.wav"
    output_path = os.path.join(OUTPUTS_DIR, out_name)

    adapter = get_adapter(model_id)
    t0 = time.time()
    res = adapter.generate(text=text, reference_voice=ref_wav, output_path=output_path)
    t1 = time.time()

    if "gen_time" not in res:
        res["gen_time"] = round(t1 - t0, 3)

    if os.path.exists(output_path):
        res["file_size_kb"] = round(os.path.getsize(output_path) / 1024.0, 2)
        if "duration" not in res or res["duration"] == 0:
            try:
                with wave.open(output_path, "r") as wf:
                    res["duration"] = round(wf.getnframes() / float(wf.getframerate()), 2)
            except Exception:
                res["duration"] = 0.0

    res["rtf"] = round(res["gen_time"] / max(res.get("duration", 0.1), 0.1), 4)
    res["output_path"] = output_path
    log_synthesis_result(res)
    return res

if __name__ == "__main__":
    init_benchmark_csv()
    print(f"[Benchmark System] CSV logging initialized at: {CSV_PATH}")
