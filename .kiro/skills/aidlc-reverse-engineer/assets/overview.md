# System Overview — Output Template

**Path**: `{OUTPUT_DIR}/overview.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# System Overview

## Summary

[10-line digest of the system: what it does, who it serves, how it's built, key architectural decisions, current state, and notable characteristics. Written as a concise narrative paragraph.]

## Stack

| Layer | Technology | Version | EOL Status |
|---|---|---|---|
| Language | [detected] | [version] | [active/maintenance/EOL/near-EOL] |
| Framework | [detected] | [version] | [active/maintenance/EOL/near-EOL] |
| Runtime | [detected] | [version] | [active/LTS/EOL] |
| Database | [detected] | [version or N/A] | [active/EOL/unknown] |
| Cache | [detected or N/A] | [version] | [status] |
| Infrastructure | [detected or N/A] | — | — |
| Build Tool | [detected] | [version] | [status] |
| Package Manager | [detected] | [version] | [status] |

## Architecture Pattern

**Pattern**: [detected — e.g., Layered Monolith, Modular Monolith, Microservices, Serverless]

```
[ASCII diagram showing high-level architecture]

  ┌──────────┐     ┌──────────┐
  │  Client   │────▶│  API     │
  └──────────┘     └────┬─────┘
                        │
                   ┌────▼─────┐
                   │  Service  │
                   └────┬─────┘
                        │
                   ┌────▼─────┐
                   │    DB     │
                   └──────────┘
```

## System Context

```
[ASCII system context diagram — what's external to this system]

  ┌──────────┐          ┌──────────────┐          ┌──────────┐
  │  Users   │─────────▶│  THIS SYSTEM │─────────▶│ Payment  │
  └──────────┘          │              │          │ Gateway  │
                        │              │◀─────────│          │
  ┌──────────┐          │              │          └──────────┘
  │  Admin   │─────────▶│              │
  └──────────┘          │              │─────────▶┌──────────┐
                        │              │          │  Email   │
                        └──────────────┘          │ Service  │
                                                  └──────────┘
```

### External Dependencies

| External System | Direction | Protocol | Purpose |
|---|---|---|---|
| [name] | [inbound/outbound/bidirectional] | [REST/gRPC/webhook/queue] | [description] |

### External Consumers

| Consumer | Protocol | What They Access |
|---|---|---|
| [name or type] | [REST/GraphQL/webhook] | [which endpoints or data] |

## Entry Points

| Entry Point | Type | File | Description |
|---|---|---|---|
| [detected] | [http/cli/worker/cron] | [file:line] | [description] |

## Project Statistics

| Metric | Value |
|---|---|
| Total Lines of Code | [count — sum of all source files, excluding blank lines and comments] |
| Source Files | [count] |
| Test Files | [count] |
| Lines of Test Code | [count] |
| Test-to-Code Ratio | [ratio — e.g., 1:3] |
| Dependencies | [count] |
| Dev Dependencies | [count] |
| Config Files | [count] |
| Modules | [count] |
| API Endpoints | [count] |
| Database Entities | [count] |
| External Integrations | [count] |

## Migration Readiness Assessment

### Version & EOL Risk

| Component | Current | Latest Stable | Gap | Risk |
|---|---|---|---|---|
| [language/framework/runtime] | [version] | [latest] | [major versions behind] | [none/low/medium/high/critical] |

### Modernization Signals

| Signal | Status | Details |
|---|---|---|
| Framework version | [current/outdated/EOL] | [specifics] |
| Deprecated API usage | [none/some/heavy] | [list key deprecated patterns] |
| Vendor lock-in | [low/medium/high] | [what's tightly coupled to specific vendor] |
| Stateful components | [none/some/many] | [what holds state — sessions, local files, in-memory] |
| Monolith decomposition readiness | [ready/partial/not-ready] | [which modules have clear boundaries] |
| Data migration complexity | [low/medium/high] | [schema size, relationships, estimated volume] |
| Test coverage for safe refactoring | [adequate/partial/insufficient] | [which areas are safe to change] |

### Recommended Modernization Priorities

| Priority | Area | Rationale | Effort | Impact |
|---|---|---|---|---|
| 1 | [area] | [why this should be addressed first] | [low/medium/high] | [low/medium/high] |
| 2 | [area] | [rationale] | [effort] | [impact] |
| 3 | [area] | [rationale] | [effort] | [impact] |
~~~
