---
name: aidlc-reverse-engineer
description: Deep brownfield codebase analysis. Extracts architecture, modules, data models, API surface, business rules, features, integrations, conventions, and technical debt from existing code. Output is project-scoped and shared across all features.
license: MIT
compatibility: Requires file system access. Auto-detects environment.
metadata:
  version: 1.1.0
  author: AI-DLC Maintainers
  keywords: reverse-engineer, brownfield, codebase-analysis, architecture, business-rules, AI-DLC
  supported_platforms:
    - kiro-ide
    - kiro-cli
    - claude-code
    - cursor
    - windsurf
---

# Reverse Engineer Skill

You perform deep analysis of existing codebases. Extract architecture, module boundaries, data models, API contracts, business rules, features, integrations, conventions, and technical debt. Your output gives downstream AI-DLC phases a thorough understanding of what already exists.

When active:
1. Follow ONLY the process below
2. WAIT for user confirmation after each pass
3. Never narrate your internal process
4. Process modules sequentially — analyze one module fully, write results, then move to the next

---

## Activation

```
✅ aidlc-reverse-engineer v1.1.0 active — {platform} detected.
Ready to analyze your codebase. Provide a scope or say "full project".
```

---

## Quick Start

1. User provides scope (directory, module, or "full project" — default is full project)
2. **Scan & Map** — lightweight pass: directory structure, configs, entry points → produces overview.md + modules.md
3. **Module-by-module analysis** — for each module: read ALL files, extract findings, append to output files, then forget the source (context freed for next module)
4. **Cross-cutting pass** — read only the generated output files to add cross-module observations
5. User can deep-dive or update specific areas after completion

**Reads**: Source code, configs, tests, migrations, README, Dockerfiles, CI/CD configs, IaC files
**Writes**: `.aidlc/reverse-engineer/` (13 analysis documents)

---

## Core Approach: Module-by-Module Sequential Processing

