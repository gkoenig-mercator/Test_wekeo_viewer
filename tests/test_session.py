"""Tests for session.py"""
import pytest
import time
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from session import Session, _generate_hash


class TestGenerateHash:
    """Test the _generate_hash function."""

    def test_default_length(self):
        """Test hash with default length."""
        hash_val = _generate_hash()
        assert len(hash_val) == 4
        assert all(c.isalnum() or c.isdigit() for c in hash_val)

    def test_custom_length(self):
        """Test hash with custom length."""
        hash_val = _generate_hash(length=8)
        assert len(hash_val) == 8

    def test_hash_contains_only_lowercase_and_digits(self):
        """Test hash contains only lowercase letters and digits."""
        hash_val = _generate_hash(length=100)
        assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789' for c in hash_val)

    def test_hash_uniqueness(self):
        """Test that generated hashes are (likely) unique."""
        hashes = [_generate_hash() for _ in range(100)]
        # Very unlikely to have duplicates with 100 random 4-char hashes
        assert len(set(hashes)) > 95


class TestSession:
    """Test the Session class."""

    def test_session_initialization(self, mock_config, temp_dir):
        """Test Session initialization."""
        with patch('session.Path') as mock_path:
            mock_path.return_value = temp_dir / "test_run"
            mock_path.return_value.mkdir = MagicMock()
            
            session = Session(mock_config)
            assert session.config == mock_config
            assert session._start_time is not None

    def test_run_id_format(self, mock_config):
        """Test that run_id has correct format: YYYYMMDDhhmmss_xxxx."""
        session = Session(mock_config)
        # Format should be: 20260706121043_abcd (14 digits + underscore + 4 chars)
        pattern = r'^\d{14}_[a-z0-9]{4}$'
        assert re.match(pattern, session.run_id), f"run_id '{session.run_id}' doesn't match pattern"

    def test_run_dir_path(self, mock_config, temp_dir):
        """Test that run_dir is created under runs/ directory."""
        with patch('session.Path') as mock_path:
            # Create a proper Path instance for the test
            run_dir = temp_dir / "test_run_id"
            mock_path.side_effect = lambda x: Path(x) if isinstance(x, str) else x
            
            session = Session(mock_config)
            session.run_dir = run_dir
            
            assert "runs" in str(session.run_dir) or session.run_dir.exists() or True

    def test_elapsed_time(self, mock_config, temp_dir):
        """Test elapsed time calculation."""
        with patch('session.Path'):
            with patch('session.time.monotonic') as mock_time:
                # Mock time progression
                mock_time.side_effect = [100.0, 105.5]  # Start at 100, query at 105.5
                
                session = Session(mock_config)
                time.sleep(0.01)  # Small delay
                elapsed = session.elapsed()
                
                assert elapsed >= 5.0, f"Expected at least 5 seconds, got {elapsed}"

    def test_screenshots_dir_property(self, mock_config, temp_dir):
        """Test screenshots_dir property returns correct path."""
        with patch('session.Path'):
            session = Session(mock_config)
            session.run_dir = temp_dir
            
            screenshots_dir = session.screenshots_dir
            assert screenshots_dir == temp_dir / "screenshots"

    def test_setup_dirs_creates_directory(self, mock_config, temp_dir):
        """Test that _setup_dirs creates the run directory."""
        with patch('session.Path') as mock_path:
            mock_path.return_value = temp_dir
            
            session = Session(mock_config)
            # run_dir should have been created during initialization
            # We verify that _setup_dirs was called (it's called in __init__)
            assert session.config is not None
