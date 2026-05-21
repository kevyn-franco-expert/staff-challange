/**
 * Shared types for Golden Path Framework.
 *
 * These types ensure consistency across CDK constructs, pipeline generators,
 * and DORA telemetry regardless of the application language.
 */

/** Supported runtime languages for Lambda functions. */
export type RuntimeLanguage = 'python' | 'go' | 'typescript' | 'clojure' | 'java' | 'dotnet';

/** AWS Lambda runtime mapping. */
export type LambdaRuntime =
  | 'python3.12'
  | 'python3.11'
  | 'python3.10'
  | 'go1.x'
  | 'nodejs20.x'
  | 'nodejs18.x'
  | 'java21'
  | 'provided.al2023';

/** Deployment environment. */
export type Environment = 'local' | 'sandbox' | 'staging' | 'production';

/** API Gateway route definition. */
export interface ApiRoute {
  readonly path: string;
  readonly method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  readonly handler: string;
  readonly authorization?: 'none' | 'iam' | 'cognito';
}

/** Lambda handler definition. */
export interface HandlerDefinition {
  readonly name: string;
  readonly path: string;
  readonly memorySize?: number;
  readonly timeoutSeconds?: number;
  readonly environment?: Record<string, string>;
}

/** Golden Path service configuration. */
export interface ServiceConfig {
  readonly serviceName: string;
  readonly team: string;
  readonly language: RuntimeLanguage;
  readonly runtime: LambdaRuntime;
  readonly handlers: HandlerDefinition[];
  readonly apiRoutes: ApiRoute[];
  readonly environment: Environment;
  readonly tags: Record<string, string>;
}

/** GitHub Actions job step. */
export interface WorkflowStep {
  readonly name: string;
  readonly uses?: string;
  readonly run?: string;
  readonly with?: Record<string, string | number | boolean>;
  readonly env?: Record<string, string>;
  readonly if?: string;
  readonly id?: string;
}

/** GitHub Actions job definition. */
export interface WorkflowJob {
  readonly name?: string;
  readonly 'runs-on': string;
  readonly needs?: string | string[];
  readonly steps: WorkflowStep[];
  readonly environment?: {
    readonly name: string;
    readonly url?: string;
  };
  readonly outputs?: Record<string, string>;
  readonly if?: string;
}

/** GitHub Actions workflow definition. */
export interface WorkflowDefinition {
  readonly name: string;
  readonly on: Record<string, unknown>;
  readonly jobs: Record<string, WorkflowJob>;
  readonly env?: Record<string, string>;
  readonly permissions?: Record<string, string>;
}

/** DORA core metric names. */
export type DoraMetric = 'deployment_frequency' | 'lead_time' | 'change_failure_rate' | 'mttr';

/** SOC 2 audit context. */
export interface AuditContext {
  readonly actor: string;
  readonly actorEmail: string;
  readonly action: string;
  readonly reason: string;
  readonly sourceIp: string;
  readonly sessionId: string;
  readonly complianceFramework: 'soc2' | 'iso27001';
}

/** Universal Work ID reference. */
export interface WorkId {
  readonly prefix: string;
  readonly number: number;
  readonly fullId: string;
}

/** Parsed Git metadata. */
export interface GitMetadata {
  readonly repository: string;
  readonly branch: string;
  readonly commitSha: string;
  readonly commitMessage: string;
  readonly authorName: string;
  readonly authorEmail: string;
  readonly commitTimestamp: string;
  readonly remoteUrl: string | null;
}
