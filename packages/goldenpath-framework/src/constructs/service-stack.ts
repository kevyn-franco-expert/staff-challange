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
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as sns from 'aws-cdk-lib/aws-sns';
import { Construct } from 'constructs';
import * as fs from 'fs';

import { type ApiRoute, type Environment, type HandlerDefinition } from '../types/index.js';
import { DoraTelemetry } from '../dora/telemetry.js';

export interface ServiceStackProps extends cdk.StackProps {
  readonly serviceName: string;
  readonly team: string;
  readonly environment: Environment;
  readonly runtime: string; // e.g., 'python3.12', 'nodejs20.x'
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
export class ServiceStack extends cdk.Stack {
  public readonly api: apigw.RestApi;
  public readonly functions: Map<string, lambda.Function> = new Map();
  public readonly table?: dynamodb.Table;
  public readonly topic: sns.Topic;
  public readonly doraTelemetry: DoraTelemetry;

  constructor(scope: Construct, id: string, props: ServiceStackProps) {
    super(scope, id, props);

    // ── Tags ──────────────────────────────────────────────────────────────
    cdk.Tags.of(this).add('service', props.serviceName);
    cdk.Tags.of(this).add('team', props.team);
    cdk.Tags.of(this).add('environment', props.environment);
    cdk.Tags.of(this).add('managed-by', 'goldenpath-framework');
    if (props.tags) {
      Object.entries(props.tags).forEach(([k, v]) => cdk.Tags.of(this).add(k, v));
    }

    // ── DORA Telemetry ────────────────────────────────────────────────────
    this.doraTelemetry = new DoraTelemetry({
      project: props.serviceName,
      environment: props.environment,
    });

    // ── SNS Topic for async events ────────────────────────────────────────
    this.topic = new sns.Topic(this, 'EventsTopic', {
      topicName: `${props.serviceName}-${props.environment}-events`,
      displayName: `${props.serviceName} Events (${props.environment})`,
    });

    // ── DynamoDB (optional) ───────────────────────────────────────────────
    if (props.enableDynamoDB) {
      this.table = new dynamodb.Table(this, 'MainTable', {
        tableName: props.dynamoTableName || `${props.serviceName}-${props.environment}`,
        partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
        sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        pointInTimeRecovery: props.environment === 'production',
        removalPolicy:
          props.environment === 'production'
            ? cdk.RemovalPolicy.RETAIN
            : cdk.RemovalPolicy.DESTROY,
      });
    }

    // ── Lambda Functions ──────────────────────────────────────────────────
    for (const handler of props.handlers) {
      const fn = this.createLambda(props, handler);
      this.functions.set(handler.name, fn);

      // Grant DynamoDB access if table exists
      if (this.table) {
        this.table.grantReadWriteData(fn);
      }

      // Grant SNS publish
      this.topic.grantPublish(fn);
    }

    // ── API Gateway ───────────────────────────────────────────────────────
    this.api = new apigw.RestApi(this, 'Api', {
      restApiName: `${props.serviceName}-${props.environment}`,
      description: `${props.serviceName} API (${props.environment})`,
      deployOptions: {
        stageName: props.environment,
        tracingEnabled: props.enableXRay ?? true,
        loggingLevel: apigw.MethodLoggingLevel.INFO,
        dataTraceEnabled: props.environment !== 'production',
        metricsEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigw.Cors.ALL_ORIGINS,
        allowMethods: apigw.Cors.ALL_METHODS,
      },
    });

    // Map routes
    for (const route of props.apiRoutes) {
      const fn = this.functions.get(route.handler);
      if (!fn) {
        throw new Error(`Handler '${route.handler}' not defined for route ${route.method} ${route.path}`);
      }

      const integration = new apigw.LambdaIntegration(fn, {
        proxy: true,
      });

      const resource = this.resolveResource(this.api.root, route.path);
      resource.addMethod(route.method, integration, {
        authorizationType:
          route.authorization === 'iam'
            ? apigw.AuthorizationType.IAM
            : apigw.AuthorizationType.NONE,
      });
    }

    // ── CloudWatch Alarms ─────────────────────────────────────────────────
    this.createAlarms(props);

    // ── Stack Outputs ─────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'ApiEndpoint', {
      value: this.api.url,
      description: 'API Gateway endpoint',
    });

