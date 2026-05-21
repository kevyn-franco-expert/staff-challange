/**
 * Transactionify Workflow Generator
 *
 * Generates GitHub Actions workflows using the Golden Path Framework.
 *
 * Usage:
 *   pnpm tsx scripts/generate-workflows.ts
 */

import * as fs from 'fs';
import * as path from 'path';

import {
  generatePRPipeline,
  generateIntegrationPipeline,
  toGitHubActionsYAML,
} from '@gila-software/goldenpath-framework';

const WORKFLOWS_DIR = path.join(process.cwd(), '.github', 'workflows');

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function main(): void {
  ensureDir(WORKFLOWS_DIR);

  // ── PR Pipeline ────────────────────────────────────────────────────────────
  const prWorkflow = generatePRPipeline({
    serviceName: 'transactionify',
    language: 'python',
    cdkStack: 'TransactionifyStack',
    enableSandboxDeploy: true,
    testCommand: 'uv run pytest tests/ -v --cov=src --cov-report=xml',
    lintCommand: 'uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/',
    awsRegion: 'us-east-1',
  });

  fs.writeFileSync(
    path.join(WORKFLOWS_DIR, 'pr.yml'),
    toGitHubActionsYAML(prWorkflow),
    'utf-8',
  );
  console.log('✅ Generated .github/workflows/pr.yml');

  // ── Integration Pipeline ───────────────────────────────────────────────────
  const integrationWorkflow = generateIntegrationPipeline({
    serviceName: 'transactionify',
    language: 'python',
    cdkStack: 'TransactionifyStack',
    stagingRoleArn:
      process.env.AWS_STAGING_ROLE_ARN ||
      'arn:aws:iam::123456789012:role/TransactionifyStagingDeployRole',
    productionRoleArn:
      process.env.AWS_PRODUCTION_ROLE_ARN ||
      'arn:aws:iam::123456789012:role/TransactionifyProductionDeployRole',
    enableSmokeTests: true,
    smokeTestCommand: 'uv run pytest tests/smoke/ -v',
    awsRegion: 'us-east-1',
  });

  fs.writeFileSync(
    path.join(WORKFLOWS_DIR, 'integration.yml'),
    toGitHubActionsYAML(integrationWorkflow),
    'utf-8',
  );
  console.log('✅ Generated .github/workflows/integration.yml');

  console.log('\n🚀 Workflows generated successfully!');
  console.log('Next: Commit these files and push to trigger the PR pipeline.');
}

main();
