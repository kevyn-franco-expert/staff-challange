/**
 * Transactionify CDK Stack
 *
 * Reference implementation using the Golden Path Framework.
 * This stack deploys a transaction processing microservice with:
 * - Lambda functions (Python)
 * - API Gateway REST API
 * - DynamoDB table
 * - SNS topic for events
 * - CloudWatch alarms
 */

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
          name: 'ProcessTransaction',
          path: 'src/handlers/process.py',
          memorySize: props.environment === 'production' ? 1024 : 512,
          timeoutSeconds: 30,
          environment: {
            TABLE_NAME: 'Transactions',
            VALIDATION_MODE: 'strict',
          },
        },
        {
          name: 'ValidateTransaction',
          path: 'src/handlers/validate.py',
          memorySize: 256,
          timeoutSeconds: 10,
        },
        {
          name: 'GetTransaction',
          path: 'src/handlers/get.py',
          memorySize: 256,
          timeoutSeconds: 5,
        },
      ],
      apiRoutes: [
        {
          path: '/transactions',
          method: 'POST',
          handler: 'ProcessTransaction',
          authorization: 'iam',
        },
        {
          path: '/transactions/{id}',
          method: 'GET',
          handler: 'GetTransaction',
          authorization: 'none',
        },
        {
          path: '/transactions/{id}/validate',
          method: 'POST',
          handler: 'ValidateTransaction',
          authorization: 'iam',
        },
      ],
      enableDynamoDB: true,
      dynamoTableName: `Transactions-${props.environment}`,
      enableXRay: true,
      tags: {
        domain: 'payments',
        'cost-center': 'engineering-payments',
        'data-classification': 'financial',
      },
    });
  }
}
