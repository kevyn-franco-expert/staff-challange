"""Test Git governance validation."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from goldenpath_cli.config import ProjectConfig
from goldenpath_cli.git import (
    GitValidationError,
    get_repo,
    validate_branch_name,
    validate_pr_template,
)


class TestValidateBranchName:
    """Branch naming convention tests."""

    def test_valid_feature_branch(self) -> None:
        """Feature branch with Work ID should pass."""
        config = ProjectConfig(work_id_prefix="FIN")
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "feature/FIN-123-add-payment"

        result = validate_branch_name(config, mock_repo)
        assert result.passed is True
        assert result.metadata["work_id"] == "FIN-123"

    def test_invalid_branch_missing_work_id(self) -> None:
        """Branch without Work ID should fail."""
        config = ProjectConfig(work_id_prefix="FIN")
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "feature/add-payment"

        result = validate_branch_name(config, mock_repo)
        assert result.passed is False
        assert "work_id" in result.message.lower() or "pattern" in result.message.lower()

    def test_invalid_branch_prefix(self) -> None:
        """Unknown branch prefix should fail."""
        config = ProjectConfig(work_id_prefix="FIN")
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "unknown/FIN-123-something"

        result = validate_branch_name(config, mock_repo)
        assert result.passed is False
        assert "type" in result.message.lower()

    def test_main_branch_exception(self) -> None:
        """Main branch might not need Work ID (handled at commit level)."""
        config = ProjectConfig(work_id_prefix="FIN")
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"

        result = validate_branch_name(config, mock_repo)
        # Main branch typically fails branch naming — that's expected
        assert result.passed is False


class TestValidatePrTemplate:
    """PR template validation tests."""

    def test_missing_template(self, tmp_path: Path) -> None:
        """Missing PR template should fail."""
        result = validate_pr_template(tmp_path)
        assert result.passed is False
        assert "No PR template found" in result.message

    def test_valid_template(self, tmp_path: Path) -> None:
        """Valid PR template should pass."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template = github_dir / "PULL_REQUEST_TEMPLATE.md"
        template.write_text("## Description\n## Work ID\n## Testing\n## Checklist\n", encoding="utf-8")

        result = validate_pr_template(tmp_path)
        assert result.passed is True

    def test_template_missing_sections(self, tmp_path: Path) -> None:
        """Template missing required sections should warn."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template = github_dir / "PULL_REQUEST_TEMPLATE.md"
        template.write_text("## Description\n", encoding="utf-8")

        result = validate_pr_template(tmp_path)
        assert result.passed is False


class TestGetRepo:
    """Repository detection tests."""

    def test_no_git_repo(self, tmp_path: Path) -> None:
        """Should raise GitValidationError when not in a repo."""
        with pytest.raises(GitValidationError):
            get_repo(tmp_path)
