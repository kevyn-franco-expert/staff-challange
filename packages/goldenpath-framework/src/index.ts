/**
 * Golden Path Framework — Enterprise CI/CD & Infrastructure Patterns
 *
 * @packageDocumentation
 */

// CDK Constructs
export { ServiceStack, ServiceStackProps } from './constructs/service-stack.js';

// Workflow Generators
export { generatePRPipeline, PRPipelineOptions } from './workflows/pr-pipeline.js';
export {
  generateIntegrationPipeline,
  IntegrationPipelineOptions,
} from './workflows/integration-pipeline.js';

// YAML Generator
export {
  toGitHubActionsYAML,
  writeWorkflow,
  validateWorkflow,
} from './pipelines/generator.js';

// DORA Telemetry
export { DoraTelemetry, DoraTelemetryConfig, DoraEvent } from './dora/telemetry.js';

// Shared Types
export * from './types/index.js';
