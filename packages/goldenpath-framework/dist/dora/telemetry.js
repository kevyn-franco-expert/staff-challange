"use strict";
/**
 * DORA Telemetry — TypeScript Implementation
 *
 * Mirrors the Python CLI telemetry to ensure consistent metric capture
 * regardless of which component generates the event.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DoraTelemetry = void 0;
/**
 * DORA telemetry collector for CDK constructs and workflows.
 */
class DoraTelemetry {
    config;
    constructor(config) {
        this.config = {
            team: 'platform',
            environment: 'unknown',
            ...config,
        };
    }
    createEvent(eventType, params) {
        return {
            timestamp: new Date().toISOString(),
            project: this.config.project,
            team: this.config.team ?? 'platform',
            environment: this.config.environment ?? 'unknown',
            durationSeconds: 0,
            success: true,
            branch: 'main',
            ...params,
            eventType,
        };
    }
    /**
     * Record a deployment event.
     */
    recordDeployment(params) {
        const event = this.createEvent('deployment', {
            ...params,
            environment: params.environment ?? this.config.environment ?? 'unknown',
        });
        this.emit(event);
        return event;
    }
    /**
     * Record a change (merge to main) event.
     */
    recordChange(params) {
        const event = this.createEvent('change', {
            ...params,
            durationSeconds: params.leadTimeSeconds,
        });
        this.emit(event);
        return event;
    }
    /**
     * Record a deployment failure.
     */
    recordFailure(params) {
        const event = this.createEvent('failure', {
            ...params,
            environment: params.environment ?? this.config.environment ?? 'unknown',
            success: false,
            metadata: { error: params.errorMessage },
        });
        this.emit(event);
        return event;
    }
    /**
     * Record an incident recovery.
     */
    recordRecovery(params) {
        const event = this.createEvent('recovery', {
            ...params,
            environment: params.environment ?? this.config.environment ?? 'unknown',
            durationSeconds: params.mttrSeconds,
            metadata: { metric: 'mttr' },
        });
        this.emit(event);
        return event;
    }
    /**
     * Emit event — in production this would send to a centralized metrics store.
     * For PoC, we log to stdout in structured JSON format.
     */
    emit(event) {
        const line = JSON.stringify(event);
        // In production: send to Kinesis, Firehose, or metrics API
        console.log(`[DORA] ${line}`);
    }
    /**
     * Generate audit context for SOC 2 compliance.
     */
    static createAuditContext(overrides) {
        return {
            actor: process.env.USER ?? 'unknown',
            actorEmail: process.env.EMAIL ?? '',
            action: '',
            reason: '',
            sourceIp: '127.0.0.1',
            sessionId: '',
            complianceFramework: 'soc2',
            ...overrides,
        };
    }
}
exports.DoraTelemetry = DoraTelemetry;
//# sourceMappingURL=telemetry.js.map