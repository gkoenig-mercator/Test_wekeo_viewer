"""Tests for config.py"""
import pytest
import os
from unittest.mock import patch
from argparse import Namespace
from config import Config


class TestConfigFromEnv:
    """Test Config.from_env() method."""

    def test_from_env_with_all_vars_set(self):
        """Test loading config when all environment variables are set."""
        env = {
            "WEKEO_USER": "testuser",
            "WEKEO_PASS": "testpass",
            "WEKEO_DATASET": "CUSTOM_DATASET",
            "WEKEO_LAYER": "Custom Layer",
            "MOUSE_INTERVAL": "8",
            "CHECK_INTERVAL": "12",
            "HEADLESS": "true",
            "WEKEO_BROWSER": "firefox",
        }
        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env()
            assert config.username == "testuser"
            assert config.password == "testpass"
            assert config.dataset_hint == "CUSTOM_DATASET"
            assert config.layer_hint == "Custom Layer"
            assert config.mouse_interval == 8
            assert config.check_interval == 12
            assert config.headless is True
            assert config.browser == "firefox"

    def test_from_env_with_defaults(self):
        """Test loading config with only defaults (no env vars)."""
        # Clear relevant env vars
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
            assert config.username == ""
            assert config.password == ""
            assert config.dataset_hint == "EO:ESA:DAT:SENTINEL-2"
            assert config.layer_hint == "True color"
            assert config.mouse_interval == 5
            assert config.check_interval == 10
            assert config.headless is False
            assert config.browser == "chromium"

    def test_from_env_headless_false_string(self):
        """Test that 'false' string for HEADLESS results in False."""
        with patch.dict(os.environ, {"HEADLESS": "false"}, clear=False):
            config = Config.from_env()
            assert config.headless is False

    def test_from_env_headless_any_truthy_string(self):
        """Test that any truthy string for HEADLESS results in True."""
        with patch.dict(os.environ, {"HEADLESS": "true"}, clear=False):
            config = Config.from_env()
            assert config.headless is True


class TestConfigFromEnvAndArgs:
    """Test Config.from_env_and_args() method."""

    def test_args_override_env(self):
        """Test that CLI args override environment variables."""
        env = {
            "WEKEO_USER": "envuser",
            "WEKEO_PASS": "envpass",
            "MOUSE_INTERVAL": "5",
        }
        args = Namespace(
            browser="webkit",
            mouse_interval=10,
            check_interval=None,
            headless=False,
        )
        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env_and_args(args)
            assert config.browser == "webkit"  # Overridden
            assert config.mouse_interval == 10  # Overridden
            assert config.username == "envuser"  # From env
            assert config.password == "envpass"  # From env

    def test_args_partial_override(self):
        """Test that None args don't override env values."""
        env = {
            "WEKEO_BROWSER": "chromium",
            "MOUSE_INTERVAL": "7",
        }
        args = Namespace(
            browser=None,
            mouse_interval=None,
            check_interval=15,
            headless=False,
        )
        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env_and_args(args)
            assert config.browser == "chromium"  # From env
            assert config.mouse_interval == 7  # From env
            assert config.check_interval == 15  # Overridden

    def test_headless_flag_only_sets_true(self):
        """Test that headless flag only sets True, not False."""
        args = Namespace(
            browser=None,
            mouse_interval=None,
            check_interval=None,
            headless=False,  # Flag not set
        )
        with patch.dict(os.environ, {"HEADLESS": "false"}, clear=False):
            config = Config.from_env_and_args(args)
            assert config.headless is False

        args.headless = True
        with patch.dict(os.environ, {"HEADLESS": "false"}, clear=False):
            config = Config.from_env_and_args(args)
            assert config.headless is True


class TestConfigValidate:
    """Test Config.validate() method."""

    def test_validate_success(self):
        """Test validation passes with valid credentials."""
        config = Config(
            username="user",
            password="pass",
            dataset_hint="dataset",
            layer_hint="layer",
            mouse_interval=5,
            check_interval=10,
            headless=True,
        )
        # Should not raise
        config.validate()

    def test_validate_missing_username(self):
        """Test validation fails without username."""
        config = Config(
            username="",
            password="pass",
            dataset_hint="dataset",
            layer_hint="layer",
            mouse_interval=5,
            check_interval=10,
            headless=True,
        )
        with pytest.raises(ValueError, match="WEKEO_USER"):
            config.validate()

    def test_validate_missing_password(self):
        """Test validation fails without password."""
        config = Config(
            username="user",
            password="",
            dataset_hint="dataset",
            layer_hint="layer",
            mouse_interval=5,
            check_interval=10,
            headless=True,
        )
        with pytest.raises(ValueError, match="WEKEO_PASS"):
            config.validate()

    def test_validate_missing_both(self):
        """Test validation fails when both credentials are missing."""
        config = Config(
            username="",
            password="",
            dataset_hint="dataset",
            layer_hint="layer",
            mouse_interval=5,
            check_interval=10,
            headless=True,
        )
        with pytest.raises(ValueError):
            config.validate()
