/**
 * Workflow YAML Generator
 *
 * Converts type-safe WorkflowDefinition objects into GitHub Actions YAML.
 * This is the "compiler" from TypeScript types to executable CI/CD configuration.
 */
import { type WorkflowDefinition } from '../types/index.js';
/**
 * Serialize a workflow definition to GitHub Actions YAML.
 *
 * @param definition - Type-safe workflow definition
 * @returns Valid GitHub Actions YAML string
 */
export declare function toGitHubActionsYAML(definition: WorkflowDefinition): string;
/**
 * Write workflow definition to a file.
 */
export declare function writeWorkflow(definition: WorkflowDefinition, filePath: string): void;
/**
 * Validate that a workflow definition has required fields.
 */
export declare function validateWorkflow(definition: WorkflowDefinition): string[];
//# sourceMappingURL=generator.d.ts.map