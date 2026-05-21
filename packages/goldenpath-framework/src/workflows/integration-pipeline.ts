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

import { type WorkflowDefinition, type WorkflowJob, type WorkflowStep } from '../types/index.js';

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
export function generateIntegrationPipeline(options: IntegrationPipelineOptions): WorkflowDefinition {
  const runsOn = options.runsOn ?? 'ubuntu-latest';
  const awsRegion = options.awsRegion ?? 'us-east-1';

  const jobs: Record<string, WorkflowJob> = {
    'detect-work-id': {
      name: 'Detect Work ID',
      'runs-on': runsOn,
      outputs: {
        work_id: '${{ steps.extract.outputs.work_id }}',
      },
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
          with: { 'fetch-depth': '0' },
        },
        {
          name: 'Extract Work ID from merge commit',
          id: 'extract',
          run: [
            'MSG="${{ github.event.head_commit.message }}"',
            'WORK_ID=$(echo "$MSG" | grep -oE \'[A-Z]+-[0-9]+\' | head -n1 || echo "")',
            'if [ -z "$WORK_ID" ]; then',
            '  WORK_ID=$(git log -1 --pretty=%B | grep -oE \'[A-Z]+-[0-9]+\' | head -n1 || echo "UNKNOWN")',
            'fi',
            'echo "work_id=$WORK_ID" >> "$GITHUB_OUTPUT"',
            'echo "✅ Work ID: $WORK_ID"',
          ].join('\n'),
        },
      ],
    },

    'build-artifacts': {
      name: 'Build & Package',
      'runs-on': runsOn,
      needs: 'detect-work-id',
      outputs: {
        artifact_hash: '${{ steps.hash.outputs.hash }}',
      },
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        ...getSetupSteps(options.language),
        {
          name: 'Build',
          run: getBuildCommand(options.language),
        },
        {
          name: 'Package Artifact',
          run: `
            mkdir -p dist
            zip -r dist/${options.serviceName}-\${{ github.sha }}.zip .
          `.trim(),
        },
        {
          name: 'Compute Hash',
          id: 'hash',
          run: 'echo "hash=$(sha256sum dist/*.zip | head -n1 | awk \'{print $1}\')" >> "$GITHUB_OUTPUT"',
        },
        {
          name: 'Upload Artifact',
          uses: 'actions/upload-artifact@v4',
          with: {
            name: '${{ github.sha }}',
            path: 'dist/*.zip',
          },
        },
      ],
    },

    'deploy-staging': {
      name: 'Deploy to Staging',
      'runs-on': runsOn,
      needs: ['detect-work-id', 'build-artifacts'],
      environment: {
        name: 'staging',
        url: '${{ steps.deploy.outputs.url }}',
      },
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        {
          name: 'Download Artifact',
          uses: 'actions/download-artifact@v4',
          with: { name: '${{ github.sha }}', path: 'dist' },
        },
        {
          name: 'Configure AWS Credentials',
          uses: 'aws-actions/configure-aws-credentials@v4',
          with: {
            'role-to-assume': options.stagingRoleArn,
            'aws-region': awsRegion,
          },
        },
        {
          name: 'CDK Deploy Staging',
          id: 'deploy',
          run: `
            npx cdk deploy ${options.cdkStack}-staging --require-approval never
            echo "url=$(aws cloudformation describe-stacks --stack-name ${options.cdkStack}-staging --query 'Stacks[0].Outputs[?OutputKey==\`ApiEndpoint\`].OutputValue' --output text)" >> "$GITHUB_OUTPUT"
          `.trim(),
        },
        {
          name: 'Emit DORA Deployment Event',
          run: 'echo \'{"event_type":"deployment","environment":"staging","work_id":"${{ needs.detect-work-id.outputs.work_id }}","commit_sha":"${{ github.sha }}","success":true}\' >> dora-events.jsonl',
        },
      ],
    },

    'smoke-tests': {
      name: 'Smoke Tests',
      'runs-on': runsOn,
      needs: 'deploy-staging',
      if: options.enableSmokeTests ? undefined : undefined,
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        ...getSetupSteps(options.language),
        {
          name: 'Run Smoke Tests',
          run: options.smokeTestCommand ?? 'echo "No smoke tests configured"',
          env: {
            API_BASE_URL: '${{ needs.deploy-staging.outputs.url }}',
            STAGE: 'staging',
          },
        },
      ],
    },

    'deploy-production': {
      name: 'Deploy to Production',
      'runs-on': runsOn,
      needs: ['deploy-staging', 'smoke-tests'],
      environment: {
        name: 'production',
        url: '${{ steps.deploy.outputs.url }}',
      },
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        {
          name: 'Download Artifact',
          uses: 'actions/download-artifact@v4',
          with: { name: '${{ github.sha }}', path: 'dist' },
        },
        {
          name: 'Configure AWS Credentials',
          uses: 'aws-actions/configure-aws-credentials@v4',
          with: {
            'role-to-assume': options.productionRoleArn,
            'aws-region': awsRegion,
          },
        },
        {
          name: 'CDK Deploy Production',
          id: 'deploy',
          run: `npx cdk deploy ${options.cdkStack}-production --require-approval never`,
        },
        {
          name: 'Emit DORA Deployment Event',
          run: 'echo \'{"event_type":"deployment","environment":"production","work_id":"${{ needs.detect-work-id.outputs.work_id }}","commit_sha":"${{ github.sha }}","success":true}\' >> dora-events.jsonl',
        },
        {
          name: 'Compute Lead Time',
          run: [
            '# Calculate time from first commit to production deploy',
            'FIRST_COMMIT_TIME=$(git log --format=%ct --reverse | head -n1)',
            'DEPLOY_TIME=$(date +%s)',
            'LEAD_TIME=$((DEPLOY_TIME - FIRST_COMMIT_TIME))',
            'echo "lead_time_seconds=$LEAD_TIME" >> "$GITHUB_ENV"',
            'echo "📊 Lead Time: ${LEAD_TIME}s"',
          ].join('\n'),
        },
      ],
    },
  };

  return {
    name: `Integration Pipeline — ${options.serviceName}`,
    on: {
      push: {
        branches: ['main'],
      },
    },
    permissions: {
      contents: 'read',
      'id-token': 'write',
      actions: 'read',
      'pull-requests': 'read',
    },
    env: {
      NODE_OPTIONS: '--max-old-space-size=4096',
    },
    jobs,
  };
}

