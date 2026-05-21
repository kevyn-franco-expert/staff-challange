"""Configuration management for Golden Path CLI.

Supports hierarchical config resolution:
1. Environment variables (GOLDENPATH_*)
2. Repository-level `goldenpath.yaml`
3. User-level `~/.config/goldenpath/config.yaml`
4. Built-in defaults
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GitConfig:
    """Git governance settings."""

    main_branch: str = "main"
    require_two_reviewers: bool = True
    enforce_pr_template: bool = True
    allowed_branch_prefixes: tuple[str, ...] = (
        "feature",
        "bugfix",
        "hotfix",
        "release",
        "chore",
    )
    work_id_pattern: str = r"[A-Z]+-\d+"
    commit_message_template: str = "[{work_id}] {type}: {description}"


@dataclass(frozen=True)
class DoraConfig:
    """DORA telemetry configuration."""

    enabled: bool = True
    audit_format: str = "soc2"  # soc2 | iso27001 | custom
    metrics_endpoint: str | None = None
    local_metrics_path: str = ".goldenpath/dora.jsonl"


@dataclass(frozen=True)
class LocalEnvConfig:
    """Local environment settings."""

    use_localstack: bool = True
    localstack_services: tuple[str, ...] = ("lambda", "apigateway", "dynamodb", "sns", "sqs")
    docker_compose_path: str = "docker-compose.local.yml"


@dataclass(frozen=True)
class ProjectConfig:
    """Top-level Golden Path configuration."""

    name: str = ""
    language: str = "python"
    work_id_prefix: str = "FIN"
    git: GitConfig = field(default_factory=GitConfig)
    dora: DoraConfig = field(default_factory=DoraConfig)
    local_env: LocalEnvConfig = field(default_factory=LocalEnvConfig)


DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "goldenpath" / "config.yaml",
    Path("goldenpath.yaml"),
    Path(".goldenpath.yaml"),
]


def load_yaml(path: Path) -> dict[str, Any]:
    """Safely load YAML file."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _env_override(config: dict[str, Any], prefix: str = "GOLDENPATH") -> dict[str, Any]:
    """Apply environment variable overrides to config dict.

    Uses double-underscore '__' as hierarchy separator.
    Example: GOLDENPATH_GIT__REQUIRE_TWO_REVIEWERS=false
    """
    for key, value in os.environ.items():
        if not key.startswith(f"{prefix}_"):
            continue
        # Split by double underscore for hierarchy
        parts = key[len(prefix) + 1 :].lower().split("__")
        target = config
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        # Simple type inference
        if value.lower() in ("true", "false"):
            target[parts[-1]] = value.lower() == "true"
        else:
            target[parts[-1]] = value
    return config


def load_config(path: Path | None = None) -> ProjectConfig:
    """Load configuration from all sources with override precedence."""
    raw: dict[str, Any] = {}

    # 1. Built-in defaults (handled by dataclass)
    # 2. User-level config
    for default_path in DEFAULT_CONFIG_PATHS:
        raw.update(load_yaml(default_path))

    # 3. Explicit path
    if path:
        raw.update(load_yaml(path))

    # 4. Environment overrides
    raw = _env_override(raw)

    return ProjectConfig(
        name=raw.get("project", {}).get("name", ""),
        language=raw.get("project", {}).get("language", "python"),
        work_id_prefix=raw.get("project", {}).get("work_id_prefix", "FIN"),
        git=GitConfig(
            main_branch=raw.get("git", {}).get("main_branch", "main"),
            require_two_reviewers=raw.get("git", {}).get("require_two_reviewers", True),
            enforce_pr_template=raw.get("git", {}).get("enforce_pr_template", True),
            allowed_branch_prefixes=tuple(
                raw.get("git", {}).get("allowed_branch_prefixes", GitConfig.allowed_branch_prefixes)
            ),
            work_id_pattern=raw.get("git", {}).get("work_id_pattern", GitConfig.work_id_pattern),
        ),
        dora=DoraConfig(
            enabled=raw.get("dora", {}).get("enabled", True),
            audit_format=raw.get("dora", {}).get("audit_format", "soc2"),
            metrics_endpoint=raw.get("dora", {}).get("metrics_endpoint"),
            local_metrics_path=raw.get("dora", {}).get("local_metrics_path", ".goldenpath/dora.jsonl"),
        ),
        local_env=LocalEnvConfig(
            use_localstack=raw.get("local_env", {}).get("use_localstack", True),
            localstack_services=tuple(
                raw.get("local_env", {}).get("localstack_services", LocalEnvConfig.localstack_services)
            ),
            docker_compose_path=raw.get("local_env", {}).get("docker_compose_path", "docker-compose.local.yml"),
        ),
    )
