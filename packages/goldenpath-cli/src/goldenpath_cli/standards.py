"""Standards checking engine.

Validates project structure, configuration, and conventions against
the Golden Path baseline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from goldenpath_cli.config import ProjectConfig

console = Console()


class StandardsCheck:
    """Orchestrates standards validation."""

    def __init__(self, config: ProjectConfig, repo_path: Path | None = None) -> None:
        self.config = config
        self.repo_path = repo_path or Path.cwd()
        self.results: list[dict[str, Any]] = []

    def _check_file_exists(self, name: str, path: Path, required: bool = True) -> dict[str, Any]:
        """Check if a file exists."""
        exists = path.exists()
        passed = exists if required else True
        severity = "error" if required and not exists else ("warning" if not exists else "info")
        return {
            "rule": f"file:{name}",
            "passed": passed,
            "message": (f"{'✓' if exists else '✗'} {name} {'found' if exists else 'missing'} at {path}"),
            "severity": severity,
            "path": str(path),
        }

    def check_project_structure(self) -> list[dict[str, Any]]:
        """Validate standard project files."""
        checks = [
            ("README.md", self.repo_path / "README.md", True),
            ("LICENSE", self.repo_path / "LICENSE", False),
            (" goldenpath.yaml", self.repo_path / "goldenpath.yaml", True),
            (".gitignore", self.repo_path / ".gitignore", True),
        ]

        if self.config.language == "python":
            checks.extend(
                [
                    ("pyproject.toml", self.repo_path / "pyproject.toml", True),
                    ("tests/", self.repo_path / "tests", True),
                ]
            )
        elif self.config.language in ("typescript", "javascript"):
            checks.extend(
                [
                    ("package.json", self.repo_path / "package.json", True),
                    ("tsconfig.json", self.repo_path / "tsconfig.json", False),
                ]
            )
        elif self.config.language == "go":
            checks.extend(
                [
                    ("go.mod", self.repo_path / "go.mod", True),
                ]
            )

        return [self._check_file_exists(name, path, req) for name, path, req in checks]

    def check_security_baseline(self) -> list[dict[str, Any]]:
        """Validate security-related files and settings."""
        results = []

        # Check for secrets scanning config
        secrets_path = self.repo_path / ".github" / "workflows" / "secrets-scan.yml"
        results.append(self._check_file_exists("secrets-scan.yml", secrets_path, False))

        # Check for dependency scanning
        dependabot = self.repo_path / ".github" / "dependabot.yml"
        results.append(self._check_file_exists("dependabot.yml", dependabot, False))

        # Check for CODEOWNERS
        codeowners = self.repo_path / ".github" / "CODEOWNERS"
        exists = codeowners.exists()
        results.append(
            {
                "rule": "security:codeowners",
                "passed": exists,
                "message": f"{'✓' if exists else '✗'} CODEOWNERS {'found' if exists else 'missing'}",
                "severity": "error" if not exists else "info",
                "path": str(codeowners),
            }
        )

        return results

    def check_dora_config(self) -> list[dict[str, Any]]:
        """Validate DORA telemetry is configured."""
        results = []
        dora_path = self.repo_path / ".goldenpath"
        results.append(
            {
                "rule": "dora:directory",
                "passed": dora_path.exists(),
                "message": f"{'✓' if dora_path.exists() else '✗'} .goldenpath directory exists",
                "severity": "warning" if not dora_path.exists() else "info",
                "path": str(dora_path),
            }
        )
        return results

    def run_all(self, strict: bool = False) -> bool:
        """Run all standards checks and report."""
        self.results = []
        self.results.extend(self.check_project_structure())
        self.results.extend(self.check_security_baseline())
        self.results.extend(self.check_dora_config())

        table = Table(title="Golden Path Standards Check")
        table.add_column("Rule", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Severity", style="dim")
        table.add_column("Message", style="white")

        errors = 0
        warnings = 0

        for result in self.results:
            status = "[green]PASS[/green]" if result["passed"] else "[red]FAIL[/red]"
            if not result["passed"] and result["severity"] == "warning":
                status = "[yellow]WARN[/yellow]"

            if not result["passed"]:
                if result["severity"] == "error":
                    errors += 1
                else:
                    warnings += 1

            table.add_row(
                result["rule"],
                status,
                result["severity"],
                result["message"],
            )

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {errors} errors, {warnings} warnings")

        if errors > 0:
            if strict:
                console.print("[red]Standards check failed (strict mode).[/red]")
                return False
            console.print("[yellow]Standards check completed with errors.[/yellow]")
        else:
            console.print("[green]✓ Standards check passed![/green]")

        return errors == 0 or not strict
