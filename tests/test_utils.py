"""Tests for utils.py"""
import pytest
from utils import minutes_formatting_for_elapse_time, parse_args


class TestMinutesFormattingForElapseTime:
    """Test the minutes_formatting_for_elapse_time function."""

    def test_zero_seconds(self):
        assert minutes_formatting_for_elapse_time(0) == "0m 0s"

    def test_seconds_only(self):
        assert minutes_formatting_for_elapse_time(45) == "0m 45s"

    def test_minutes_and_seconds(self):
        assert minutes_formatting_for_elapse_time(125) == "2m 5s"

    def test_exact_minute(self):
        assert minutes_formatting_for_elapse_time(60) == "1m 0s"

    def test_large_value(self):
        assert minutes_formatting_for_elapse_time(3661) == "61m 1s"

    def test_float_input(self):
        # Function should truncate float to int
        assert minutes_formatting_for_elapse_time(125.7) == "2m 5s"

    def test_float_truncation(self):
        assert minutes_formatting_for_elapse_time(59.9) == "0m 59s"


class TestParseArgs:
    """Test the parse_args function."""

    def test_no_args(self):
        """Test with default arguments."""
        args = parse_args([])
        assert args.browser is None
        assert args.mouse_interval is None
        assert args.check_interval is None
        assert args.headless is None

    def test_browser_arg(self):
        """Test specifying browser."""
        args = parse_args(["--browser", "firefox"])
        assert args.browser == "firefox"

    def test_mouse_interval_arg(self):
        """Test specifying mouse interval."""
        args = parse_args(["--mouse-interval", "10"])
        assert args.mouse_interval == 10

    def test_check_interval_arg(self):
        """Test specifying check interval."""
        args = parse_args(["--check-interval", "15"])
        assert args.check_interval == 15

    def test_headless_flag(self):
        """Test headless flag."""
        args = parse_args(["--headless"])
        assert args.headless is True

    def test_multiple_args(self):
        """Test multiple arguments together."""
        args = parse_args([
            "--browser", "webkit",
            "--mouse-interval", "7",
            "--check-interval", "12",
            "--headless"
        ])
        assert args.browser == "webkit"
        assert args.mouse_interval == 7
        assert args.check_interval == 12
        assert args.headless is True

    def test_invalid_browser(self):
        """Test that invalid browser raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["--browser", "invalid_browser"])
