# Technical Debt — Output Template

**Path**: `{OUTPUT_DIR}/debt.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Technical Debt

## Summary

[detected] debt items identified. [count] high severity, [count] medium, [count] low. [Brief characterization of overall codebase health.]

## Risk Heatmap

| Module | Complexity | Test Coverage | Coupling | Debt Items | Overall Risk |
|---|---|---|---|---|---|
| [name] | [low/medium/high] | [good/partial/none] | [low/medium/high] | [count] | [🟢/🟡/🔴] |

## Debt Inventory

| # | Item | Type | Severity | Location | Description |
|---|---|---|---|---|---|
| 1 | [name] | [complexity/dead-code/coverage/dependency/inconsistency/missing-abstraction/security/architecture] | [high/medium/low] | [file:line] | [description] |

## Complexity Hotspots

| File | Function | Cyclomatic Complexity | Lines | Issue |
|---|---|---|---|---|
| [file:line] | [function] | [value or estimate] | [count] | [description] |

## Test Assessment

### Coverage Overview

| Module | Unit Tests | Integration Tests | E2E Tests | Test-to-Code Ratio | Critical Paths Tested |
|---|---|---|---|---|---|
| [name] | [yes/partial/no] | [yes/partial/no] | [yes/no] | [ratio] | [yes/partial/no] |

### Test Quality Signals

| Signal | Status | Details |
|---|---|---|
| Test framework | [modern/outdated/none] | [framework and version] |
| Flaky test patterns | [none/some/many] | [evidence — timeouts, sleep(), random data without seeds] |
| Excessive mocking | [none/some/heavy] | [modules where mocks dominate over real logic testing] |
| Missing test types | [list] | [e.g., no integration tests, no contract tests] |
| Test execution speed | [fast/slow/unknown] | [evidence from CI config or test count] |

### Coverage Gaps (High Risk)

| Area | Type | Impact | Description |
|---|---|---|---|
| [module or feature] | [no-tests/partial/critical-path-untested] | [high/medium/low] | [description] |

## Dependency Issues

| Dependency | Issue | Current | Latest | Risk |
|---|---|---|---|---|
| [package] | [outdated/deprecated/vulnerable/unmaintained] | [version] | [version] | [high/medium/low] |

## Architectural Debt

| Issue | Type | Modules Affected | Description | Remediation |
|---|---|---|---|---|
| [name] | [circular-dependency/god-module/leaky-abstraction/wrong-layer/tight-coupling] | [list] | [description] | [suggested approach] |

## Remediation Priorities

| Priority | Item | Effort | Impact | Rationale |
|---|---|---|---|---|
| 1 | [description] | [hours/days/weeks] | [high/medium/low] | [why this should be fixed first] |
| 2 | [description] | [effort] | [impact] | [rationale] |
| 3 | [description] | [effort] | [impact] | [rationale] |
~~~