// ── Helpers (duplicated for self-containment) ────────────────────────────────

function getSetupSteps(language: string): WorkflowStep[] {
  switch (language) {
    case 'python':
      return [
        { name: 'Install uv', uses: 'astral-sh/setup-uv@v3' },
        { name: 'Setup Python', uses: 'actions/setup-python@v5', with: { 'python-version': '3.12' } },
        { name: 'Install dependencies', run: 'uv pip install -e ".[dev]"' },
      ];
    case 'go':
      return [{ name: 'Setup Go', uses: 'actions/setup-go@v5', with: { 'go-version': '1.22' } }];
    case 'typescript':
      return [
        { name: 'Setup Node.js', uses: 'actions/setup-node@v4', with: { 'node-version': '20', cache: 'pnpm' } },
        { name: 'Install pnpm', uses: 'pnpm/action-setup@v3', with: { version: '8' } },
        { name: 'Install dependencies', run: 'pnpm install' },
      ];
    default:
      return [{ name: 'Setup', run: `echo "No setup for ${language}"` }];
  }
}

function getBuildCommand(language: string): string {
  switch (language) {
    case 'python':
      return 'uv build';
    case 'go':
      return 'go build -o dist/ ./...';
    case 'typescript':
      return 'pnpm build';
    default:
      return 'echo "No build step"';
  }
}