    new cdk.CfnOutput(this, 'TopicArn', {
      value: this.topic.topicArn,
      description: 'SNS Topic ARN',
    });
  }

  private createLambda(props: ServiceStackProps, handler: HandlerDefinition): lambda.Function {
    const logGroup = new logs.LogGroup(this, `${handler.name}LogGroup`, {
      logGroupName: `/aws/lambda/${props.serviceName}-${handler.name}-${props.environment}`,
      retention: props.environment === 'production' ? logs.RetentionDays.ONE_MONTH : logs.RetentionDays.ONE_WEEK,
    });

    // Use inline code for test environments where assets don't exist
    const assetPath = `./dist/${handler.path}`;
    const code = fs.existsSync(assetPath)
      ? lambda.Code.fromAsset(assetPath)
      : lambda.Code.fromInline('def handler(event, context): return {"statusCode": 200}');

    const fn = new lambda.Function(this, handler.name, {
      functionName: `${props.serviceName}-${handler.name}-${props.environment}`,
      runtime: resolveRuntime(props.runtime),
      handler: handler.path.includes('.') ? handler.path.split('.').slice(-2).join('.') : 'index.handler',
      code,
      memorySize: handler.memorySize ?? 512,
      timeout: cdk.Duration.seconds(handler.timeoutSeconds ?? 30),
      environment: {
        ...handler.environment,
        SERVICE_NAME: props.serviceName,
        ENVIRONMENT: props.environment,
        SNS_TOPIC_ARN: this.topic.topicArn,
        ...(this.table ? { TABLE_NAME: this.table.tableName } : {}),
        POWERTOOLS_SERVICE_NAME: props.serviceName,
        POWERTOOLS_LOG_LEVEL: props.environment === 'production' ? 'INFO' : 'DEBUG',
      },
      logGroup,
      tracing: lambda.Tracing.ACTIVE,
    });

    // X-Ray permissions
    fn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['xray:PutTraceSegments', 'xray:PutTelemetryRecords'],
        resources: ['*'],
      })
    );

    return fn;
  }

  private resolveResource(parent: apigw.IResource, path: string): apigw.IResource {
    const segments = path.split('/').filter(Boolean);
    let current = parent;
    for (const segment of segments) {
      const clean = segment.replace(/[{}]/g, '');
      const existing = current.getResource(clean);
      current = existing || current.addResource(clean);
    }
    return current;
  }

  private createAlarms(props: ServiceStackProps): void {
    for (const [name, fn] of this.functions) {
      const alarm = new cloudwatch.Alarm(this, `${name}ErrorAlarm`, {
        metric: fn.metricErrors({
          period: cdk.Duration.minutes(1),
          statistic: 'sum',
        }),
        threshold: 5,
        evaluationPeriods: 2,
        comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        alarmName: `${props.serviceName}-${name}-${props.environment}-errors`,
      });

      // Add tag for DORA incident correlation
      cdk.Tags.of(alarm).add('dora-metric', 'change_failure_rate');
    }
  }
}

function resolveRuntime(runtime: string): lambda.Runtime {
  const map: Record<string, lambda.Runtime> = {
    'python3.12': lambda.Runtime.PYTHON_3_12,
    'python3.11': lambda.Runtime.PYTHON_3_11,
    'python3.10': lambda.Runtime.PYTHON_3_10,
    'python3.9': lambda.Runtime.PYTHON_3_9,
    'nodejs20.x': lambda.Runtime.NODEJS_20_X,
    'nodejs18.x': lambda.Runtime.NODEJS_18_X,
    'go1.x': lambda.Runtime.GO_1_X,
    'java21': lambda.Runtime.JAVA_21,
    'provided.al2023': lambda.Runtime.PROVIDED_AL2023,
  };
  return map[runtime] ?? lambda.Runtime.PROVIDED_AL2023;
}
