# Transactionify — Golden Path Integration Example

> **Reference implementation showing how to integrate the Golden Path ecosystem with the existing Transactionify microservice**
>
> **Upstream Repository**: https://github.com/rrgarciach/transactionify

This example demonstrates how to apply the Golden Path Platform to the `transactionify` microservice — an existing AWS Lambda + API Gateway + DynamoDB project that handles transaction processing.

## Understanding the Base Repository

Transactionify (https://github.com/rrgarciach/transactionify) provides:

- **Language**: Python 3.9+ (Lambda handlers)
- **IaC**: AWS CDK (TypeScript)
- **API**: REST via API Gateway
  - `POST /api/v1/accounts` — Create account
  - `POST /api/v1/accounts/{id}/payments` — Create payment
  - `GET /api/v1/accounts/{id}/balance` — Get balance
  - `GET /api/v1/accounts/{id}/transactions` — List transactions (paginated)
- **Tests**: pytest under `test/unit/src/python/`
- **Quality**: black, flake8, mypy

## Integration Strategy

Instead of replacing the existing codebase, the Golden Path **wraps and enhances** it:

```
transactionify/                          (forked from upstream)
├── src/python/                          (existing handlers)
│   └── transactionify/
│       ├── handlers/
│       │   ├── authorizer.py
│       │   ├── accounts.py
│       │   ├── payments.py
│       │   └── transactions.py
│       └── models/
├── test/unit/src/python/                (existing tests)
├── infra/                               (NEW — Golden Path CDK)
│   ├── stack.ts
│   └── bin.ts
├── scripts/                             (NEW)
│   └── generate-workflows.ts
├── .github/
│   └── workflows/                       (NEW — generated)
│       ├── pr.yml
│       └── integration.yml
├── goldenpath.yaml                      (NEW — Golden Path config)
├── docker-compose.local.yml             (NEW — LocalStack)
└── pyproject.toml                       (NEW — replaces requirements.txt approach)
```

## Step-by-Step Integration

### 1. Fork the Repository

```bash
# Fork https://github.com/rrgarciach/transactionify to your org
git clone https://github.com/YOUR_ORG/transactionify.git
cd transactionify
```

### 2. Initialize Golden Path Configuration

```bash
# Install the CLI
uv tool install git+https://github.com/gila-software/goldenpath-platform.git#subdirectory=packages/goldenpath-cli

# Initialize Golden Path conventions
goldenpath init --name transactionify --language python --work-id FIN-100

# This creates:
#   goldenpath.yaml
#   .github/PULL_REQUEST_TEMPLATE.md
#   .github/CODEOWNERS
#   .gitignore enhancements
```

### 3. Install the Framework

```bash
# Install pnpm if not present
curl -fsSL https://get.pnpm.io/install.sh | sh -

# Install the framework
pnpm add "https://github.com/gila-software/goldenpath-platform.git#path=packages/goldenpath-framework"

# Install CDK peer dependencies
pnpm add aws-cdk-lib constructs
```

### 4. Create the CDK Stack (`infra/stack.ts`)

```typescript
import { App, StackProps } from 'aws-cdk-lib';
import { ServiceStack } from '@gila-software/goldenpath-framework';

export interface TransactionifyStackProps extends StackProps {
  readonly environment: 'sandbox' | 'staging' | 'production';
}

export class TransactionifyStack extends ServiceStack {
  constructor(scope: App, id: string, props: TransactionifyStackProps) {
    super(scope, id, {
      ...props,
      serviceName: 'transactionify',
      team: 'payments',
      environment: props.environment,
      runtime: 'python3.12',
      language: 'python',
      handlers: [
        {
          name: 'Authorizer',
          path: 'src/python/transactionify/handlers/authorizer.py',
          memorySize: 256,
          timeoutSeconds: 5,
        },
        {
          name: 'AccountsHandler',
          path: 'src/python/transactionify/handlers/accounts.py',
          memorySize: 512,
          timeoutSeconds: 30,
          environment: { TABLE_NAME: 'Accounts' },
        },
        {
          name: 'PaymentsHandler',
          path: 'src/python/transactionify/handlers/payments.py',
          memorySize: 512,
          timeoutSeconds: 30,
          environment: { TABLE_NAME: 'Payments' },
        },
        {
          name: 'TransactionsHandler',
          path: 'src/python/transactionify/handlers/transactions.py',
          memorySize: 512,
          timeoutSeconds: 30,
          environment: { TABLE_NAME: 'Transactions' },
        },
      ],
      apiRoutes: [
        {
          path: '/api/v1/accounts',
          method: 'POST',
          handler: 'AccountsHandler',
          authorization: 'iam',
        },
        {
          path: '/api/v1/accounts/{id}/payments',
          method: 'POST',
          handler: 'PaymentsHandler',
          authorization: 'iam',
        },
        {
          path: '/api/v1/accounts/{id}/balance',
          method: 'GET',
          handler: 'AccountsHandler',
          authorization: 'none',
        },
        {
          path: '/api/v1/accounts/{id}/transactions',
          method: 'GET',
          handler: 'TransactionsHandler',
          authorization: 'none',
        },
      ],
      enableDynamoDB: true,
      dynamoTableName: `Transactionify-${props.environment}`,
      enableXRay: true,
      tags: {
        domain: 'payments',
        'cost-center': 'engineering-payments',
        'data-classification': 'financial',
      },
    });
  }
}
```

### 5. Generate CI/CD Workflows

```typescript
// scripts/generate-workflows.ts
import {
  generatePRPipeline,
  generateIntegrationPipeline,
  toGitHubActionsYAML,
} from '@gila-software/goldenpath-framework';
import * as fs from 'fs';

// PR Pipeline
const pr = generatePRPipeline({
  serviceName: 'transactionify',
  language: 'python',
  cdkStack: 'TransactionifyStack',
  enableSandboxDeploy: true,
  // Adapted to upstream test structure
  testCommand: 'cd test/unit/src/python && pytest -v --cov=src/python/transactionify --cov-report=xml',
  lintCommand: 'black --check src/python/ && flake8 src/python/ && mypy src/python/',
});

fs.writeFileSync('.github/workflows/pr.yml', toGitHubActionsYAML(pr));

// Integration Pipeline
const integration = generateIntegrationPipeline({
  serviceName: 'transactionify',
  language: 'python',
  cdkStack: 'TransactionifyStack',
  stagingRoleArn: 'arn:aws:iam::123456789012:role/TransactionifyStagingDeployRole',
  productionRoleArn: 'arn:aws:iam::123456789012:role/TransactionifyProductionDeployRole',
  enableSmokeTests: true,
  smokeTestCommand: 'cd test/smoke && pytest -v',
});

fs.writeFileSync('.github/workflows/integration.yml', toGitHubActionsYAML(integration));
```

Run it:

```bash
pnpm tsx scripts/generate-workflows.ts
```

### 6. Bootstrap Local Environment

```bash
goldenpath local env --bootstrap

# Start LocalStack
docker-compose -f docker-compose.local.yml up -d

# Initialize DynamoDB tables
./scripts/init-localstack.sh

# Run existing tests locally (no cloud latency)
cd test/unit/src/python
pytest -v
```

### 7. Install Git Hooks

```bash
goldenpath hooks install
```

This enforces:
- Work ID in commit messages (`FIN-xxx`)
- Pre-push validation (black, flake8, mypy, pytest)
- Golden Path standards

### 8. Update `goldenpath.yaml`

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
  local_metrics_path: .goldenpath/dora.jsonl

local_env:
  use_localstack: true
  localstack_services:
    - lambda
    - apigateway
    - dynamodb
    - sns
    - sqs
  docker_compose_path: docker-compose.local.yml
```

## What Changes vs. Upstream?

| Aspect | Upstream Repo | With Golden Path |
|--------|---------------|------------------|
| **CI/CD** | None / manual | Auto-generated type-safe workflows |
| **IaC** | Raw CDK or manual | `ServiceStack` with DORA + X-Ray + alarms |
| **Local Dev** | None | LocalStack + docker-compose |
| **Git Governance** | Manual | Automated hooks + standards |
| **DORA Metrics** | None | Automatic emission on every deployment |
| **Security** | Manual review | TruffleHog + Trivy + Amazon Q |
| **PR Process** | Informal | Standardized template + 2-reviewers + Work ID |

## Verification Checklist

After integration, verify:

- [ ] `goldenpath standards --strict` passes
- [ ] `goldenpath validate work-id` passes on feature branches
- [ ] `cdk synth` produces valid CloudFormation
- [ ] `.github/workflows/pr.yml` triggers on PR open
- [ ] `.github/workflows/integration.yml` triggers on merge to main
- [ ] LocalStack runs `pytest` with zero AWS latency
- [ ] DORA events appear in `.goldenpath/dora.jsonl`

## Compliance Mapping

| Requirement | Evidence in Fork |
|-------------|------------------|
| Work ID in branches/commits | `commit-msg` hook + `goldenpath validate` |
| Two-reviewer rule | Branch protection + PR template |
| PR Pipeline | `.github/workflows/pr.yml` (generated) |
| Integration Pipeline | `.github/workflows/integration.yml` (generated) |
| DORA telemetry | `DoraTelemetry` in CDK + CLI `dora report` |
| SOC 2 audit trail | `AuditContext` in every deployment event |
| Local environment | `docker-compose.local.yml` + LocalStack |
