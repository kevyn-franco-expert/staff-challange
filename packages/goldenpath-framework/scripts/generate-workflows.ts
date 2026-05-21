/**
 * Workflow Generator Script
 *
 * Usage: pnpm generate-workflows
 *
 * Generates GitHub Actions YAML files from TypeScript definitions.
 * This ensures CI/CD configurations are type-safe and version-controlled.
 */

import * as fs from 'fs';
import * as path from 'path';

import { generatePRPipeline } from '../src/workflows/pr-pipeline.js';
import { generateIntegrationPipeline } from '../src/workflows/integration-pipeline.js';
import { toGitHubActionsYAML } from '../src/pipelines/generator.js';

const OUTPUT_DIR = path.join(process.cwd(), '.github', 'workflows');

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function main(): void {
  const serviceName = process.env.SERVICE_NAME || 'transactionify';
  const language = (process.env.SERVICE_LANGUAGE || 'python') as 'python' | 'go' | 'typescript';
  const cdkStack = process.env.CDK_STACK || 'TransactionifyStack';

  console.log(`Generating workflows for: ${serviceName} (${language})`);

  ensureDir(OUTPUT_DIR);

  // PR Pipeline
  const prWorkflow = generatePRPipeline({
    serviceName,
    language,
    cdkStack,
    enableSandboxDeploy: true,
  });
  const prYaml = toGitHubActionsYAML(prWorkflow);
  fs.writeFileSync(path.join(OUTPUT_DIR, 'pr.yml'), prYaml, 'utf-8');
  console.log('✅ Generated .github/workflows/pr.yml');

  // Integration Pipeline
  const integrationWorkflow = generateIntegrationPipeline({
    serviceName,
    language,
    cdkStack,
    stagingRoleArn: process.env.AWS_STAGING_ROLE_ARN || 'arn:aws:iam::STAGING:role/DeployRole',
    productionRoleArn: process.env.AWS_PRODUCTION_ROLE_ARN || 'arn:aws:iam::PROD:role/DeployRole',
    enableSmokeTests: true,
  });
  const integrationYaml = toGitHubActionsYAML(integrationWorkflow);
  fs.writeFileSync(path.join(OUTPUT_DIR, 'integration.yml'), integrationYaml, 'utf-8');
  console.log('✅ Generated .github/workflows/integration.yml');

  console.log('\nWorkflow generation complete!');
}

main();