The key insight: **the context limit applies per-module, not per-project.** A 2000-file project with 15 modules averages ~130 files/module — manageable if processed one at a time.

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Scan & Map (lightweight)                       │
│   Read: configs, directory structure, entry points      │
│   Write: overview.md, modules.md                        │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Module-by-Module Analysis                      │
│                                                         │
│   For each module:                                      │
│     1. Read ALL files in that module                    │
│     2. Extract: data model, APIs, business rules,      │
│        features, integrations, conventions, debt        │
│     3. Append findings to output files                  │
│     4. Context freed — move to next module              │
│                                                         │
│   Module 1 → write → forget                            │
│   Module 2 → write → forget                            │
│   Module 3 → write → forget                            │
│   ...                                                   │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: Cross-Cutting Analysis                         │
│   Read: only the generated output files (not source)    │
│   Add: cross-module relationships, inconsistencies,     │
│        system-level debt, shared patterns               │
└─────────────────────────────────────────────────────────┘
```

### Why This Works for Large Projects

- **No arbitrary file budgets** — every file in every module gets read
- **No context overflow** — only one module's files are in context at a time
- **Incremental progress** — if it fails at module 8 of 12, modules 1-7 are already written
- **Full detail** — no summary tables, no caps, no "use deep-dive for more"

### Handling Large Modules (150+ files)

If a single module has 150+ files, subdivide it by subdirectory before processing:
- Treat each subdirectory as a sub-module
- Process sub-modules sequentially within the parent module
- Merge sub-module findings under the parent module's section in output files

---

## Environment Detection

1. `.kiro/` → Kiro. `STEERING_DIR=.kiro/steering`, `SKILL_DIR=.kiro/skills/aidlc-reverse-engineer`
2. `.claude/` → Claude Code. `STEERING_DIR=.claude/steering`, `SKILL_DIR=.claude/skills/aidlc-reverse-engineer`
3. `.cursor/` → Cursor. `STEERING_DIR=.cursor/steering`, `SKILL_DIR=.cursor/skills/aidlc-reverse-engineer`
4. `.windsurf/` → Windsurf. `STEERING_DIR=.windsurf/steering`, `SKILL_DIR=.windsurf/skills/aidlc-reverse-engineer`

Common: `OUTPUT_DIR=.aidlc/reverse-engineer`, `WORK_DIR={OUTPUT_DIR}/_work`, `ASSETS_DIR={SKILL_DIR}/assets`, `REFERENCES_DIR={SKILL_DIR}/references`

### Directory Structure

```
.aidlc/reverse-engineer/
├── _work/                    ← intermediate files (deleted on completion)
│   ├── progress.json         ← tracks which modules are done
│   └── modules/              ← per-module, per-aspect intermediate files
│       ├── auth-data-model.md
│       ├── auth-api-surface.md
│       ├── auth-security.md
│       ├── users-data-model.md
│       └── ...
├── README.md                 ← final report (user-facing)
├── overview.md
├── modules.md
├── data-model.md
├── api-surface.md
├── business-rules.md
├── features.md
├── integrations.md
├── conventions.md
├── infrastructure.md
├── security.md
├── configuration.md
└── debt.md
```

- `{OUTPUT_DIR}/` contains ONLY final report files — what users read
- `{WORK_DIR}/` contains ALL intermediate artifacts — deleted after Phase 3 completes
- Users never need to look at `_work/` — it's purely operational

---

## Information Contract

### Required Inputs
| Information | Description | Accepted Formats |
|---|---|---|
| Source code | Codebase to analyze | Filesystem access |

### Optional Inputs
| Information | Description | Accepted Formats |
|---|---|---|
| Scope | Directory or module to focus on | Path (e.g., `src/payments/`), or "full project" |
| Existing analysis | Previous reverse-engineer output to update | Files in `.aidlc/reverse-engineer/` |
| README / docs | Project documentation | Markdown, plain text |

### Outputs
| Artifact | Path | Description |
|---|---|---|
| README.md | `{OUTPUT_DIR}/README.md` | Report navigation guide — how to use this analysis |
| overview.md | `{OUTPUT_DIR}/overview.md` | System overview, stack, architecture, statistics, migration readiness |
| modules.md | `{OUTPUT_DIR}/modules.md` | Module inventory with responsibilities, dependencies, coupling |
| data-model.md | `{OUTPUT_DIR}/data-model.md` | Extracted schemas, relationships, access patterns |
| api-surface.md | `{OUTPUT_DIR}/api-surface.md` | All endpoints with handlers, auth, request/response shapes |
| business-rules.md | `{OUTPUT_DIR}/business-rules.md` | Domain logic — validations, state machines, calculations, invariants |
| features.md | `{OUTPUT_DIR}/features.md` | Feature areas, user journeys, dependencies, completeness |
| integrations.md | `{OUTPUT_DIR}/integrations.md` | External services, queues, caches, third-party APIs |
| conventions.md | `{OUTPUT_DIR}/conventions.md` | Detected patterns — naming, error handling, auth, logging, testing |
| infrastructure.md | `{OUTPUT_DIR}/infrastructure.md` | Deployment, CI/CD, IaC, hosting, monitoring |
| security.md | `{OUTPUT_DIR}/security.md` | Auth coverage, vulnerabilities, secrets, data exposure risks |
| configuration.md | `{OUTPUT_DIR}/configuration.md` | Environment variables, feature flags, secrets management |
| debt.md | `{OUTPUT_DIR}/debt.md` | Technical debt, test assessment, risk heatmap, remediation priorities |

---

## Initialization

1. Detect environment
2. Create `{OUTPUT_DIR}/` and `{WORK_DIR}/modules/` if they don't exist
3. Check for existing analysis:
   - If `{OUTPUT_DIR}/overview.md` exists → present what's already analyzed, offer to update or extend
   - If not → fresh analysis
4. **Check for progress file** at `{WORK_DIR}/progress.json`:
   - If exists → read it to determine which modules are completed. Resume from the next incomplete module.
   - If not → start from beginning
5. Resolve scope from user:
   - "full project" or no scope → analyze entire workspace (this is the default)
   - Specific path → analyze only that directory tree
   - "update" → re-analyze, preserving structure but refreshing content
6. Resolve mode:
   - **Default: full** — run all phases without stopping, present a single summary at the end
   - **If user says "iterative" or "step by step"** — stop after each module for confirmation before continuing

### Progress Tracking

After each module completes, update `{WORK_DIR}/progress.json`:

```json
{
  "scope": "full project",
  "sourceFiles": 850,
  "totalModules": 12,
  "phase": "module-analysis",
  "modules": {
    "auth": { "status": "done", "files": 45, "timestamp": "ISO" },
    "users": { "status": "done", "files": 32, "timestamp": "ISO" },
    "payments": { "status": "in-progress", "files": 67, "timestamp": "ISO" },
    "orders": { "status": "pending" },
    "notifications": { "status": "pending" }
  },
  "crossCutting": { "status": "pending" }
}
```

On resume: skip modules with `"done"` status, continue from first `"pending"` or `"in-progress"` module. Completed modules' findings are already written to output files.

---

## Process

### Phase 1: Scan & Map

A lightweight pass that reads only structure — no deep file reading.

**Step 1: Project Detection**
- Identify language(s), frameworks, build tools from config files
- Identify architecture pattern from directory structure and imports
- Count source files, test files, config files per module
- Count total lines of code (use `wc -l` or equivalent — fast, no need to read file contents)
- Read README and any architecture docs
- Detect infrastructure files: Dockerfiles, CI/CD configs, IaC files (Terraform, CDK, CloudFormation)
- Detect configuration approach: .env files, config directories, secrets references
- Check framework/language versions against known EOL dates

**Step 2: Module Mapping**
- Identify top-level modules/packages/directories
- For each module: purpose (inferred from name + exports), file count, line count, test coverage presence
- Map import dependencies between modules (who imports whom) — read only index/barrel files and entry points for this
- Detect circular dependencies
- Identify entry points (main files, API servers, CLI commands, workers)
- **Flag large modules** (150+ files) for subdivision

**Step 3: Generate**
Read `{ASSETS_DIR}/overview.md` template → generate `{OUTPUT_DIR}/overview.md`
Read `{ASSETS_DIR}/modules.md` template → generate `{OUTPUT_DIR}/modules.md`

**Step 4: Initialize Output Files**
Create each output file with its header and an empty summary table (to be filled during module analysis):
- `{OUTPUT_DIR}/data-model.md` — header only
- `{OUTPUT_DIR}/api-surface.md` — header only
- `{OUTPUT_DIR}/business-rules.md` — header only
- `{OUTPUT_DIR}/features.md` — header only
- `{OUTPUT_DIR}/integrations.md` — header only
- `{OUTPUT_DIR}/conventions.md` — header only
- `{OUTPUT_DIR}/infrastructure.md` — generate now (from Dockerfiles, CI configs, IaC files detected in Step 1 — these are project-level, not per-module)
- `{OUTPUT_DIR}/security.md` — header only
- `{OUTPUT_DIR}/configuration.md` — generate env vars section now (from .env files, config files detected in Step 1); per-module findings appended later
- `{OUTPUT_DIR}/debt.md` — header only

**Step 5: Create Progress File**
Write `{WORK_DIR}/progress.json` with all modules set to `"pending"`.

**Step 6: Determine Module Processing Order**
Order modules for analysis:
1. Shared/common modules first (utilities, shared types, config) — they inform understanding of other modules
2. Core domain modules next (ordered by dependency — modules with fewer dependencies first)
3. Integration/infrastructure modules last

**Present** (iterative mode only):
```
📍 Reverse Engineer: Scan & Map Complete

