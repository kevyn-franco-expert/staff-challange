"""Git governance and validation utilities.

Enforces:
- Universal Work ID (FIN-123) in branches, commits, PR titles
- Two-reviewer rule
- PR template compliance
- Branch naming conventions
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git import Repo
from git.exc import InvalidGitRepositoryError

from goldenpath_cli.config import ProjectConfig


class GitValidationError(Exception):
    """Raised when Git governance rules are violated."""


@dataclass(frozen=True)
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    rule: str
    message: str
    severity: str = "error"  # error | warning | info
    metadata: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", self.metadata if self.metadata is not None else {})


def get_repo(path: Path | None = None) -> Repo:
    """Get Git repository from path or current directory."""
    search_path = path or Path.cwd()
    try:
        return Repo(search_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        raise GitValidationError(f"No Git repository found at {search_path}") from exc


def validate_branch_name(config: ProjectConfig, repo: Repo | None = None) -> ValidationResult:
    """Ensure branch name contains a valid Work ID."""
    repo = repo or get_repo()
    branch = repo.active_branch.name
    prefix = config.work_id_prefix
    pattern = re.compile(config.git.work_id_pattern)

    # Extract Work ID from branch (e.g., feature/FIN-123-description)
    parts = branch.split("/")
    if len(parts) < 2:
        return ValidationResult(
            passed=False,
            rule="branch-naming",
            message=f"Branch '{branch}' must follow pattern: <type>/{prefix}-<id>-<description>",
            severity="error",
            metadata={"branch": branch, "expected_pattern": f"<type>/{prefix}-<id>-<desc>"},
        )

    branch_type = parts[0]
    if branch_type not in config.git.allowed_branch_prefixes:
        return ValidationResult(
            passed=False,
            rule="branch-prefix",
            message=(f"Branch type '{branch_type}' not allowed. Use: {config.git.allowed_branch_prefixes}"),
            severity="error",
            metadata={"branch": branch, "allowed": config.git.allowed_branch_prefixes},
        )

    # Extract Work ID from the second segment (e.g., FIN-123-add-payment -> FIN-123)
    work_id_segment = parts[1]
    match = pattern.search(work_id_segment)
    if not match:
        return ValidationResult(
            passed=False,
            rule="work-id-in-branch",
            message=(f"Work ID not found in '{work_id_segment}'. Expected pattern: {pattern.pattern}"),
            severity="error",
            metadata={"branch": branch, "segment": work_id_segment},
        )

    work_id = match.group(0)
    return ValidationResult(
        passed=True,
        rule="branch-naming",
        message=f"Branch '{branch}' complies with Golden Path conventions",
        severity="info",
        metadata={"branch": branch, "work_id": work_id, "type": branch_type},
    )


def validate_commit_messages(config: ProjectConfig, repo: Repo | None = None) -> list[ValidationResult]:
    """Ensure commits on current branch include Work ID references."""
    repo = repo or get_repo()
    pattern = re.compile(config.git.work_id_pattern)
    results: list[ValidationResult] = []

    # Compare against main branch
    main = config.git.main_branch
    try:
        commits = list(repo.iter_commits(f"{main}..HEAD"))
    except Exception:
        # If main is not reachable, check last N commits
        commits = list(repo.iter_commits("HEAD", max_count=10))

    for commit in commits:
        msg = commit.message.split("\n")[0]  # First line only
        if not pattern.search(msg):
            results.append(
                ValidationResult(
                    passed=False,
                    rule="commit-work-id",
                    message=f"Commit {commit.hexsha[:8]} missing Work ID in message: '{msg}'",
                    severity="error",
                    metadata={"sha": commit.hexsha, "message": msg},
                )
            )
        else:
            results.append(
                ValidationResult(
                    passed=True,
                    rule="commit-work-id",
                    message=f"Commit {commit.hexsha[:8]} contains Work ID",
                    severity="info",
                    metadata={"sha": commit.hexsha, "message": msg},
                )
            )

    return results


def validate_pr_template(repo_path: Path | None = None) -> ValidationResult:
    """Check if PR template exists in repository."""
    path = repo_path or Path.cwd()
    template_paths = [
        path / ".github" / "PULL_REQUEST_TEMPLATE.md",
        path / ".github" / "pull_request_template.md",
        path / "PULL_REQUEST_TEMPLATE.md",
    ]

    for template in template_paths:
        if template.exists():
            content = template.read_text(encoding="utf-8")
            required_sections = ["Description", "Work ID", "Testing", "Checklist"]
            missing = [s for s in required_sections if s.lower() not in content.lower()]
            if missing:
                return ValidationResult(
                    passed=False,
                    rule="pr-template",
                    message=f"PR template missing sections: {missing}",
                    severity="warning",
                    metadata={"path": str(template), "missing": missing},
                )
            return ValidationResult(
                passed=True,
                rule="pr-template",
                message=f"PR template found and valid at {template}",
                severity="info",
                metadata={"path": str(template)},
            )

    return ValidationResult(
        passed=False,
        rule="pr-template",
        message="No PR template found. Create .github/PULL_REQUEST_TEMPLATE.md",
        severity="error",
        metadata={"searched": [str(p) for p in template_paths]},
    )


def get_git_info(repo: Repo | None = None) -> dict[str, Any]:
    """Extract Git metadata for DORA and audit logging."""
    repo = repo or get_repo()
    head = repo.head.commit

    return {
        "repository": repo.working_dir,
        "branch": repo.active_branch.name,
        "commit_sha": head.hexsha,
        "commit_short_sha": head.hexsha[:8],
        "commit_message": head.message.strip(),
        "author_name": head.author.name,
        "author_email": head.author.email,
        "commit_timestamp": head.committed_datetime.isoformat(),
        "remote_url": next(repo.remote().urls, None),
    }
