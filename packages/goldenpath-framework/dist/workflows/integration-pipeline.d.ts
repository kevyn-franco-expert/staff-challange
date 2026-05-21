/**
 * Integration Pipeline Workflow Generator
 *
 * Generates the post-merge pipeline that deploys through staging to production.
 * This pipeline represents the "Integration" phase of the CI/CD lifecycle.
 *
 * Stages:
 * 1. Final Validation (re-run tests on main)
 * 2. Staging Deployment
 * 3. Smoke Tests
 * 4. Production Deployment (gated)
 * 5. DORA Telemetry Export
 */
import { type WorkflowDefinition } from '../types/index.js';
export interface IntegrationPipelineOptions {
    readonly serviceName: string;
    readonly language: 'python' | 'go' | 'typescript' | 'clojure';
    readonly runsOn?: string;
    readonly cdkStack: string;
    readonly awsRegion?: string;
    readonly stagingRoleArn: string;
    readonly productionRoleArn: string;
    readonly enableSmokeTests?: boolean;
    readonly smokeTestCommand?: string;
}
/**
 * Generate an Integration (post-merge) pipeline workflow definition.
 */
export declare function generateIntegrationPipeline(options: IntegrationPipelineOptions): WorkflowDefinition;
//# sourceMappingURL=integration-pipeline.d.ts.map