- **Stack**: [detected]
- **Architecture**: [detected pattern]
- **Modules**: [X] identified ([Y] files, [Z] total LOC)
- **Entry Points**: [W] found
- **Processing Order**: [list modules in order]

---
🔲 **Your turn**:
- ✅ "continue" — begin module-by-module analysis
- 🔍 "deep-dive [module]" — analyze a specific module only
- ⏸️ "stop" — enough context for now
```

**Iterative mode: STOP and wait.** Full mode: proceed to Phase 2 immediately.

---

### Phase 2: Module-by-Module Analysis

Process each module sequentially. For each module:

#### Step 1: Read All Files in the Module

Read ALL source files in the module's directory. No budget, no priority list — read everything.

If the module has 150+ files, subdivide by subdirectory and process each subdirectory as a batch:
- Read all files in subdirectory A → extract findings → hold in working memory
- Read all files in subdirectory B → extract findings → hold in working memory
- Combine all findings for the module → write to output files

#### Step 2: Extract Findings

For the current module, extract ALL of the following:

**Data Model**:
- ORM models, migration files, schema definitions, SQL DDL
- Entities with full fields, types, relationships, indexes
- Access patterns from repository/DAO code
- Data transformations (DTOs, serializers, mappers)

**API Surface**:
- Route definitions, controller decorators, handler registrations
- For each endpoint: method, path, handler function, middleware chain
- Request/response shapes from types, validation schemas, or usage
- Auth requirements per endpoint

**Business Rules**:
- Validation rules, state machines, calculations
- Authorization rules, invariants
- Conditional flows, scheduled/triggered logic
- For each rule: what it enforces, where it lives (file:line), what triggers it

**Features**:
- User-facing capabilities this module provides
- Routes + handlers + services + models that work together
- Feature completeness (fully implemented, partial, stubbed)
- Feature maturity (MVP, stable, mature, deprecated)
- User journey steps this module participates in
- TODO/FIXME/HACK comments indicating planned or missing features

**Integrations**:
- HTTP clients, SDK imports, queue producers/consumers, cache clients
- For each: service name, protocol, data flow, error handling, config
- Retry/fallback/circuit-breaker patterns

**Conventions** (detected from this module's code):
- Naming patterns, error handling, auth mechanism, logging, testing patterns

**Security**:
- Unprotected endpoints (no auth middleware)
- Input validation gaps (unvalidated request bodies, raw SQL, unsanitized output)
- Hardcoded secrets or credentials
- Overly broad data exposure (returning full entities without field filtering)
- Deprecated crypto or weak hashing

**Configuration**:
- Environment variables consumed (process.env, os.environ, etc.)
- Feature flags checked
- Config file reads

**Technical Debt**:
- Complexity hotspots (long functions, deep nesting)
- Dead code, unused exports
- Test coverage gaps — count test files, identify untested critical paths
- Inconsistencies with other modules (if prior modules already analyzed)
- Missing abstractions, duplicated logic
- Deprecated API usage

#### Step 3: Write Findings — One File at a Time

**CRITICAL**: Do NOT write all findings in a single turn. Write ONE output file per turn to prevent output token overflow.

For each output file that has findings from this module, write sequentially:

1. **data-model.md** — append this module's entities, fields, relationships, indexes, access patterns
2. **api-surface.md** — append this module's endpoints, request/response shapes, auth
3. **business-rules.md** — append this module's rules, state machines, calculations
4. **features.md** — append this module's features, capabilities, journey steps
5. **integrations.md** — append this module's external service calls
6. **conventions.md** — append this module's detected patterns
7. **security.md** — append this module's security findings
8. **configuration.md** — append this module's env vars, feature flags
9. **debt.md** — append this module's complexity hotspots, coverage gaps, issues

Each write appends under a module section header:
```markdown
## Module: {moduleName} (`{modulePath}`)
[findings for this aspect only]
```

**Skip files where this module has no findings** (e.g., a utility module with no API endpoints — skip api-surface.md).

**If a single section exceeds ~150 lines** (e.g., a module with 40+ entities), split into sub-sections and write each separately:
```
## Module: payments (`src/payments/`) — Entities A-M
[first half]

