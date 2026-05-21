# Platform Engineering Steering Principles

## Context

You are assisting with the Golden Path Platform — an enterprise Developer Experience (DevEx) framework consisting of a Python CLI and a TypeScript infrastructure framework. The platform serves 10+ independent engineering teams.

## Architecture Principles

1. **Convention over Configuration**: The easiest path must be the compliant path.
2. **Polyglot Support**: Infrastructure patterns must be language-agnostic while application code can be Python, Go, TypeScript, or Clojure.
3. **Shift-Left**: Validate as early as possible (IDE → pre-commit → pre-push → PR → integration).
4. **Observable by Default**: Every deployment, change, and failure emits DORA telemetry.
5. **Self-Service**: Teams should extend the platform without Platform Engineering approval for standard use cases.

## Code Style

### Python (CLI)
- Use `dataclasses` for configuration objects
- Prefer `pathlib.Path` over string paths
- Use `typer` for CLI commands with rich help text
- All functions must have type annotations (enforced by mypy strict mode)
- Docstrings follow Google convention

### TypeScript (Framework)
- All public APIs must have explicit return types
- Use `readonly` for immutable properties
- Prefer interfaces over type aliases for public APIs
- CDK constructs must expose outputs via `CfnOutput`
- Workflow definitions must pass `validateWorkflow()` before YAML generation

## DORA Compliance

Every change that affects deployment, infrastructure, or validation must consider:
- How will this affect Deployment Frequency measurement?
- Does it add or remove Lead Time?
- Could it impact Change Failure Rate?
- Does it improve or degrade MTTR?

## Testing Requirements

- Minimum one test per public function/method
- Tests must assert on behavior, not implementation
- Use pytest for Python, vitest for TypeScript
- Mock external dependencies (Git, AWS, filesystem)

## Security

- No secrets in source code (enforced by TruffleHog)
- IAM roles use least privilege
- OIDC preferred over long-lived credentials
- All infrastructure changes must be reviewable (no direct console changes)
