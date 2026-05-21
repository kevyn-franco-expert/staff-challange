# Golden Path CLI

> **Enterprise Developer Experience Platform — Python CLI**

The `goldenpath-cli` is the primary developer interface for the Golden Path ecosystem. It enforces conventions, automates Git workflows, triggers local validations, and captures DORA telemetry.

## Installation

Install directly from the Git repository using `uv`:

```bash
# Install uv if not already available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the CLI
uv tool install git+https://github.com/gila-software/goldenpath-platform.git#subdirectory=packages/goldenpath-cli

# Or in a local project
uv pip install "git+https://github.com/gila-software/goldenpath-platform.git#subdirectory=packages/goldenpath-cli"
```

## Quick Start

```bash
# Verify installation
goldenpath --version

# Initialize a new service with Golden Path conventions
goldenpath init --name my-service --language python --work-id FIN-123

# Run standards check
goldenpath standards

# Install git hooks for pre-push validation
goldenpath hooks install

# Validate Work ID presence in current branch/commits
goldenpath validate work-id
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new service with Golden Path scaffolding |
| `standards` | Validate project against Golden Path standards |
| `validate work-id` | Ensure Work ID compliance (FIN-xxx) |
| `validate pr` | Validate PR title, reviewers, and template |
| `branch` | Create standardized branch with Work ID |
| `hooks install` | Install pre-push git hooks |
| `dora report` | Generate local DORA metrics snapshot |
| `local env` | Bootstrap local development environment |

## Configuration

Create `goldenpath.yaml` in your repository root:

```yaml
project:
  name: transactionify
  language: python
  work_id_prefix: FIN

git:
  main_branch: main
  require_two_reviewers: true
  enforce_pr_template: true

dora:
  enabled: true
  audit_format: soc2
```

## Inner-Source Contributions

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on proposing new language support or pipeline features.
