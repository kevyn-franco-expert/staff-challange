# Golden Path Framework

> **Enterprise CI/CD & Infrastructure Framework — TypeScript**

The `goldenpath-framework` provides type-safe AWS CDK constructs and GitHub Actions workflow generators that enforce the Golden Path across all services.

## Installation

Install directly from the Git repository using `pnpm`:

```bash
# Add to your service repository
pnpm add github:gila-software/goldenpath-platform#packages/goldenpath-framework

# Or with explicit subdirectory (pnpm 8+)
pnpm add "https://github.com/gila-software/goldenpath-platform.git#path=packages/goldenpath-framework"
```

## Quick Start

### 1. CDK Constructs

```typescript
import { App } from 'aws-cdk-lib';
import { ServiceStack } from '@gila-software/goldenpath-framework';

const app = new App();
new ServiceStack(app, 'TransactionifyStack', {
  serviceName: 'transactionify',
  environment: 'staging',
  runtime: 'python3.12',
  handlers: [
    { name: 'ProcessTransaction', path: 'src/handlers/process.py' },
    { name: 'ValidateTransaction', path: 'src/handlers/validate.py' },
  ],
  apiRoutes: [
    { path: '/transactions', method: 'POST', handler: 'ProcessTransaction' },
    { path: '/transactions/{id}', method: 'GET', handler: 'ValidateTransaction' },
  ],
});
```

### 2. Workflow Generation

```typescript
import { generatePRPipeline, generateIntegrationPipeline } from '@gila-software/goldenpath-framework/workflows';
import * as fs from 'fs';

// Generate PR Pipeline
const prWorkflow = generatePRPipeline({
  serviceName: 'transactionify',
  language: 'python',
  runsOn: 'ubuntu-latest',
  testCommand: 'uv run pytest tests/ -v',
  cdkStack: 'TransactionifyStack',
});

fs.writeFileSync('.github/workflows/pr.yml', prWorkflow);
```

## Stack-Aware Pipelines

The framework supports environment-aware deployments:

| Environment | Trigger | Purpose |
|-------------|---------|---------|
| `sandbox` | PR open/update | Rapid validation |
| `staging` | PR merge (main) | Integration testing |
| `production` | Manual + gated | Production release |

## Type-Safe Workflow Design

The framework generates GitHub Actions workflows with compile-time safety. Workflow definitions are TypeScript objects that validate structure before YAML generation.

### Compatibility with github-actions-workflow-ts

While this framework uses a lightweight, self-contained type system for workflow generation, it is fully compatible with the design patterns promoted by [`github-actions-workflow-ts`](https://github.com/simonbuchan/github-actions-workflow-ts). Both approaches share the same core principle: **workflows as code** with static type checking.

Key similarities:
- Jobs, steps, and triggers are typed interfaces
- Workflow validation happens at compile time, not at runtime in CI
- YAML emission is deterministic and version-controlled

You can extend the framework's `WorkflowDefinition` type to integrate with `github-actions-workflow-ts` if your organization prefers that specific library.

## DORA Telemetry

Framework constructs automatically emit DORA events:

```typescript
import { DoraTelemetry } from '@gila-software/goldenpath-framework/dora';

const telemetry = new DoraTelemetry({ project: 'transactionify' });
telemetry.recordDeployment({ environment: 'staging', commitSha: 'abc123', success: true });
```

## Inner-Source Contributions

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on adding new language support or CDK patterns.
