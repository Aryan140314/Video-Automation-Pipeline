import os
import sys
import unittest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import (
    get_base_dir,
    get_models_dir,
    get_model_dir,
    get_voices_dir,
    get_outputs_dir,
    get_logs_dir,
    get_cache_dir,
    get_config_dir,
    get_runtimes_dir,
    get_isolated_venv_python
)

class TestPathResolver(unittest.TestCase):
    def test_dev_base_dir(self):
        os.environ.pop("TTS_STUDIO_PROD", None)
        base = get_base_dir()
        self.assertTrue(os.path.isabs(base))
        self.assertEqual(os.path.abspath(base), os.path.abspath(WORKSPACE_ROOT))

    def test_prod_base_dir(self):
        os.environ["TTS_STUDIO_PROD"] = "1"
        base = get_base_dir()
        self.assertIn("TTS-Studio", base)
        os.environ.pop("TTS_STUDIO_PROD", None)

    def test_subdirectories_created(self):
        self.assertTrue(os.path.exists(get_models_dir()))
        self.assertTrue(os.path.exists(get_voices_dir()))
        self.assertTrue(os.path.exists(get_outputs_dir()))
        self.assertTrue(os.path.exists(get_logs_dir()))
        self.assertTrue(os.path.exists(get_cache_dir()))
        self.assertTrue(os.path.exists(get_config_dir()))
        self.assertTrue(os.path.exists(get_runtimes_dir()))

    def test_model_dir(self):
        f5_dir = get_model_dir("F5-TTS")
        self.assertTrue(f5_dir.endswith("f5tts"))
        self.assertTrue(os.path.exists(f5_dir))

    def test_isolated_venv_path(self):
        py_path = get_isolated_venv_python("xttsv2")
        self.assertIn(".venv_xttsv2", py_path)

if __name__ == "__main__":
    unittest.main()
