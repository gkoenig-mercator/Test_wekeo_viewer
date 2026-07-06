"""Tests for storage.py"""
import pytest
import csv
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from storage import Storage, CSV_HEADERS


class TestStorageInitialization:
    """Test Storage class initialization."""

    def test_storage_init(self, mock_config, temp_dir):
        """Test Storage initialization."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "test_run"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.config = mock_config

        with patch('storage.Path') as mock_path:
            # Make Path return real Path objects for temp_dir
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir / "runs"
                elif isinstance(arg, Path):
                    return arg
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            assert storage.session == mock_session


class TestStorageCsvSetup:
    """Test CSV initialization and writing."""

    def test_csv_headers_exist(self):
        """Test that CSV_HEADERS constant is properly defined."""
        assert len(CSV_HEADERS) > 0
        assert "run_id" in CSV_HEADERS
        assert "duration_seconds" in CSV_HEADERS
        assert "disconnect_reason" in CSV_HEADERS

    def test_csv_created_on_init(self, mock_config, temp_dir):
        """Test that CSV is created if it doesn't exist."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.config = mock_config
        csv_path = temp_dir / "results.csv"

        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.csv_path = csv_path
            storage._setup_csv()
            
            assert csv_path.exists()
            
            # Verify headers were written
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                assert headers == CSV_HEADERS

    def test_csv_not_recreated(self, mock_config, temp_dir):
        """Test that existing CSV is not overwritten."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.config = mock_config
        csv_path = temp_dir / "results.csv"

        # Create initial CSV
        with open(csv_path, 'w') as f:
            f.write("test_data\n")

        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.csv_path = csv_path
            storage._setup_csv()
            
            # Verify original content wasn't overwritten
            with open(csv_path, 'r') as f:
                content = f.read()
                assert content == "test_data\n"


class TestStorageLogging:
    """Test Storage logging functionality."""

    def test_log_writes_to_file(self, mock_config, temp_dir):
        """Test that log messages are written to file."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.config = mock_config

        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.log("Test message")
            
            # Check that file exists and contains message
            assert storage.log_path.exists()
            content = storage.log_path.read_text()
            assert "Test message" in content

    def test_log_includes_timestamp(self, mock_config, temp_dir):
        """Test that log includes timestamp."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.config = mock_config

        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.log("Test message")
            
            content = storage.log_path.read_text()
            # Check for timestamp format (YYYY-MM-DD HH:MM:SS)
            assert "[" in content and "]" in content


class TestStorageSaveResult:
    """Test Storage result saving."""

    def test_save_result_writes_to_csv(self, mock_config, temp_dir):
        """Test that save_result appends to CSV."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.run_id = "test_run_id"
        mock_session.config = mock_config

        csv_path = temp_dir / "results.csv"
        
        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.csv_path = csv_path
            storage._setup_csv()
            storage.save_result(duration_seconds=42.5, disconnect_reason="timeout")
            
            # Read CSV and verify data was added
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                row = next(reader)
                assert row[0] == "test_run_id"  # run_id
                assert row[2] == "42"  # duration_seconds (int part)
                assert row[3] == "timeout"  # disconnect_reason

    def test_save_result_with_config_data(self, mock_config, temp_dir):
        """Test that save_result includes config data."""
        mock_session = MagicMock()
        mock_session.run_dir = temp_dir / "run1"
        mock_session.run_dir.mkdir(parents=True, exist_ok=True)
        mock_session.run_id = "test_id_123"
        mock_session.config = mock_config

        csv_path = temp_dir / "results.csv"
        
        with patch('storage.Path') as mock_path:
            def path_side_effect(arg):
                if arg == "runs":
                    return temp_dir
                return Path(arg)
            
            mock_path.side_effect = path_side_effect
            
            storage = Storage(mock_session)
            storage.csv_path = csv_path
            storage._setup_csv()
            storage.save_result(duration_seconds=100, disconnect_reason="manual")
            
            # Read CSV and verify config data
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                row = next(reader)
                # Verify username, browser, etc. from config
                assert mock_config.username in row
                assert mock_config.browser in row
