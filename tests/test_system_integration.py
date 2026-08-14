import os
import sys
import unittest
import wave
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import get_base_dir, get_outputs_dir
from hardware_detector import inspect_hardware
from model_manager import get_model_manager
from voice_manager import get_voice_manager
from generation_engine import get_generation_engine
from backend.main import app

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.hw = inspect_hardware()
        self.mm = get_model_manager()
        self.vm = get_voice_manager()
        self.engine = get_generation_engine()

    def test_full_system_lifecycle_health(self):
        # 1. Probe Health Endpoint
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_full_system_hardware_discovery(self):
        # 2. Probe Hardware Discovery
        res = self.client.get("/api/hardware")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommended_device", data)
        self.assertIn(data["recommended_device"], ["CUDA", "CPU"])

    def test_full_system_models_registry(self):
        # 3. Probe Models Registry
        res = self.client.get("/api/models")
        self.assertEqual(res.status_code, 200)
        models = res.json()["models"]
        self.assertEqual(len(models), 7)

    def test_full_system_voices_catalog(self):
        # 4. Probe Voices Catalog
        res = self.client.get("/api/voices")
        self.assertEqual(res.status_code, 200)
        voices = res.json()["voices"]
        self.assertGreaterEqual(len(voices), 7)

    def test_full_system_generation_flow_f5tts(self):
        # 5. Execute Generation Request via API for F5-TTS
        payload = {
            "text": "System integration testing for TTS Studio backend pipeline.",
            "model_id": "f5tts",
            "voice_category": "Narration",
            "speed": 1.1,
            "pitch": 0
        }
        res = self.client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)

    def test_full_system_no_silent_fallback_enforcement(self):
        # 6. Verify No Silent Fallback for Missing Model
        payload = {
            "text": "Testing uninstalled model error reporting.",
            "model_id": "omnivoice"
        }
        res = self.client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["backend"], "DEPENDENCY_MISSING")

    def test_full_system_diagnostics_report(self):
        # 7. Probe System Diagnostics
        res = self.client.get("/api/diagnostics")
        self.assertEqual(res.status_code, 200)
        diag = res.json()
        self.assertIn("hardware", diag)
        self.assertIn("models", diag)
        self.assertGreaterEqual(diag["voice_count"], 7)

if __name__ == "__main__":
    unittest.main()
