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
        """Test Session initialization creates required attributes."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            (temp_dir / "runs").mkdir(exist_ok=True)
            session = Session(mock_config)
            assert session.config == mock_config
            assert session._start_time is not None
        finally:
            os.chdir(old_cwd)

    def test_run_id_format(self, mock_config):
        """Test that run_id has correct format: YYYYMMDDhhmmss_xxxx."""
        session = Session(mock_config)
        # Format should be: 20260706_120530_abcd (8 digits + underscore + 6 digits + underscore + 4 chars)
        pattern = r'^\d{8}_\d{6}_[a-z0-9]{4}$'
        assert re.match(pattern, session.run_id), f"run_id '{session.run_id}' doesn't match pattern"

    def test_run_dir_path(self, mock_config, temp_dir):
        """Test that run_dir is created under runs/ directory."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            (temp_dir / "runs").mkdir(exist_ok=True)
            session = Session(mock_config)
            assert session.run_dir.parent.name == "runs"
        finally:
            os.chdir(old_cwd)

    def test_elapsed_time(self, mock_config, temp_dir):
        """Test elapsed time calculation."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            (temp_dir / "runs").mkdir(exist_ok=True)
            session = Session(mock_config)
            time.sleep(0.1)  # Sleep for 0.1 seconds
            elapsed = session.elapsed()
            
            # Should have elapsed at least 0.1 seconds
            assert elapsed >= 0.05, f"Expected at least 0.05 seconds, got {elapsed}"
        finally:
            os.chdir(old_cwd)

    def test_screenshots_dir_property(self, mock_config, temp_dir):
        """Test screenshots_dir property returns correct path."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            (temp_dir / "runs").mkdir(exist_ok=True)
            session = Session(mock_config)
            
            screenshots_dir = session.screenshots_dir
            assert screenshots_dir.name == "screenshots"
            assert str(screenshots_dir).endswith("screenshots")
        finally:
            os.chdir(old_cwd)

    def test_setup_dirs_creates_directory(self, mock_config, temp_dir):
        """Test that _setup_dirs creates the run directory."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            (temp_dir / "runs").mkdir(exist_ok=True)
            session = Session(mock_config)
            # run_dir should have been created during initialization
            assert session.run_dir.exists()
        finally:
            os.chdir(old_cwd)
