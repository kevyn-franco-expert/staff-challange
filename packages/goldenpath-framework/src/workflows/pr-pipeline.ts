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

import { type WorkflowDefinition, type WorkflowJob, type WorkflowStep } from '../types/index.js';

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
export function generatePRPipeline(options: PRPipelineOptions): WorkflowDefinition {
  const runsOn = options.runsOn ?? 'ubuntu-latest';
  const awsRegion = options.awsRegion ?? 'us-east-1';

  // Language-specific defaults
  const testCmd = options.testCommand ?? getDefaultTestCommand(options.language);
  const lintCmd = options.lintCommand ?? getDefaultLintCommand(options.language);

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
          name: 'Extract Work ID',
          id: 'extract',
          run: [
            'BRANCH="${{ github.head_ref }}"',
            'WORK_ID=$(echo "$BRANCH" | grep -oE \'[A-Z]+-[0-9]+\' || echo "")',
            'echo "work_id=$WORK_ID" >> "$GITHUB_OUTPUT"',
            'if [ -z "$WORK_ID" ]; then',
            '  echo "❌ No Work ID found in branch name: $BRANCH"',
            '  exit 1',
            'fi',
            'echo "✅ Work ID: $WORK_ID"',
          ].join('\n'),
        },
      ],
    },

    'small-tests': {
      name: 'Small Tests',
      'runs-on': runsOn,
      needs: 'detect-work-id',
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        ...getSetupSteps(options.language),
        {
          name: 'Unit Tests',
          run: testCmd,
          id: 'unit-tests',
        },
        {
          name: 'Lint & Format',
          run: lintCmd,
        },
        {
          name: 'Property-Based Tests',
          run: getPBTCommand(options.language),
          if: "${{ hashFiles('**/hypothesis/**', '**/rapid/**', '**/fast-check/**') != '' }}",
        },
        {
          name: 'API Contract Validation',
          run: getContractTestCommand(options.language),
          if: "${{ hashFiles('**/contract*/**', '**/openapi*.yaml', '**/openapi*.json') != '' }}",
        },
      ],
    },

    'security-scan': {
      name: 'Security Scan',
      'runs-on': runsOn,
      needs: 'detect-work-id',
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        {
          name: 'Secret Detection',
          uses: 'trufflesecurity/trufflehog@main',
          with: { path: './', base: '${{ github.event.repository.default_branch }}', head: 'HEAD' },
        },
        {
          name: 'Dependency Vulnerabilities',
          uses: 'anchore/scan-action@v3',
          with: { path: '.', 'fail-build': true },
        },
      ],
    },

    'standards-check': {
      name: 'Golden Path Standards',
      'runs-on': runsOn,
      needs: 'detect-work-id',
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        {
          name: 'Install Golden Path CLI',
          run: 'pip install goldenpath-cli',
        },
        {
          name: 'Validate Standards',
          run: 'goldenpath standards --strict',
        },
        {
          name: 'Validate Work ID',
          run: 'goldenpath validate work-id',
        },
      ],
    },
  };

  // Optional sandbox deployment
  if (options.enableSandboxDeploy && options.cdkStack) {
    jobs['deploy-sandbox'] = {
      name: 'Deploy to Sandbox',
      'runs-on': runsOn,
      needs: ['small-tests', 'security-scan', 'standards-check'],
      environment: {
        name: 'sandbox',
      },
      if: "${{ contains(github.event.pull_request.labels.*.name, 'deploy:sandbox') }}",
      steps: [
        {
          name: 'Checkout',
          uses: 'actions/checkout@v4',
        },
        ...getSetupSteps(options.language),
        {
          name: 'Configure AWS Credentials',
          uses: 'aws-actions/configure-aws-credentials@v4',
          with: {
            'role-to-assume': '${{ secrets.AWS_SANDBOX_ROLE_ARN }}',
            'aws-region': awsRegion,
          },
        },
        {
          name: 'CDK Synth',
          run: `npx cdk synth ${options.cdkStack}-sandbox`,
        },
        {
          name: 'CDK Deploy Sandbox',
          run: `npx cdk deploy ${options.cdkStack}-sandbox --require-approval never`,
        },
        {
          name: 'Emit DORA Event',
          run: 'echo \'{"event_type":"deployment","environment":"sandbox","work_id":"${{ needs.detect-work-id.outputs.work_id }}","commit_sha":"${{ github.sha }}"}\' >> dora-events.jsonl',
        },
      ],
    };
  }

  return {
    name: `PR Pipeline — ${options.serviceName}`,
    on: {
      pull_request: {
        types: ['opened', 'synchronize', 'reopened'],
        branches: ['main'],
      },
    },
    permissions: {
      contents: 'read',
      'pull-requests': 'read',
      'id-token': 'write',
    },
    jobs,
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function getSetupSteps(language: string): WorkflowStep[] {
  switch (language) {
    case 'python':
      return [
        {
          name: 'Install uv',
          uses: 'astral-sh/setup-uv@v3',
        },
        {
          name: 'Setup Python',
          uses: 'actions/setup-python@v5',
          with: { 'python-version': '3.12' },
        },
        {
          name: 'Install dependencies',
          run: 'uv pip install -e ".[dev]"',
        },
      ];
    case 'go':
      return [
        {
          name: 'Setup Go',
          uses: 'actions/setup-go@v5',
          with: { 'go-version': '1.22' },
      }];
    case 'typescript':
      return [
        {
          name: 'Setup Node.js',
          uses: 'actions/setup-node@v4',
          with: { 'node-version': '20', cache: 'pnpm' },
        },
        {
          name: 'Install pnpm',
          uses: 'pnpm/action-setup@v3',
          with: { version: '8' },
        },
        {
          name: 'Install dependencies',
          run: 'pnpm install',
        },
      ];
    default:
      return [{ name: 'Setup', run: 'echo "No setup configured for ${language}"' }];
  }
}

function getDefaultTestCommand(language: string): string {
  switch (language) {
    case 'python':
      return 'uv run pytest tests/ -v --cov=src --cov-report=xml';
    case 'go':
      return 'go test ./... -v -race -coverprofile=coverage.out';
    case 'typescript':
      return 'pnpm test -- --run --coverage';
    case 'clojure':
      return 'lein test';
    default:
      return 'echo "No tests configured"';
  }
}

function getDefaultLintCommand(language: string): string {
  switch (language) {
    case 'python':
      return 'uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/';
    case 'go':
      return 'gofmt -d . && golangci-lint run';
    case 'typescript':
      return 'pnpm lint && pnpm typecheck';
    default:
      return 'echo "No lint configured"';
  }
}

function getPBTCommand(language: string): string {
  switch (language) {
    case 'python':
      return 'uv run pytest tests/ -m property_based -v || echo "No PBT tests found"';
    case 'typescript':
      return 'pnpm test -- --grep "property" || echo "No PBT tests found"';
    default:
      return 'echo "No PBT configured"';
  }
}

function getContractTestCommand(_language: string): string {
  return 'echo "Contract tests would run here (e.g., schemathesis, prism)"';
}
