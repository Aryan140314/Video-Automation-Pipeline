import os
import sys
import unittest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from backend.main import app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "TTS Studio Local Backend")

    def test_hardware_endpoint(self):
        res = self.client.get("/api/hardware")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("gpu_present", data)
        self.assertIn("recommended_device", data)
        self.assertIn("vram_total_gb", data)

    def test_models_endpoint(self):
        res = self.client.get("/api/models")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 7)
        model_ids = [m["id"] for m in data["models"]]
        self.assertIn("f5tts", model_ids)
        self.assertIn("chatterbox", model_ids)
        self.assertIn("xttsv2", model_ids)

    def test_voices_endpoint(self):
        res = self.client.get("/api/voices")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["count"], 7)
        categories = [v["category"] for v in data["voices"]]
        self.assertIn("Narration", categories)
        self.assertIn("Announcement", categories)
        self.assertIn("Audiobook", categories)

    def test_diagnostics_endpoint(self):
        res = self.client.get("/api/diagnostics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("hardware", data)
        self.assertIn("models", data)
        self.assertIn("python_version", data)

    def test_generate_validation_error(self):
        # Voice category that doesn't exist
        payload = {
            "text": "Testing synthesis endpoint",
            "model_id": "f5tts",
            "voice_category": "NonExistentVoiceCategory123"
        }
        res = self.client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