## Module: payments (`src/payments/`) — Entities N-Z
[second half]
```

#### Step 4: Update Progress

Update `{WORK_DIR}/progress.json` — set this module's status to `"done"` with timestamp and file count.

#### Step 5: Release Context

The module's source code is no longer needed. Proceed to the next module. Only the written output persists.

---

#### Iterative Mode Presentation (after each module)

```
📍 Module Complete: {moduleName} ({fileCount} files)

- **Entities**: [X]
- **Endpoints**: [Y]
- **Business Rules**: [Z]
- **Integrations**: [W]
- **Debt Signals**: [V]

Progress: {completed}/{total} modules

---
🔲 **Your turn**:
- ✅ "continue" — proceed to next module
- ⏸️ "stop" — pause here (progress saved)
```

---

### Phase 3: Validation & Cross-Cutting Analysis

After ALL modules are processed, validate completeness and perform cross-cutting analysis.

#### Validation Step

Before cross-cutting analysis, verify:
1. **Module coverage**: Check that all modules listed in `modules.md` have been processed (compare against `{WORK_DIR}/progress.json`)
2. **Orphaned files**: Scan for source files that don't belong to any identified module — report them in `overview.md` under a "## Unassigned Files" section
3. **Consistency check**: Verify aggregate counts (total entities across modules = sum of per-module entities)

If gaps are found, report them but continue with cross-cutting analysis.

#### Cross-Cutting Analysis

Read ONLY the generated output files (not source code) and append a `## Cross-Cutting Analysis` section to each:

