import unittest
import os
import shutil
import time
from backend.core.controller import download_controller
from backend.core.models import TaskStatus

class TestDownloadController(unittest.TestCase):
    def setUp(self):
        # Reset controller state for tests
        download_controller.tasks = {}
        download_controller.destination = "test_downloads"
        os.makedirs("test_downloads", exist_ok=True)

    def tearDown(self):
        if os.path.exists("test_downloads"):
            try:
                shutil.rmtree("test_downloads")
            except:
                pass

    def test_add_urls(self):
        text = "Check this out https://www.youtube.com/watch?v=BaW_jenozKc and also https://vimeo.com/123456"
        download_controller.add_urls(text)
        self.assertEqual(len(download_controller.tasks), 2)
        self.assertIn("https://www.youtube.com/watch?v=BaW_jenozKc", download_controller.tasks)

    def test_deduplication_normalization(self):
        url1 = "https://youtube.com/watch?v=123"
        url2 = "https://youtube.com/watch?v=123#t=10s"
        download_controller.add_urls(url1)
        download_controller.add_urls(url2) # Should be ignored or normalized to same
        # normalization removes fragment
        self.assertEqual(len(download_controller.tasks), 1)

    def test_status_transitions(self):
        url = "https://example.com/video.mp4"
        download_controller.add_urls(url)
        
        # Simulate manager loop pickup (state change)
        t = download_controller.tasks[url]
        self.assertEqual(t.status, TaskStatus.INFO)
        
        # Test manual state overrides
        download_controller.cancel(url)
        self.assertEqual(t.status, TaskStatus.CANCELLED)
        
        download_controller.retry(url) # Should fail as it ignores cancelled, only failed
        self.assertEqual(t.status, TaskStatus.CANCELLED)
        
        # Force fail to test retry
        t.status = TaskStatus.FAILED
        download_controller.retry(url)
        self.assertEqual(t.status, TaskStatus.QUEUED)

if __name__ == "__main__":
    unittest.main()
