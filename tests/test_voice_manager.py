import os
import sys
import unittest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from voice_manager import get_voice_manager
from backend.main import app

class TestVoiceManager(unittest.TestCase):
    def setUp(self):
        self.vm = get_voice_manager()
        self.client = TestClient(app)

    def test_voice_indexing_count(self):
        indexed = self.vm.index_voices(force_refresh=True)
        self.assertGreaterEqual(len(indexed), 7)

    def test_voice_metadata_properties(self):
        indexed = self.vm.index_voices()
        first = indexed[0]
        self.assertIn("category", first)
        self.assertIn("filename", first)
        self.assertIn("duration_sec", first)
        self.assertGreater(first["duration_sec"], 0.0)
        self.assertGreater(first["sample_rate"], 0)
        self.assertGreater(first["channels"], 0)

    def test_category_listing(self):
        cats = self.vm.get_categories()
        self.assertIn("Narration", cats)
        self.assertIn("Announcement", cats)

    def test_category_resolution(self):
        narration_wav = self.vm.resolve_category_wav("Narration")
        self.assertIsNotNone(narration_wav)
        self.assertTrue(os.path.exists(narration_wav))
        self.assertTrue(narration_wav.endswith(".wav"))

    def test_categories_api_endpoint(self):
        res = self.client.get("/api/voices/categories")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["count"], 7)
        self.assertIn("Narration", data["categories"])

    def test_audio_stream_api_endpoint(self):
        res = self.client.get("/api/voices/audio/Narration")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "audio/wav")
        self.assertGreater(len(res.content), 1000)

if __name__ == "__main__":
    unittest.main()
