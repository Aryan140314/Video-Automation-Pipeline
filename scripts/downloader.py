"""
TTS Studio Resumable Downloader Utility
=======================================
Downloads model weight files from official URLs with HTTP Range header support,
disk space pre-checking, speed calculation, and progress callbacks.
"""

import os
import time
import shutil
import requests
import psutil

class ResumableDownloader:
    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size
        self._cancel_flag = False
        self._pause_flag = False

    def cancel(self):
        self._cancel_flag = True

    def pause(self):
        self._pause_flag = True

    def check_disk_space(self, target_dir: str, required_bytes: int) -> bool:
        """Verifies that target partition has at least `required_bytes` free."""
        try:
            os.makedirs(target_dir, exist_ok=True)
            free_bytes = psutil.disk_usage(target_dir).free
            return free_bytes >= (required_bytes + 500 * 1024 * 1024)  # 500MB safety buffer
        except Exception:
            return True  # Fallback if partition check fails

    def download_file(
        self,
        url: str,
        dest_path: str,
        expected_size: int | None = None,
        progress_callback=None
    ) -> bool:
        """
        Downloads a file with range support and resume capabilities.
        dest_path: Final target destination path.
        """
        self._cancel_flag = False
        self._pause_flag = False

        dest_dir = os.path.dirname(os.path.abspath(dest_path))
        os.makedirs(dest_dir, exist_ok=True)
        part_path = dest_path + ".part"

        # Check existing partial file size for HTTP Range resume
        resume_byte_pos = 0
        if os.path.exists(part_path):
            resume_byte_pos = os.path.getsize(part_path)

        # Pre-check disk space
        if expected_size and not self.check_disk_space(dest_dir, expected_size - resume_byte_pos):
            raise OSError("Insufficient disk space to download model file.")

        headers = {}
        if resume_byte_pos > 0:
            headers["Range"] = f"bytes={resume_byte_pos}-"

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            # Handle server Range header support
            if resume_byte_pos > 0 and response.status_code == 206:
                mode = "ab"
                content_range = response.headers.get("Content-Range", "")
                if "/" in content_range:
                    total_bytes = int(content_range.split("/")[-1])
                else:
                    total_bytes = (expected_size or 0)
            elif response.status_code == 200:
                mode = "wb"
                resume_byte_pos = 0
                total_bytes = int(response.headers.get("content-length", expected_size or 0))
            else:
                response.raise_for_status()
                total_bytes = expected_size or 0
                mode = "wb"

            downloaded = resume_byte_pos
            start_time = time.time()
            last_time = start_time
            last_downloaded = downloaded

            with open(part_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if self._cancel_flag:
                        f.close()
                        if os.path.exists(part_path):
                            os.remove(part_path)
                        print("[Downloader] Download cancelled by user.")
                        return False

                    if self._pause_flag:
                        print("[Downloader] Download paused.")
                        return False

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        current_time = time.time()
                        elapsed = current_time - last_time
                        if elapsed >= 0.5:  # Update metrics every 500ms
                            speed_mbps = round(((downloaded - last_downloaded) / (1024 * 1024)) / elapsed, 2)
                            percent = round((downloaded / total_bytes) * 100, 1) if total_bytes > 0 else 0.0
                            if progress_callback:
                                progress_callback({
                                    "downloaded_bytes": downloaded,
                                    "total_bytes": total_bytes,
                                    "percent": percent,
                                    "speed_mbps": speed_mbps
                                })
                            last_time = current_time
                            last_downloaded = downloaded

            # Move .part to final destination
            if os.path.exists(part_path):
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(part_path, dest_path)

            if progress_callback:
                progress_callback({
                    "downloaded_bytes": downloaded,
                    "total_bytes": downloaded,
                    "percent": 100.0,
                    "speed_mbps": 0.0
                })

            return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0

        except Exception as e:
            print(f"[Downloader Error] {url}: {e}")
            return False
