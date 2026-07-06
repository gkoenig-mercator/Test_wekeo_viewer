import pytest
import tempfile
from pathlib import Path
import sys
from unittest.mock import MagicMock

# Add the parent directory to sys.path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Provide a mock Config object."""
    from config import Config

    return Config(
        username="test_user",
        password="test_pass",
        dataset_hint="TEST_DATASET",
        layer_hint="Test Layer",
        mouse_interval=5,
        check_interval=10,
        headless=True,
        browser="chromium",
    )


@pytest.fixture
def mock_page():
    """Provide a mock Playwright Page object."""
    mock = MagicMock()
    mock.screenshot = MagicMock()
    mock.url = "https://example.com"
    return mock