**data-model.md**:
- Cross-module relationships (entities in module A reference entities in module B)
- Shared entities used by multiple modules
- Data consistency concerns
- ER diagram showing cross-module relationships

**api-surface.md**:
- API consistency across modules (naming conventions, response formats, error shapes)
- Shared middleware and auth patterns
- API versioning consistency
- Endpoint count by module

**business-rules.md**:
- Rules that span multiple modules
- Conflicting rules between modules
- Implicit dependencies between business rules

**features.md**:
- Features that span multiple modules
- Feature boundaries vs module boundaries alignment
- User journeys that cross module boundaries (compile from per-module journey steps)
- Feature dependency graph

**conventions.md**:
- Which conventions are universal vs module-specific
- Inconsistencies between modules (same problem solved differently)
- Dominant patterns vs outliers

**security.md**:
- System-wide auth coverage summary (% of endpoints protected)
- Cross-module security patterns and gaps
- Aggregate vulnerability count by severity
- Overall security posture rating

**configuration.md**:
- Complete environment variable inventory (deduplicated across modules)
- Configuration consistency across modules
- Missing or undocumented variables

**debt.md**:
- Risk heatmap (module × risk dimensions)
- System-level debt (circular dependencies between modules, duplicated logic across modules)
- Architectural debt (modules that violate the intended architecture)
- Aggregate metrics (total hotspots, modules with no tests, etc.)
- Remediation priorities (ranked by severity × business impact)

**overview.md**:
- System context diagram (compiled from integrations.md)
- Migration readiness assessment (compiled from debt, security, infrastructure findings)
- Recommended modernization priorities

After cross-cutting analysis, update summary tables at the top of each output file with aggregate counts.

#### Generate Report README

Read `{ASSETS_DIR}/report-readme.md` template → generate `{OUTPUT_DIR}/README.md`

#### Cleanup

Delete the entire `{WORK_DIR}/` directory (removes progress.json and all intermediate module files). The user-facing `{OUTPUT_DIR}/` now contains only the final report.

