"""Tests for storage.py"""
import pytest
import csv
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock
from storage import Storage, CSV_HEADERS


class TestStorageCsvHeaders:
    """Test CSV header configuration."""

    def test_csv_headers_exist(self):
        """Test that CSV_HEADERS constant is properly defined."""
        assert len(CSV_HEADERS) > 0
        assert "run_id" in CSV_HEADERS
        assert "duration_seconds" in CSV_HEADERS
        assert "disconnect_reason" in CSV_HEADERS


class TestStorageWithTempDir:
    """Test Storage functionality with temporary directory setup."""

    def test_storage_csv_setup(self, mock_config, temp_dir):
        """Test that CSV is created on initialization."""
        # Set up mock session and change to temp dir
        mock_session = MagicMock()
        run_dir = temp_dir / "run1"
        run_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / "runs").mkdir(exist_ok=True)
        
        mock_session.run_dir = run_dir
        mock_session.config = mock_config

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            storage = Storage(mock_session)
            
            # Verify CSV was created with headers
            assert storage.csv_path.exists()
            with open(storage.csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                assert headers == CSV_HEADERS
        finally:
            os.chdir(old_cwd)

    def test_storage_logging(self, mock_config, temp_dir):
        """Test that log messages are written to file."""
        mock_session = MagicMock()
        run_dir = temp_dir / "run1"
        run_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / "runs").mkdir(exist_ok=True)
        
        mock_session.run_dir = run_dir
        mock_session.config = mock_config

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            storage = Storage(mock_session)
            storage.log("Test message")
            
            # Check that file exists and contains message
            assert storage.log_path.exists()
            content = storage.log_path.read_text()
            assert "Test message" in content
            assert "[" in content  # timestamp bracket
        finally:
            os.chdir(old_cwd)

    def test_storage_save_result(self, mock_config, temp_dir):
        """Test that save_result appends to CSV."""
        mock_session = MagicMock()
        run_dir = temp_dir / "run1"
        run_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / "runs").mkdir(exist_ok=True)
        
        mock_session.run_dir = run_dir
        mock_session.run_id = "test_run_id"
        mock_session.config = mock_config

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            storage = Storage(mock_session)
            storage.save_result(duration_seconds=42.5, disconnect_reason="timeout")
            
            # Read CSV and verify data was added
            with open(storage.csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                row = next(reader)
                assert row[0] == "test_run_id"  # run_id
                assert row[2] == "42.5"  # duration_seconds (saved as float)
                assert row[3] == "timeout"  # disconnect_reason
        finally:
            os.chdir(old_cwd)

    def test_storage_csv_not_recreated(self, mock_config, temp_dir):
        """Test that existing CSV is not overwritten."""
        mock_session = MagicMock()
        run_dir = temp_dir / "run1"
        run_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / "runs").mkdir(exist_ok=True)
        
        mock_session.run_dir = run_dir
        mock_session.config = mock_config
        csv_path = temp_dir / "runs" / "results.csv"

        # Create initial CSV with test data
        with open(csv_path, 'w') as f:
            f.write("test_data\n")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            storage = Storage(mock_session)
            
            # Verify original content wasn't overwritten
            with open(storage.csv_path, 'r') as f:
                content = f.read()
                assert content == "test_data\n"
        finally:
            os.chdir(old_cwd)
