"""Test configuration loading and defaults."""

from pathlib import Path

import pytest

from goldenpath_cli.config import load_config


class TestLoadConfig:
    """Configuration loading tests."""

    def test_default_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default config should return sensible defaults."""
        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config.name == ""
        assert config.language == "python"
        assert config.git.main_branch == "main"
        assert config.git.require_two_reviewers is True

    def test_env_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables should override defaults."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GOLDENPATH_PROJECT__NAME", "transactionify")
        monkeypatch.setenv("GOLDENPATH_GIT__REQUIRE_TWO_REVIEWERS", "false")
        config = load_config()
        assert config.name == "transactionify"
        assert config.git.require_two_reviewers is False

    def test_yaml_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """YAML config file should be loaded."""
        monkeypatch.chdir(tmp_path)
        yaml_content = """
project:
  name: my-service
  language: go
git:
  main_branch: develop
"""
        (tmp_path / "goldenpath.yaml").write_text(yaml_content, encoding="utf-8")
        config = load_config()
        assert config.name == "my-service"
        assert config.language == "go"
        assert config.git.main_branch == "develop"
