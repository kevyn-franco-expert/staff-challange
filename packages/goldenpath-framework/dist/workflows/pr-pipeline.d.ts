/**
 * PR Pipeline Workflow Generator
 *
 * Generates type-safe GitHub Actions workflow definitions for Pull Request
 * validation. The PR pipeline focuses on rapid feedback:
 *
 * Stages:
 * 1. Small Tests (Unit, PBT, API Contract)
 * 2. Security Scan
 * 3. Standards Validation
 * 4. Sandbox Deployment (optional, gated by label)
 */
import { type WorkflowDefinition } from '../types/index.js';
export interface PRPipelineOptions {
    readonly serviceName: string;
    readonly language: 'python' | 'go' | 'typescript' | 'clojure';
    readonly runsOn?: string;
    readonly testCommand?: string;
    readonly lintCommand?: string;
    readonly cdkStack?: string;
    readonly enableSandboxDeploy?: boolean;
    readonly awsRegion?: string;
}
/**
 * Generate a PR pipeline workflow definition.
 *
 * @param options - Pipeline configuration
 * @returns Type-safe workflow definition
 */
export declare function generatePRPipeline(options: PRPipelineOptions): WorkflowDefinition;
//# sourceMappingURL=pr-pipeline.d.ts.map