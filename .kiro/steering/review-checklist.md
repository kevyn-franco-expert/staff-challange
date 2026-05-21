# AI-Assisted Review Checklist

## Pre-Review Context

- Read the associated spec/RFC
- Understand the DORA impact
- Check for breaking changes
- Verify polyglot compatibility

## Code Review Checklist

### Architecture
- [ ] Does it follow Convention over Configuration?
- [ ] Is it extensible without core modification?
- [ ] Does it maintain separation between CLI and Framework?

### Python (CLI)
- [ ] Type annotations present on all public functions?
- [ ] Docstrings follow Google convention?
- [ ] No bare except clauses?
- [ ] pathlib used instead of os.path?
- [ ] Configuration uses dataclasses with frozen=True where appropriate?

### TypeScript (Framework)
- [ ] Explicit return types on public APIs?
- [ ] readonly used for immutable properties?
- [ ] No any types without justification?
- [ ] CDK constructs properly tagged?
- [ ] Workflow definitions validate successfully?

### Testing
- [ ] At least one test per public function?
- [ ] Mock external dependencies?
- [ ] Test names describe behavior, not implementation?
- [ ] Edge cases covered?

### DORA & Observability
- [ ] Are events emitted for deployments/changes/failures/recoveries?
- [ ] Audit context includes actor/action/reason?
- [ ] Metrics are comparable across languages?

### Security
- [ ] No hardcoded secrets?
- [ ] IAM policies follow least privilege?
- [ ] Input validation present?
- [ ] No SQL injection / command injection risks?

### Documentation
- [ ] README updated?
- [ ] SETUP.md updated if installation steps change?
- [ ] ADR updated if architectural decision?
- [ ] Inner-source guidelines followed?

## Review Comment Format

```
**[Category]**: [Severity] — [Message]

**Context**: [Why this matters]
**Suggestion**: [How to fix]
**Reference**: [Link to spec/guideline]
```

Categories: Architecture, Type Safety, Testing, DORA, Security, Documentation
Severity: Blocking, Warning, Nit, Praise
