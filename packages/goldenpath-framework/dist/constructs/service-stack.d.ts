/**
 * Golden Path Service Stack — Reusable CDK Construct
 *
 * Provides a standardized AWS infrastructure pattern for microservices:
 * - Lambda functions with consistent IAM, logging, and tracing
 * - API Gateway REST API with route mapping
 * - CloudWatch alarms and dashboards
 * - DynamoDB table (optional, for stateful services)
 * - SNS topic for async events
 *
 * This construct is "polyglot-ready" — the runtime language is configurable
 * while the infrastructure patterns remain consistent.
 */
import * as cdk from 'aws-cdk-lib';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sns from 'aws-cdk-lib/aws-sns';
import { Construct } from 'constructs';
import { type ApiRoute, type Environment, type HandlerDefinition } from '../types/index.js';
import { DoraTelemetry } from '../dora/telemetry.js';
export interface ServiceStackProps extends cdk.StackProps {
    readonly serviceName: string;
    readonly team: string;
    readonly environment: Environment;
    readonly runtime: string;
    readonly language: string;
    readonly handlers: HandlerDefinition[];
    readonly apiRoutes: ApiRoute[];
    readonly enableDynamoDB?: boolean;
    readonly dynamoTableName?: string;
    readonly enableXRay?: boolean;
    readonly tags?: Record<string, string>;
}
/**
 * Standardized service stack implementing Golden Path infrastructure patterns.
 *
 * @example
 * ```ts
 * new ServiceStack(app, 'TransactionifyStack', {
 *   serviceName: 'transactionify',
 *   environment: 'staging',
 *   runtime: 'python3.12',
 *   handlers: [{ name: 'Process', path: 'src/process.py' }],
 *   apiRoutes: [{ path: '/tx', method: 'POST', handler: 'Process' }],
 * });
 * ```
 */
export declare class ServiceStack extends cdk.Stack {
    readonly api: apigw.RestApi;
    readonly functions: Map<string, lambda.Function>;
    readonly table?: dynamodb.Table;
    readonly topic: sns.Topic;
    readonly doraTelemetry: DoraTelemetry;
    constructor(scope: Construct, id: string, props: ServiceStackProps);
    private createLambda;
    private resolveResource;
    private createAlarms;
}
//# sourceMappingURL=service-stack.d.ts.map