# Spec-Driven Development Guidelines

## Overview

This project follows Spec-Driven Development (SDD) where GitHub Issues / RFCs drive implementation. AI-assisted code review uses these specifications as context.

## Specification Format

Every feature must have a spec document containing:

```markdown
# Spec: [Feature Name]

## Problem Statement
What problem does this solve?

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Proposed Solution
High-level approach.

## API Design
```python
# Example API
```

## DORA Impact
- Deployment Frequency: [no impact / improves / degrades]
- Lead Time: [no impact / improves / degrades]
- Change Failure Rate: [no impact / improves / degrades]
- MTTR: [no impact / improves / degrades]

## Security Considerations
- Threat model
- Mitigation strategies

## Testing Strategy
- Unit tests
- Integration tests
- Property-based tests

## Rollout Plan
- Phase 1: ...
- Phase 2: ...
```

## Review Criteria for AI

When reviewing code against a spec, verify:

1. **Completeness**: Does the implementation cover all success criteria?
2. **API Consistency**: Does the public API match the spec?
3. **DORA Compliance**: Are metrics captured as specified?
4. **Test Coverage**: Are all test strategies implemented?
5. **Security**: Are all mitigations in place?
6. **Documentation**: Is the feature documented in README and SETUP?

## Spec Status Flow

```
Draft → Review → Approved → Implementing → In Review → Merged → Observing
```

Specs in "Observing" phase are evaluated against DORA metrics for 2 weeks post-release.
