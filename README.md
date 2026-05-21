# Golden Path Platform

> **Enterprise Developer Experience (DevEx) Framework — Proof of Concept**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOLDEN PATH — SHARED ENGINEERING PLATFORM                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       │
│   │   Python     │ ◄─────► │   Golden     │ ◄─────► │  TypeScript  │       │
│   │     Team     │         │     Path     │         │    Team      │       │
│   └──────────────┘         │   Platform   │         └──────────────┘       │
│                            │              │                                │
│   ┌──────────────┐         │  ┌────────┐  │         ┌──────────────┐       │
│   │     Go       │ ◄─────► │  │  CLI   │  │ ◄─────► │    Clojure   │       │
│   │     Team     │         │  │(Python)│  │         │    Team      │       │
│   └──────────────┘         │  └───┬────┘  │         └──────────────┘       │
│                            │      │       │                                │
│                            │  ┌───┴────┐  │                                │
│                            │  │Framework│  │                                │
│                            │  │(TypeScript)│                               │
│                            │  └───┬────┘  │                                │
│                            │      │       │                                │
│                            └──────┼───────┘                                │
│                                   ▼                                        │
│                    ┌──────────────────────────┐                            │
│                    │   AWS CDK  │  GitHub Actions │  DORA Metrics         │
│                    └──────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Overview

The **Golden Path Platform** is a shared engineering ecosystem designed to homologate the development lifecycle across 10+ independent, full-cycle engineering teams at Gila Software. It treats Developer Experience as a product, providing:

- **Consistency**: Same conventions, same metrics, same quality bar regardless of language
- **Convention over Configuration**: Easier to follow the rules than to break them
- **Shift-Left**: Fail fast with local validation and pre-push governance
- **Observability**: Standardized DORA metrics and SOC 2 audit trails

## Architecture

The platform consists of **two independent, distributable packages**:

### Component A: `goldenpath-cli` (Python)

Developer-facing CLI tool installed via `uv`:

| Capability | Command | Purpose |
|-----------|---------|---------|
| Project Scaffolding | `goldenpath init` | Bootstrap services with conventions |
| Git Governance | `goldenpath validate work-id` | Enforce FIN-xxx in branches/commits |
| Standards Check | `goldenpath standards` | Validate project structure & security |
| Pre-Push Hooks | `goldenpath hooks install` | Run tests/lint before push |
| Local Environment | `goldenpath local env --bootstrap` | LocalStack for cloud-free dev |
| DORA Reporting | `goldenpath dora report` | Local metrics dashboard |

### Component B: `goldenpath-framework` (TypeScript)

Infrastructure and CI/CD framework installed via `pnpm`:

| Capability | Export | Purpose |
|-----------|--------|---------|
| CDK Constructs | `ServiceStack` | Standardized Lambda + API Gateway patterns |
| PR Pipeline | `generatePRPipeline()` | Type-safe PR workflow generator |
| Integration Pipeline | `generateIntegrationPipeline()` | Staging → Production deployment |
| DORA Telemetry | `DoraTelemetry` | Emit standardized metrics from infrastructure |

## Installation

### Prerequisites

