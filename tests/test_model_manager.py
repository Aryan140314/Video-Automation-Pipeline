import os
import sys
import unittest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from model_manager import get_model_manager
from backend.main import app

class TestModelManager(unittest.TestCase):
    def setUp(self):
        self.mm = get_model_manager()
        self.client = TestClient(app)

    def test_manifest_contains_seven_models(self):
        manifest = self.mm.get_manifest()
        self.assertEqual(len(manifest), 7)
        self.assertIn("f5tts", manifest)
        self.assertIn("chatterbox", manifest)
        self.assertIn("fishspeech", manifest)
        self.assertIn("omnivoice", manifest)
        self.assertIn("cosyvoice", manifest)
        self.assertIn("xttsv2", manifest)
        self.assertIn("indextts2", manifest)

    def test_model_info(self):
        info = self.mm.get_model_info("F5-TTS")
        self.assertIsNotNone(info)
        self.assertEqual(info["id"], "f5tts")

    def test_model_status_query(self):
        status_f5 = self.mm.get_model_status("f5tts")
        self.assertIn(status_f5, ["NOT_INSTALLED", "READY", "DOWNLOADING", "MODEL_LOAD_FAILED"])

        status_fish = self.mm.get_model_status("fishspeech")
        self.assertEqual(status_fish, "DEPENDENCY_MISSING")

    def test_model_status_api_endpoint(self):
        res = self.client.get("/api/models/f5tts/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["model_id"], "f5tts")
        self.assertIn("status", data)

    def test_model_verify_api_endpoint(self):
        res = self.client.post("/api/models/f5tts/verify")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["model_id"], "f5tts")
        self.assertIn("valid", data)

    def test_model_unload_api_endpoint(self):
        res = self.client.post("/api/models/f5tts/unload")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "unloaded")

if __name__ == "__main__":
    unittest.main()
