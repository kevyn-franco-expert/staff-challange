"""Branch creation and management utilities.

Standardizes branch naming across all teams with Work ID enforcement.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from goldenpath_cli.config import ProjectConfig

console = Console()


def create_branch(config: ProjectConfig, work_id: str, branch_type: str, description: str) -> str:
    """Create a new branch following Golden Path conventions.

    Args:
        config: Project configuration
        work_id: Work ID (e.g., FIN-123)
        branch_type: Branch type (feature, bugfix, hotfix, release, chore)
        description: Short description (kebab-case)

    Returns:
        The created branch name
    """
    # Validate work_id matches prefix
    prefix = config.work_id_prefix
    if not work_id.startswith(prefix):
        raise ValueError(f"Work ID '{work_id}' must start with prefix '{prefix}'")

    # Validate branch type
    if branch_type not in config.git.allowed_branch_prefixes:
        raise ValueError(f"Branch type '{branch_type}' not allowed. Use: {config.git.allowed_branch_prefixes}")

    # Sanitize description
    clean_desc = description.lower().replace(" ", "-").replace("_", "-")
    clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "-")
    clean_desc = clean_desc.strip("-")

    if not clean_desc:
        raise ValueError("Description cannot be empty after sanitization")

    branch_name = f"{branch_type}/{work_id}-{clean_desc}"

    # Verify we're in a git repo
    if not (Path.cwd() / ".git").exists():
        raise RuntimeError("Not in a Git repository")

    # Create branch
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create branch: {e.stderr}") from e

    console.print(f"[green]✓[/green] Created branch: [bold]{branch_name}[/bold]")
    console.print(f"[dim]Type:[/dim] {branch_type}")
    console.print(f"[dim]Work ID:[/dim] {work_id}")
    console.print(f"[dim]Description:[/dim] {clean_desc}")

    return branch_name
