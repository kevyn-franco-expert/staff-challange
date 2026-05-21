"""Test branch creation and management."""

from pathlib import Path

import pytest

from goldenpath_cli.branch import create_branch
from goldenpath_cli.config import ProjectConfig


class TestCreateBranch:
    """Branch creation tests."""

    def test_valid_branch_creation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should create branch with correct naming convention."""
        monkeypatch.chdir(tmp_path)
        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)
        # Create initial commit so we can branch
        (tmp_path / "README.md").write_text("# test", encoding="utf-8")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True)

        config = ProjectConfig(work_id_prefix="FIN")
        branch = create_branch(config, "FIN-123", "feature", "add payment validation")

        assert branch == "feature/FIN-123-add-payment-validation"
        # Verify branch exists
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == branch

    def test_invalid_work_id_prefix(self, tmp_path: Path) -> None:
        """Should reject Work ID with wrong prefix."""
        config = ProjectConfig(work_id_prefix="FIN")
        with pytest.raises(ValueError, match="must start with prefix"):
            create_branch(config, "BUG-123", "feature", "test")

    def test_invalid_branch_type(self, tmp_path: Path) -> None:
        """Should reject invalid branch type."""
        config = ProjectConfig(work_id_prefix="FIN")
        with pytest.raises(ValueError, match="not allowed"):
            create_branch(config, "FIN-123", "unknown", "test")
