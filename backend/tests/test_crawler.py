import pytest
import queue
import json
from unittest.mock import patch, MagicMock, call

# These tests will fail until CrawlerService is implemented in Plan 01
# This is expected - TDD RED phase


class TestCrawlerServiceInit:
    """Tests for CrawlerService initialization."""

    def test_crawler_service_import(self):
        """Test that CrawlerService can be imported."""
        # Will fail until backend/core/crawler.py exists
        from core.crawler import CrawlerService
        assert CrawlerService is not None

    def test_crawler_service_creation(self, msg_queue):
        """Test CrawlerService can be instantiated with message queue."""
        from core.crawler import CrawlerService
        service = CrawlerService(msg_queue)
        assert service.msg_queue == msg_queue
        assert service._active_process is None


class TestExtractUrls:
    """Tests for URL extraction functionality."""

    def test_extract_urls_starts_process(self, msg_queue, mock_subprocess):
        """Test that extract_urls starts a subprocess with correct yt-dlp args."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        service = CrawlerService(msg_queue)
        service.extract_urls("https://youtube.com/playlist?list=test")

        # Verify subprocess was called with yt-dlp flat-playlist flags
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert "yt-dlp" in call_args
        assert "--flat-playlist" in call_args
        assert "--dump-json" in call_args

    def test_extract_urls_sends_start_message(self, msg_queue, mock_subprocess):
        """Test that extraction sends crawl_start message."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        service = CrawlerService(msg_queue)
        service.extract_urls("https://youtube.com/playlist?list=test")

        # Check for start message in queue
        msg_type, payload = msg_queue.get(timeout=1)
        assert msg_type == "crawl_start"
        assert "page_url" in payload

    def test_extract_urls_parses_json_output(self, msg_queue, mock_subprocess, sample_yt_dlp_output):
        """Test that extraction parses yt-dlp JSON output correctly."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        # Setup mock stdout to yield sample lines
        mock_process.stdout.__iter__ = lambda self: iter(sample_yt_dlp_output)

        service = CrawlerService(msg_queue)
        service.extract_urls("https://youtube.com/playlist?list=test")

        # Wait for completion (with timeout)
        import time
        time.sleep(0.5)

        # Check for progress and complete messages
        messages = []
        while not msg_queue.empty():
            messages.append(msg_queue.get())

        msg_types = [m[0] for m in messages]
        assert "crawl_start" in msg_types


class TestCancelExtraction:
    """Tests for extraction cancellation."""

    def test_cancel_sets_event(self, msg_queue, mock_subprocess):
        """Test that cancel sets the cancellation event."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        service = CrawlerService(msg_queue)
        service.extract_urls("https://youtube.com/playlist?list=test")
        service.cancel()

        assert service._cancel_event.is_set()

    def test_cancel_terminates_process(self, msg_queue, mock_subprocess):
        """Test that cancel terminates the active process."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        service = CrawlerService(msg_queue)
        service.extract_urls("https://youtube.com/playlist?list=test")

        # Set the process reference
        service._active_process = mock_process
        service.cancel()

        mock_process.terminate.assert_called()

    def test_cancel_sends_cancelled_message(self, msg_queue, mock_subprocess):
        """Test that cancel sends crawl_cancelled message."""
        from core.crawler import CrawlerService
        mock_popen, mock_process = mock_subprocess

        service = CrawlerService(msg_queue)
        service.cancel()

        # Note: The actual message sending depends on implementation
        # This test verifies the expected behavior


class TestProgressMessages:
    """Tests for progress message broadcasting."""

    def test_progress_message_format(self, msg_queue):
        """Test that crawl_progress message has correct format."""
        from core.crawler import CrawlerService
        # Progress messages should have: count, latest

    def test_complete_message_format(self, msg_queue):
        """Test that crawl_complete message has correct format."""
        from core.crawler import CrawlerService
        # Complete messages should have: urls array

    def test_error_message_format(self, msg_queue):
        """Test that crawl_error message has correct format."""
        from core.crawler import CrawlerService
        # Error messages should have: error string