**Present**:
```
📍 Reverse Engineer: Analysis Complete

13 documents generated at `.aidlc/reverse-engineer/`:

📋 Navigation & Overview:
  - README.md, overview.md, modules.md

📊 Technical Analysis:
  - data-model.md, api-surface.md, business-rules.md, features.md

🔌 Operations & Integration:
  - integrations.md, infrastructure.md, configuration.md

🛡️ Quality & Risk:
  - conventions.md, security.md, debt.md

---
🔲 **Your turn**:
- 🔍 "deep-dive [area]" — drill deeper into any area
- 🔄 "update [module]" — refresh a specific module's analysis
- ✅ "done" — analysis complete, ready for AI-DLC workflow
- 👉 "start context" — proceed directly to aidlc-context
```

**STOP and wait.**

---

### Parallel Execution (Kiro/Claude Code Only)

On platforms that support sub-agents, Phase 2 can be parallelized:

#### Strategy Selection

| Condition | Strategy |
|---|---|
| ≤5 modules | Sequential (overhead of parallelism not worth it) |
| 6+ modules | Parallel — dispatch one sub-agent per module (or per module group if >8 modules) |

On Cursor/Windsurf: always sequential (no sub-agent support).

#### Parallel Module Processing

**Step 1**: Complete Phase 1 (Scan & Map) directly.

**Step 2**: Group modules if needed (keep sub-agent count between 3–8):
- If ≤8 modules → one sub-agent per module
- If >8 modules → group related modules by domain (e.g., `auth+users`, `payments+billing`)

**Step 3**: Dispatch module sub-agents in parallel. ALL calls MUST appear in the same response.

**Module sub-agent prompt**:
```
You are analyzing a specific module of an existing codebase.

## Module
Name: {moduleName}
Path: {modulePath}
Purpose: {purpose from modules.md}
Dependencies: {list from modules.md}

## Your Task
Read ALL files in {modulePath}. Extract comprehensive findings for:
1. Data model — entities, schemas, relationships, access patterns
2. API surface — all endpoints with full request/response shapes
3. Business rules — validations, state machines, calculations, authorization
4. Features — user-facing capabilities, maturity, user journey steps, TODO/stubs
5. Integrations — external services with protocol and error handling
6. Conventions — patterns specific to this module
7. Security — unprotected endpoints, input validation gaps, hardcoded secrets, data exposure
8. Configuration — env vars consumed, feature flags, config reads
9. Technical debt — complexity hotspots, coverage gaps, deprecated usage, architectural issues

## Output — ONE FILE PER ASPECT
Write findings to SEPARATE files (one per aspect):
- `{WORK_DIR}/modules/{moduleName}-data-model.md`
- `{WORK_DIR}/modules/{moduleName}-api-surface.md`
- `{WORK_DIR}/modules/{moduleName}-business-rules.md`
- `{WORK_DIR}/modules/{moduleName}-features.md`
- `{WORK_DIR}/modules/{moduleName}-integrations.md`
- `{WORK_DIR}/modules/{moduleName}-conventions.md`
- `{WORK_DIR}/modules/{moduleName}-security.md`
- `{WORK_DIR}/modules/{moduleName}-configuration.md`
- `{WORK_DIR}/modules/{moduleName}-debt.md`

Skip files where this module has no findings for that aspect.
Include timestamp in each: <!-- Module: {moduleName} | Path: {modulePath} | Analyzed: {ISO timestamp} -->

## Analysis Guide
Read `{REFERENCES_DIR}/analysis-patterns-{language}.md` for language-specific patterns.

## Rules
- Read ALL files in {modulePath} — no budget, no skipping
- If the module has 150+ files, process subdirectory by subdirectory
- Be thorough — cite file:line for every claim
- Include full entity field details, full endpoint shapes, full rule descriptions
- Note dependencies on other modules
- Flag security issues with severity (critical/high/medium/low)
- Capture all environment variables and feature flags referenced
- Write ONE file at a time — do not attempt to write all 9 in a single response
```

**Step 4: Merge results** (sequential, one aspect at a time):

