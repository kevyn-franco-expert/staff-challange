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
export class DoraTelemetry {
  private readonly config: DoraTelemetryConfig;

  constructor(config: DoraTelemetryConfig) {
    this.config = {
      team: 'platform',
      environment: 'unknown',
      ...config,
    };
  }

  private createEvent(
    eventType: DoraEvent['eventType'],
    params: Partial<DoraEvent> & { workId: string; commitSha: string }
  ): DoraEvent {
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
  recordDeployment(params: {
    workId: string;
    commitSha: string;
    environment?: string;
    success?: boolean;
    durationSeconds?: number;
  }): DoraEvent {
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
  recordChange(params: {
    workId: string;
    commitSha: string;
    leadTimeSeconds: number;
    branch?: string;
  }): DoraEvent {
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
  recordFailure(params: {
    workId: string;
    commitSha: string;
    environment?: string;
    errorMessage: string;
  }): DoraEvent {
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
  recordRecovery(params: {
    workId: string;
    commitSha: string;
    environment?: string;
    mttrSeconds: number;
  }): DoraEvent {
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
  private emit(event: DoraEvent): void {
    const line = JSON.stringify(event);
    // In production: send to Kinesis, Firehose, or metrics API
    console.log(`[DORA] ${line}`);
  }

  /**
   * Generate audit context for SOC 2 compliance.
   */
  static createAuditContext(overrides?: Partial<AuditContext>): AuditContext {
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
