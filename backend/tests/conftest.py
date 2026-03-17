import pytest
import queue
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def msg_queue():
    """Create a message queue for CrawlerService."""
    return queue.Queue()


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.Popen for testing without actual yt-dlp calls."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.wait = MagicMock(return_value=0)
        mock_process.terminate = MagicMock()
        mock_popen.return_value = mock_process
        yield mock_popen, mock_process


@pytest.fixture
def mock_crawler_service(msg_queue):
    """Create a CrawlerService instance with mocked subprocess."""
    # This will import after the module is created in Plan 01
    # For now, just return the queue for setup
    return msg_queue


@pytest.fixture
def sample_yt_dlp_output():
    """Sample yt-dlp --flat-playlist --dump-json output lines."""
    return [
        '{"id": "video1", "url": "https://youtube.com/watch?v=video1", "title": "Test Video 1"}',
        '{"id": "video2", "url": "https://youtube.com/watch?v=video2", "title": "Test Video 2"}',
        '{"id": "video3", "url": "https://youtube.com/watch?v=video3", "title": "Test Video 3"}',
    ]