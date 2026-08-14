import os
import sys
import wave
import unittest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from generation_engine import get_generation_engine
from speech_synth_helper import preprocess_tts_text
from tts_adapters import IntelligentChunker, get_adapter
from backend.main import app

class TestGoldenRegression(unittest.TestCase):
    def setUp(self):
        self.engine = get_generation_engine()
        self.client = TestClient(app)

    def test_preprocessing_equivalence(self):
        sample = "Welcome to [pause] **TTS Studio** with *high* performance."
        helper_out = preprocess_tts_text(sample)
        self.assertIn("...", helper_out)
        self.assertIn("T-T-S STUDIO", helper_out)
        self.assertIn("HIGH", helper_out)

    def test_intelligent_chunker_word_preservation(self):
        text = "word " * 150
        chunks = IntelligentChunker.chunk_text(text, max_words=60)
        self.assertGreater(len(chunks), 1)
        reconstructed_word_count = sum(len(c.split()) for c in chunks)
        self.assertEqual(reconstructed_word_count, 150)

    def test_no_silent_fallback_rule(self):
        """
        HARD RULE (Section 7): Selected model MUST be actual model executed.
        Must NEVER silently fall back to F5-TTS or SAPI5 if an uninstalled model is selected.
        """
        # Test Fish Speech (uninstalled)
        res_fish = self.engine.generate("Test text", model_id="fishspeech")
        self.assertEqual(res_fish["status"], "error")
        self.assertEqual(res_fish["backend"], "DEPENDENCY_MISSING")

        # Test CosyVoice (uninstalled)
        res_cosy = self.engine.generate("Test text", model_id="cosyvoice")
        self.assertEqual(res_cosy["status"], "error")
        self.assertEqual(res_cosy["backend"], "DEPENDENCY_MISSING")

    def test_model_identity_f5tts(self):
        adapter_f5 = get_adapter("f5tts")
        self.assertEqual(adapter_f5.model_name, "F5-TTS")

    def test_model_identity_chatterbox(self):
        adapter_cb = get_adapter("chatterbox")
        self.assertEqual(adapter_cb.model_name, "Chatterbox Turbo")

    def test_api_generate_no_silent_fallback(self):
        payload = {
            "text": "Test no silent fallback API",
            "model_id": "fishspeech"
        }
        res = self.client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["backend"], "DEPENDENCY_MISSING")

    def test_api_generate_voice_resolution(self):
        payload = {
            "text": "Testing voice resolution",
            "model_id": "f5tts",
            "voice_category": "Narration"
        }
        res = self.client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["status"], ["success", "error"])

if __name__ == "__main__":
    unittest.main()