- **Python CLI**: [uv](https://github.com/astral-sh/uv) package manager
- **Framework**: [pnpm](https://pnpm.io/) package manager
- **AWS**: AWS CDK CLI (`npm install -g aws-cdk`)
- **Docker**: For local development with LocalStack

### Install the CLI

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install CLI from repository
uv tool install git+https://github.com/gila-software/goldenpath-platform.git#subdirectory=packages/goldenpath-cli

# Verify
goldenpath --version
```

### Install the Framework

```bash
# In your service repository
pnpm add "https://github.com/gila-software/goldenpath-platform.git#path=packages/goldenpath-framework"

# Or with GitHub Packages (if published)
pnpm add @gila-software/goldenpath-framework
```

## Reference Project: Transactionify

The challenge references **Transactionify** — a microservice handling transaction processing:

- **Repository**: https://github.com/rrgarciach/transactionify
- **Stack**: AWS Lambda (Python) + API Gateway + DynamoDB + AWS CDK (TypeScript)
- **API**: `/api/v1/accounts`, `/api/v1/accounts/{id}/payments`, `/api/v1/accounts/{id}/balance`, `/api/v1/accounts/{id}/transactions`

## Quick Start: Transactionify Integration

See [`examples/transactionify-integration/`](examples/transactionify-integration/) for the complete fork-and-integrate guide.

```bash
# 1. Fork the reference repository
git clone https://github.com/YOUR_ORG/transactionify.git
cd transactionify

# 2. Initialize Golden Path conventions
goldenpath init --name transactionify --language python --work-id FIN-100

# 3. Install the framework
pnpm add "https://github.com/gila-software/goldenpath-platform.git#path=packages/goldenpath-framework"
pnpm add aws-cdk-lib constructs

# 4. Create CDK stack (see examples/transactionify-integration/infra/stack.ts)
#    Maps existing handlers: authorizer, accounts, payments, transactions

# 5. Generate CI/CD workflows
pnpm tsx scripts/generate-workflows.ts

# 6. Bootstrap local environment
goldenpath local env --bootstrap
docker-compose -f docker-compose.local.yml up -d

# 7. Install hooks
goldenpath hooks install

# 8. Run existing tests locally
cd test/unit/src/python
pytest -v
```

## DORA Metrics

The platform captures four core DORA metrics with SOC 2 audit trails:

| Metric | Source | Collection Method |
|--------|--------|-------------------|
| **Deployment Frequency** | GitHub Actions + CDK | Event emitted on every deployment |
| **Lead Time for Changes** | Git commits + deploy timestamp | First commit to production deploy |
| **Change Failure Rate** | CloudWatch Alarms + deployments | Failed deployments / total deployments |
| **MTTR** | Incident detection + recovery | Time from alarm to resolution |

All events include: `actor`, `action`, `reason`, `timestamp`, `work_id`, `compliance_framework`.

```bash
# View local metrics
goldenpath dora report --project transactionify --days 30
```

## Repository Structure

```
goldenpath-platform/
├── packages/
│   ├── goldenpath-cli/          # Python CLI (uv distributable)
│   │   ├── src/goldenpath_cli/
│   │   │   ├── cli.py           # Main Typer application
│   │   │   ├── config.py        # Hierarchical configuration
│   │   │   ├── git.py           # Git governance validation
│   │   │   ├── dora.py          # DORA telemetry collector
│   │   │   ├── standards.py     # Standards checking engine
│   │   │   ├── hooks.py         # Git hooks management
│   │   │   └── local_env.py     # LocalStack bootstrap
│   │   ├── tests/               # pytest suite
│   │   └── pyproject.toml       # uv packaging
│   └── goldenpath-framework/    # TypeScript Framework (pnpm distributable)
│       ├── src/
│       │   ├── constructs/      # CDK constructs
│       │   ├── workflows/       # GitHub Actions generators
│       │   ├── pipelines/       # YAML compiler
│       │   ├── dora/            # DORA telemetry types
│       │   └── types/           # Shared TypeScript types
│       ├── tests/               # vitest suite
│       └── package.json         # pnpm packaging
├── examples/
│   └── transactionify-integration/  # Reference integration
├── docs/
│   ├── ADR.md                   # Architecture Decision Record
│   └── output/                  # Generated deliverables (PDFs)
├── .github/
│   └── workflows/               # Platform CI/CD
├── Makefile                     # Unified build/test commands
└── README.md                    # This file
```

## Development

```bash
# Install everything
make install

# Run all tests
make test

# Run all lints
make lint

# Build both packages
make build
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the Inner-Source governance model, contribution flow, and quality gates.

## License

MIT — © 2024 Gila Software Platform Engineering
