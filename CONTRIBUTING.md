# Contributing to Golden Path Platform

> **Inner-Source Contribution Guidelines**

Thank you for investing in the shared platform! This document ensures contributions are consistent, reviewable, and safe.

## Contribution Model

We follow an **Inner-Source** model with **Trusted Committers**:

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTRIBUTION FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────┐     │
│   │  Team    │───►│  Fork /  │───►│  Pull Request    │     │
│   │  Member  │    │  Branch  │    │  (with Work ID)  │     │
│   └──────────┘    └──────────┘    └────────┬─────────┘     │
│                                            │               │
│                              ┌─────────────▼──────────┐    │
│                              │   Trusted Committer    │    │
│                              │   Review (Platform)    │    │
│                              │   - Architecture       │    │
│                              │   - Security           │    │
│                              │   - DORA Impact        │    │
│                              └─────────────┬──────────┘    │
│                                            │               │
│                              ┌─────────────▼──────────┐    │
│                              │   Merge & Release      │    │
│                              └────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

1. **Clone** the monorepo
2. **Install** dependencies: `make install`
3. **Create** a feature branch: `git checkout -b feature/FIN-xxx-description`
4. **Ensure** all commits include Work ID: `[FIN-xxx] type: description`
5. **Run** tests before push: `make test`
6. **Open** a PR with the template

## Adding New Language Support

To add a new runtime language (e.g., Java, Rust):

### 1. CLI Changes (`packages/goldenpath-cli/`)

Update `standards.py` to recognize the new language:

```python
elif self.config.language == "rust":
    checks.extend([
        ("Cargo.toml", self.repo_path / "Cargo.toml", True),
        ("src/main.rs", self.repo_path / "src" / "main.rs", False),
    ])
```

Update `local_env.py` to generate language-specific test configs.

### 2. Framework Changes (`packages/goldenpath-framework/`)

Update `src/types/index.ts`:

```typescript
export type RuntimeLanguage = 'python' | 'go' | 'typescript' | 'clojure' | 'java' | 'rust';
export type LambdaRuntime = 'python3.12' | ... | 'provided.al2023' | 'java21';
```

Update workflow generators to include build/test steps for the new language.

### 3. Update Tests

Add test cases in both `packages/goldenpath-cli/tests/` and `packages/goldenpath-framework/tests/`.

### 4. Documentation

Update:
- `README.md` — Supported languages table
- `docs/SETUP.md` — Language-specific setup instructions
- `examples/` — Add a minimal example project

## Commit Convention

```
[FIN-123] feat(cli): add Rust language support

- Recognize Cargo.toml in standards check
- Add rust test commands to PR pipeline
- Update local env bootstrap for Rust

Refs: FIN-123
```

## Review Criteria

All PRs are evaluated against:

- [ ] **Architecture**: Does it align with the Golden Path philosophy?
- [ ] **Polyglot**: Does it work consistently across all supported languages?
- [ ] **DORA**: Does it capture or improve metric accuracy?
- [ ] **Security**: Does it follow least-privilege and secrets management?
- [ ] **Tests**: Are there unit tests with clear assertions?
- [ ] **Docs**: Is the change documented for other teams?

## Inner-Source Governance

The Platform Engineering team acts as **stewards**; no single team owns the platform.

### Roles

| Role | Who | Responsibility |
|------|-----|----------------|
| **Contributor** | Any engineer | Open PRs, participate in discussions |
| **Trusted Committer** | Platform + rotating team reps | Review, merge, mentor |
| **Steward** | Platform Engineering Lead | Architecture decisions, releases |

### Decision Making

| Change Type | Process | Timeline |
|-------------|---------|----------|
| **Lightweight** (bug, docs, tests) | 1 Trusted Committer approval | 24–48 h |
| **Standard** (new feature) | 2 Trusted Committer approvals | 1 week |
| **Heavyweight** (breaking change) | Steering Committee consensus | 2 weeks + 1 week notice |

### Avoiding the Bottleneck

Teams extend the framework via composition — they never modify core:

```typescript
class PaymentStack extends ServiceStack {
  constructor(scope, id, props) {
    super(scope, id, props);
    this.addPaymentProcessor();
  }
}
```

## Release Process

1. Version bump follows [SemVer](https://semver.org/)
2. Both packages release independently
3. Git tags mark releases: `cli-v1.2.3`, `framework-v1.2.3`

## Code of Conduct

- Be respectful and constructive
- Assume positive intent
- Focus on the problem, not the person
- Document your decisions

## Questions?

- Slack: `#platform-engineering`
- Email: platform@gila.software
- Office Hours: Tuesdays 10:00 AM CST
