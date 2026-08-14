import os
import sys
import unittest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from hardware_detector import inspect_hardware, get_nvidia_driver_version

class TestHardwareDetector(unittest.TestCase):
    def test_inspect_hardware_structure(self):
        report = inspect_hardware()
        self.assertIsInstance(report, dict)
        self.assertIn("gpu_present", report)
        self.assertIn("cuda_available", report)
        self.assertIn("device_name", report)
        self.assertIn("recommended_device", report)
        self.assertIn("vram_total_gb", report)
        self.assertIn("vram_allocated_gb", report)
        self.assertIn("sys_ram_total_gb", report)
        self.assertIn("nvidia_driver_version", report)
        self.assertIn("status_message", report)

    def test_cuda_detection(self):
        report = inspect_hardware()
        if report["cuda_available"]:
            self.assertEqual(report["recommended_device"], "CUDA")
            self.assertGreater(report["vram_total_gb"], 0.0)
            self.assertNotEqual(report["device_name"], "System CPU")

    def test_driver_version(self):
        driver = get_nvidia_driver_version()
        if driver is not None:
            self.assertIsInstance(driver, str)
            self.assertTrue(len(driver) > 0)

if __name__ == "__main__":
    unittest.main()
