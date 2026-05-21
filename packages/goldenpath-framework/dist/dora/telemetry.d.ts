/**
 * DORA Telemetry — TypeScript Implementation
 *
 * Mirrors the Python CLI telemetry to ensure consistent metric capture
 * regardless of which component generates the event.
 */
export interface DoraTelemetryConfig {
    readonly project: string;
    readonly team?: string;
    readonly environment?: string;
    readonly metricsEndpoint?: string;
}
export interface DoraEvent {
    readonly eventType: 'deployment' | 'change' | 'failure' | 'recovery' | 'validation';
    readonly timestamp: string;
    readonly workId: string;
    readonly project: string;
    readonly team: string;
    readonly environment: string;
    readonly commitSha: string;
    readonly branch: string;
    readonly durationSeconds: number;
    readonly success: boolean;
    readonly metadata?: Record<string, unknown>;
}
export interface AuditContext {
    readonly actor: string;
    readonly actorEmail: string;
    readonly action: string;
    readonly reason: string;
    readonly sourceIp: string;
    readonly sessionId: string;
    readonly complianceFramework: 'soc2' | 'iso27001';
}
/**
 * DORA telemetry collector for CDK constructs and workflows.
 */
export declare class DoraTelemetry {
    private readonly config;
    constructor(config: DoraTelemetryConfig);
    private createEvent;
    /**
     * Record a deployment event.
     */
    recordDeployment(params: {
        workId: string;
        commitSha: string;
        environment?: string;
        success?: boolean;
        durationSeconds?: number;
    }): DoraEvent;
    /**
     * Record a change (merge to main) event.
     */
    recordChange(params: {
        workId: string;
        commitSha: string;
        leadTimeSeconds: number;
        branch?: string;
    }): DoraEvent;
    /**
     * Record a deployment failure.
     */
    recordFailure(params: {
        workId: string;
        commitSha: string;
        environment?: string;
        errorMessage: string;
    }): DoraEvent;
    /**
     * Record an incident recovery.
     */
    recordRecovery(params: {
        workId: string;
        commitSha: string;
        environment?: string;
        mttrSeconds: number;
    }): DoraEvent;
    /**
     * Emit event — in production this would send to a centralized metrics store.
     * For PoC, we log to stdout in structured JSON format.
     */
    private emit;
    /**
     * Generate audit context for SOC 2 compliance.
     */
    static createAuditContext(overrides?: Partial<AuditContext>): AuditContext;
}
//# sourceMappingURL=telemetry.d.ts.map