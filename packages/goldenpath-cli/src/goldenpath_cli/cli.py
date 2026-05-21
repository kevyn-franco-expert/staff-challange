"""Golden Path CLI — Main application entry point.

Commands:
  init       Initialize a new service with Golden Path scaffolding
  standards  Validate project against Golden Path standards
  validate   Run validation checks (work-id, pr, commits)
  branch     Create standardized branches with Work ID
  hooks      Manage git hooks
  dora       DORA metrics and telemetry
  local      Local environment management
"""

from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from goldenpath_cli.branch import create_branch
from goldenpath_cli.config import ProjectConfig, load_config
from goldenpath_cli.dora import DoraTelemetry
from goldenpath_cli.git import (
    get_git_info,
    get_repo,
    validate_branch_name,
    validate_commit_messages,
    validate_pr_template,
)
from goldenpath_cli.hooks import HookManager
from goldenpath_cli.local_env import LocalEnvBootstrap
from goldenpath_cli.standards import StandardsCheck

app = typer.Typer(
    name="goldenpath",
    help="Golden Path CLI — Enterprise Developer Experience Platform",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        from goldenpath_cli import __version__

        console.print(f"[bold]Golden Path CLI[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(  # noqa: UP007
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
    config: Path | None = typer.Option(  # noqa: UP007
        None, "--config", "-c", help="Path to goldenpath.yaml config file"
    ),
) -> None:
    """Golden Path CLI — Enforce conventions, automate workflows, capture DORA."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)


# =============================================================================
# INIT Command
# =============================================================================
@app.command()
def init(
    name: str = typer.Option(..., help="Service name"),
    language: str = typer.Option("python", help="Primary language (python, go, typescript, clojure)"),
    work_id: str = typer.Option(..., help="Initial Work ID (e.g., FIN-123)"),
    path: Path | None = typer.Option(None, help="Target directory (default: ./<name>)"),  # noqa: UP007
) -> None:
    """Initialize a new service with Golden Path scaffolding."""
    target = path or Path(name)
    target.mkdir(parents=True, exist_ok=True)

    # Create standard directories
    (target / "src").mkdir(exist_ok=True)
    (target / "tests").mkdir(exist_ok=True)
    (target / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (target / "scripts").mkdir(exist_ok=True)

    # Generate goldenpath.yaml
    config_content = f"""project:
  name: {name}
  language: {language}
  work_id_prefix: {work_id.split("-")[0]}

git:
  main_branch: main
  require_two_reviewers: true
  enforce_pr_template: true

dora:
  enabled: true
  audit_format: soc2

local_env:
  use_localstack: true
  localstack_services:
    - lambda
    - apigateway
    - dynamodb
    - sns
    - sqs
"""
    (target / "goldenpath.yaml").write_text(config_content, encoding="utf-8")

    # Generate PR template
    pr_template = """## Description
<!-- Describe your changes -->

## Work ID
<!-- Link to ticket: FIN-XXX -->

## Testing
<!-- How did you test these changes? -->
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Local validation completed

## Checklist
- [ ] Two reviewers assigned
- [ ] Work ID referenced in commits
- [ ] No secrets or credentials committed
- [ ] DORA events will be emitted on merge
"""
    (target / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(pr_template, encoding="utf-8")

    # Generate CODEOWNERS
    codeowners = "# Default owners for everything\n* @gila-software/platform-team\n"
    (target / ".github" / "CODEOWNERS").write_text(codeowners, encoding="utf-8")

    # Generate .gitignore
    gitignore = """.venv/
__pycache__/
*.egg-info/
node_modules/
.cdk.staging/
cdk.out/
.env
.env.local
.goldenpath/dora.jsonl
.localstack/
"""
    (target / ".gitignore").write_text(gitignore, encoding="utf-8")

    console.print(
        Panel.fit(
            f"[bold green]✅ Initialized Golden Path service: {name}[/bold green]\n"
            f"[dim]Language:[/dim] {language}\n"
            f"[dim]Work ID:[/dim] {work_id}\n"
            f"[dim]Path:[/dim] {target.resolve()}",
            title="goldenpath init",
        )
    )
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  cd {target}")
    console.print("  goldenpath hooks install")
    console.print("  goldenpath standards")


# =============================================================================
# STANDARDS Command
# =============================================================================
@app.command()
def standards(
    ctx: typer.Context,
    strict: bool = typer.Option(False, "--strict", help="Fail on any error"),
    check: bool = typer.Option(True, "--check/--no-check", help="Run standards check"),
) -> None:
    """Validate project against Golden Path standards."""

    config: ProjectConfig = ctx.obj["config"]

    if not check:
        console.print("[dim]Standards check skipped[/dim]")
        raise typer.Exit(0)

    checker = StandardsCheck(config)
    passed = checker.run_all(strict=strict)
    raise typer.Exit(0 if passed else 1)


# =============================================================================
# VALIDATE Command
# =============================================================================
validate_app = typer.Typer(help="Validation checks")
app.add_typer(validate_app, name="validate")


@validate_app.command("work-id")
def validate_work_id(
    ctx: typer.Context,
) -> None:
    """Validate Work ID compliance in current branch and commits."""

    config: ProjectConfig = ctx.obj["config"]

    repo = get_repo()
    results = []

    # Branch validation
    branch_result = validate_branch_name(config, repo)
    results.append(branch_result)

    # Commit validation
    commit_results = validate_commit_messages(config, repo)
    results.extend(commit_results)

    # Render results
    all_passed = all(r.passed for r in results)
    for result in results:
        color = "green" if result.passed else "red"
        icon = "✓" if result.passed else "✗"
        console.print(f"[{color}]{icon}[/{color}] {result.rule}: {result.message}")

    if not all_passed:
        console.print("\n[red]Work ID validation failed.[/red]")
        console.print("[dim]All branches and commits must include a Work ID (e.g., FIN-123)[/dim]")
        raise typer.Exit(1)

    console.print("[green]✓ Work ID validation passed[/green]")


@validate_app.command("pr")
def validate_pr(
    ctx: typer.Context,
) -> None:
    """Validate PR template and governance settings."""

    config: ProjectConfig = ctx.obj["config"]

    template_result = validate_pr_template()

    if template_result.passed:
        console.print(f"[green]✓[/green] {template_result.message}")
    else:
        console.print(f"[red]✗[/red] {template_result.message}")

    if config.git.require_two_reviewers:
        console.print("[dim]ℹ Two-reviewer rule is enforced for this repository[/dim]")

    if not template_result.passed:
        raise typer.Exit(1)


# =============================================================================
# BRANCH Command
# =============================================================================
@app.command()
def branch(
    ctx: typer.Context,
    work_id: str = typer.Option(..., help="Work ID (e.g., FIN-123)"),
    branch_type: str = typer.Option("feature", help="Branch type"),
    description: str = typer.Option(..., help="Short description"),
) -> None:
    """Create a standardized branch with Work ID enforcement."""

    config: ProjectConfig = ctx.obj["config"]

    try:
        create_branch(config, work_id, branch_type, description)
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except RuntimeError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# HOOKS Command
# =============================================================================
@app.command()
def hooks(
    install: bool = typer.Option(False, "--install", help="Install all hooks"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Remove Golden Path hooks"),
) -> None:
    """Manage Git hooks for pre-push validation."""
    manager = HookManager()

    if install:
        manager.install_all()
    elif uninstall:
        manager.uninstall_all()
    else:
        console.print("[dim]Use --install or --uninstall[/dim]")


# =============================================================================
# DORA Command
# =============================================================================
dora_app = typer.Typer(help="DORA metrics and telemetry")
app.add_typer(dora_app, name="dora")


@dora_app.command("report")
def dora_report(
    ctx: typer.Context,
    project: str | None = typer.Option(None, help="Filter by project name"),  # noqa: UP007
    days: int = typer.Option(30, help="Analysis period in days"),
) -> None:
    """Generate DORA metrics report from local telemetry."""

    config: ProjectConfig = ctx.obj["config"]
    telemetry = DoraTelemetry(config.dora)

    metrics = telemetry.compute_metrics(project=project, days=days)
    if not metrics:
        console.print("[yellow]No DORA events found. Run validations to generate telemetry.[/yellow]")
        return

    console.print(
        Panel.fit(
            f"[bold]DORA Metrics Report[/bold]\n"
            f"Period: {metrics['period_days']} days | Project: {metrics['project']}\n\n"
            f"  Deployment Frequency:      {metrics['deployment_frequency']}\n"
            f"  Lead Time (hours):         {metrics['lead_time_for_changes_hours']}\n"
            f"  Change Failure Rate:       {metrics['change_failure_rate']:.2%}\n"
            f"  Mean Time To Recovery (h): {metrics['mean_time_to_recovery_hours']}\n\n"
            f"[dim]Audit Compliance: {metrics['audit_trail_compliance']}[/dim]",
            title="DORA",
        )
    )


@dora_app.command("emit-validation")
def dora_emit_validation(
    ctx: typer.Context,
    work_id: str = typer.Option(..., help="Work ID"),
    success: bool = typer.Option(True, help="Validation outcome"),
) -> None:
    """Manually emit a validation DORA event."""

    config: ProjectConfig = ctx.obj["config"]
    telemetry = DoraTelemetry(config.dora)

    start = time.time()
    git_info = get_git_info()
    duration = time.time() - start

    event = telemetry.record_validation(
        work_id=work_id,
        project=config.name or git_info["repository"].split("/")[-1],
        commit_sha=git_info["commit_sha"],
        branch=git_info["branch"],
        success=success,
        duration=duration,
        metadata={"trigger": "manual_cli", "actor": git_info["author_email"]},
    )

    console.print(f"[green]✓[/green] Emitted {event.event_type} event for {work_id}")


# =============================================================================
# LOCAL Command
# =============================================================================
local_app = typer.Typer(help="Local environment management")
app.add_typer(local_app, name="local")


@local_app.command("env")
def local_env(
    ctx: typer.Context,
    bootstrap: bool = typer.Option(False, "--bootstrap", help="Generate local env files"),
    up: bool = typer.Option(False, "--up", help="Start docker-compose (requires bootstrap first)"),
) -> None:
    """Manage local development environment."""

    config: ProjectConfig = ctx.obj["config"]

    if bootstrap:
        bootstrapper = LocalEnvBootstrap(config)
        bootstrapper.bootstrap()
    elif up:
        import subprocess

        compose_file = config.local_env.docker_compose_path
        console.print("[bold]Starting local environment...[/bold]")
        try:
            subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                check=True,
            )
            console.print("[green]✓[/green] LocalStack is running")
        except FileNotFoundError:
            console.print("[red]✗[/red] docker-compose not found. Install Docker Desktop.")
            raise typer.Exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] Failed to start services: {e}")
            raise typer.Exit(1)
    else:
        console.print("[dim]Use --bootstrap to generate files or --up to start services[/dim]")


if __name__ == "__main__":
    app()
