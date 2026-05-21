#!/usr/bin/env node
/**
 * CDK App Entry Point
 *
 * Usage:
 *   npx cdk synth TransactionifyStack-staging
 *   npx cdk deploy TransactionifyStack-staging
 */

import { App } from 'aws-cdk-lib';
import { TransactionifyStack } from './stack.js';

const app = new App();

const environment = process.env.ENVIRONMENT || 'sandbox';
if (!['sandbox', 'staging', 'production'].includes(environment)) {
  throw new Error(`Invalid environment: ${environment}`);
}

new TransactionifyStack(app, `TransactionifyStack-${environment}`, {
  environment: environment as 'sandbox' | 'staging' | 'production',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  tags: {
    'goldenpath:managed': 'true',
    'goldenpath:version': '0.1.0',
  },
});