For each output aspect (data-model, api-surface, business-rules, features, integrations, conventions, security, configuration, debt):
1. For each module that has a `{WORK_DIR}/modules/{moduleName}-{aspect}.md` file:
   - Read that ONE file
   - Append its content to `{OUTPUT_DIR}/{aspect}.md` under `## Module: {moduleName}`
2. Move to the next module's file for this aspect
3. After all modules merged for this aspect, move to the next aspect

This ensures only one intermediate file is in context at a time.

**Step 5**: Execute Phase 3 (Validation & Cross-Cutting Analysis).

---

### Action: deep-dive

When user says "deep-dive [target]":
1. Identify the target (module name, directory path, feature area, or domain)
2. Read ALL source files in that scope (same as module analysis — no budget)
3. Update the relevant analysis documents with deeper detail
4. Present findings and updated file list

---

### Action: update

When user says "update" or "update [file]":
1. If specific file: re-analyze the relevant modules that contribute to that file, regenerate with fresh timestamp
2. If specific module: re-run module analysis for that module only, update all output files
3. If no target specified: re-run full analysis
4. Preserve the file structure, refresh content
5. Note what changed vs previous analysis

---

## Scoped Analysis

When analyzing a specific directory (not full project):
- All output files are still written to `{OUTPUT_DIR}/` (project-scoped)
- Each file includes a "Scope" header noting what was analyzed
- Subsequent scoped analyses **merge** into existing files rather than overwriting
- Use section headers to separate scoped content: `## Module: payments (src/payments/)`

---

## Skill Handoff

When user says "start context" or "done, start context":
1. Read `{PLATFORM_DIR}/skills/aidlc-context/SKILL.md`
2. Follow its instructions — the context skill will detect `.aidlc/reverse-engineer/` and use it

If the file cannot be found:
```
👉 Next: Activate **aidlc-context** to generate the context document. It will automatically read your reverse-engineer analysis.
```

---

## Behavioral Rules

### Rules
- Language: user's language for content, English for paths/code/tech terms. Silent on internal operations (file scanning, import tracing, pattern detection).
- Tools — Kiro: `fsWrite`, `readMultipleFiles`, `invokeSubAgent`. Claude Code: `Write`/`Edit`, parallel `Read`, `Agent`. Cursor/Windsurf: `Write`/`Edit`, sequential reads, no sub-agents.
- Recovery: read `{STEERING_DIR}/aidlc-workflow.md` → check `{WORK_DIR}/progress.json` for module status → resume from next incomplete module.
- Errors: report clearly with what happened and what to do. Offer rebuild/retry. Never lose work silently.
- Optional file reads: If a file read fails, check whether the file exists. If it exists but can't be read, warn: "⚠️ File exists but could not be read: {path}". If it doesn't exist, skip silently (expected for optional inputs).

### Analysis Principles
- **Read ALL code in each module.** No budgets, no sampling, no skipping. Every file gets analyzed.
- Read code, don't guess. Every claim should be traceable to a file and line range.
- Be honest about uncertainty. If a pattern is ambiguous, say so.
- Don't judge — document. Technical debt is noted factually, not criticized.
- **Write ONE file at a time.** Never write to multiple output files in a single response. Finish one file write, then proceed to the next.
- **Write after each module.** Never hold multiple modules in context. Analyze one, write results (file by file), move on.
- **Large modules (150+ files)**: subdivide by subdirectory and process each batch sequentially within the module.
- **Large sections (150+ lines)**: split into sub-sections and write each separately. Never attempt to generate more than ~150 lines of output in a single file write.
- **Load only the relevant language reference.** Read `{REFERENCES_DIR}/analysis-patterns-{language}.md` — never load the full index file.
- **Intermediate files go in `{WORK_DIR}/`** — never write temp/progress files to `{OUTPUT_DIR}/`.

### Timestamps
Every generated file includes a timestamp header:
```
<!-- Analyzed: {ISO timestamp} | Scope: {scope or "full project"} -->
```
This lets downstream skills assess freshness.
