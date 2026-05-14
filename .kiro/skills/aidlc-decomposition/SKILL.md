---
name: aidlc-decomposition
description: Decompose requirements into units of work with DDD concepts. Define system boundaries, dependencies, and development sequence. Presents incremental vs comprehensive mode choice.
license: MIT
compatibility: Requires file system access. Auto-detects environment.
metadata:
  version: 1.0.0
  author: AI-DLC Maintainers
  keywords: specification, decomposition, units, DDD, bounded-context, AI-DLC
  supported_platforms:
    - kiro-ide
    - kiro-cli
    - claude-code
    - cursor
    - windsurf
---

# Decomposition Skill

You break requirements into manageable, independently deliverable units of work. You define system boundaries, dependencies, and development sequence using DDD concepts.

When active:
1. Follow ONLY the process below
2. WAIT for user approval after each step
3. Never narrate your internal process
4. Do NOT make technology stack decisions — that's the design phase's job
5. Decomposition should be proportional to project complexity
6. Integration contracts are sketches, not full API specs
7. For upstream artifacts (context.md, requirements.md), read ONLY the `## Summary` section first

---

## Activation

```
✅ aidlc-decomposition v1.0.0 active — {platform} detected.
Ready to decompose requirements into units of work.
```

---

## Quick Start

1. Generate D2 decision gate → user fills answers (or "use recommendations")
2. Validate D2 for conflicts → resolve if any
3. Generate units with boundaries, dependencies, and story assignments
4. Present results → wait for approval
5. On approval → choose delivery mode (incremental / incremental skip foundation / comprehensive)

**Reads**: context.md (Summary), requirements.md, personas.md
**Writes**: decisions-units.md, units.md

---

## Environment Detection

1. `.kiro/` → Kiro. `STEERING_DIR=.kiro/steering`, `SKILL_DIR=.kiro/skills/aidlc-decomposition`
2. `.claude/` → Claude Code. `STEERING_DIR=.claude/steering`, `SKILL_DIR=.claude/skills/aidlc-decomposition`
3. `.cursor/` → Cursor. `STEERING_DIR=.cursor/steering`, `SKILL_DIR=.cursor/skills/aidlc-decomposition`
4. `.windsurf/` → Windsurf. `STEERING_DIR=.windsurf/steering`, `SKILL_DIR=.windsurf/skills/aidlc-decomposition`

Common: `SPECS_DIR=.aidlc/specs`, `WORKFLOW_DIR=.aidlc/workflow`, `ASSETS_DIR={SKILL_DIR}/assets`

---

## Information Contract

### Required Inputs
| Information | Description | Accepted Formats |
|---|---|---|
| Project context | What exists, stack, scope, feature description | Markdown (context.md), YAML, JSON, plain text, inline |
| User stories with priorities | Requirements from previous phase | Markdown (requirements.md), YAML, JSON, CSV, plain text |

### Optional Inputs
| Information | Description | Accepted Formats |
|---|---|---|
| Personas | User types and characteristics | Markdown (personas.md), YAML, JSON |
| Existing decomposition | Pre-existing units or architecture breakdown | Markdown, YAML, JSON, plain text |
| Reverse-engineer analysis | Existing module boundaries | `.aidlc/reverse-engineer/modules.md` |

If user provides existing decomposition, validate and enrich rather than generate from scratch.

If `.aidlc/reverse-engineer/modules.md` exists, read its Summary section to inform unit proposals using existing module boundaries.

### Outputs
| Artifact | Default Path |
|---|---|
| decisions-units.md | `{WORKFLOW_DIR}/{feature}/decisions-units.md` |
| units.md | `{SPECS_DIR}/{feature}/units.md` |

---

## Initialization

1. Detect environment
2. Resolve feature name:
   - Scan `{WORKFLOW_DIR}/*/aidlc-manifest.yaml` for existing manifests
   - If exactly one manifest → use its `feature` field
   - If multiple manifests → present list, ask user which feature to work on
   - If no manifests → infer from `{SPECS_DIR}/` folders (if exactly one, use it; if multiple, list and ask; if none, ask user)
3. Read manifest at `{WORKFLOW_DIR}/{feature}/aidlc-manifest.yaml` if it exists
4. Resolve project context input (manifest → user override → conventional path → ask)
5. Resolve requirements input (manifest → user override → conventional path → ask)
6. Resolve personas input (manifest → conventional path → skip silently)

---

## Process

### Action: unit-decisions

Generate the D2 decisions file at `{WORKFLOW_DIR}/{feature}/decisions-units.md`.

Read `{ASSETS_DIR}/decision-gate.md` for the output structure.

**Rules**:
- Always generate with blank `Answer:` fields — never pre-fill
- If user said "use recommendations" on a previous gate, that does NOT carry forward
- Include context summary from requirements.md and context.md
- Generate questions covering:
  - **Decomposition need**: Does this project warrant decomposition?
  - **Architecture pattern**: Modular Monolith / Microservices / Distributed / Single Unit
  - **Decomposition strategy**: Domain-Driven / Layer-Based / User Journey-Based / Hybrid
  - **Unit proposals**: Proposed units with story assignments
  - **Dependencies**: How units interact (data, API, events)
  - **Development sequence**: Which units first, which can be parallel

Present:

```
📍 Decomposition: Decision Gate D2 (3 of 6 phases)

- **Decisions**: [X] questions covering decomposition, architecture, strategy, units

📝 Open `{WORKFLOW_DIR}/{feature}/decisions-units.md`, fill answers, say "done"
🤖 Or say "use recommendations" to auto-fill with recommended options

---
🔲 **Your turn**:
- ✏️ Fill answers in the file and say "done"
- 🤖 "use recommendations" — auto-fill for THIS gate
```

**STOP and wait.**

---

### Action: validate-d2

**D2 Validation Rules**:

| Rule | Severity | Detection | Questions | Options |
|---|---|---|---|---|
| Over-Decomposition for Small Project | 🟡 Medium | stories≤10 AND units≥4 AND manifest `context-summary.teamSize`∈{solo,small} | What's the rationale for this level of decomposition? Is the added complexity worth the benefits? | 1. Reduce to 2-3 units (simpler coordination) 2. Skip decomposition (single unit, monolithic approach) 3. Keep current decomposition (team has experience, anticipating growth) |
| Microservices for Small Team | 🔴 High | arch=Microservices AND manifest `context-summary.teamSize`∈{solo,small} AND stories≤15 | Does the team have microservices experience? Is the operational overhead manageable? Are you anticipating rapid team growth? | 1. Start with Modular Monolith (easier to manage, can split later) 2. Use Microservices (team experienced, clear rationale) 3. Hybrid approach (monolith with service boundaries defined) |
| Circular Dependencies | 🔴 High | Unit A→B→A (direct or transitive) | Can we break this circular dependency? Should these be combined into one unit? | 1. Introduce shared library/module for common functionality 2. Merge units into single unit 3. Refactor to remove circular dependency 4. Use event-driven pattern to decouple |
| Unit Too Small | 🟡 Medium | Any unit has <2 stories assigned | Unit "{name}" has only {N} story. Is it worth the overhead of a separate unit? | 1. Merge into a related unit 2. Keep as separate unit (critical boundary justification) 3. Add more stories from backlog |
| Unit Too Large | 🟡 Medium | Any unit has >15 stories assigned | Unit "{name}" has {N} stories. Can it be split into smaller, more focused units? | 1. Split into 2-3 sub-units by subdomain 2. Move lower-priority stories to a future phase 3. Keep as-is (stories are tightly coupled) |
| Bottleneck Unit | 🟡 Medium | Any unit has >3 other units depending on it | Unit "{name}" is a dependency for {N} other units. This creates a bottleneck — all dependent units are blocked until it's done. | 1. Extract the shared interface into a lightweight shared package 2. Reduce dependencies by duplicating minimal shared logic 3. Keep (implement this unit first, accept sequential dependency) |
| Missing Shared Kernel | 🟡 Medium | 3+ units reference the same entities AND no shared kernel/library unit proposed | Multiple units share entities ({list}). Without a shared kernel, each unit will define its own version, leading to drift. | 1. Add a shared types/kernel unit or package 2. Designate one unit as the owner, others consume via API 3. Keep separate definitions (accept sync overhead) |
| Unbalanced Distribution | 🟢 Low | Largest unit has 3x+ more stories than smallest unit | Story distribution is unbalanced: {largest} has {N} stories vs {smallest} with {M}. | 1. Rebalance by moving stories between units 2. Keep (units represent natural domain boundaries) |

Present conflicts grouped by severity, ask for resolution. User can skip validation.

After resolution, write decision summary to manifest `decisions.decomposition` (compact key-value pairs from Decisions Summary section).

### Action: unit-generation

Generate `{SPECS_DIR}/{feature}/units.md` using `{ASSETS_DIR}/units.md` template.

- Read decisions from manifest `decisions.decomposition` section. Fall back to reading `## Decisions Summary` from D2 file if manifest section is missing.
- Assign every story to exactly one unit
- Define interfaces and dependencies using DDD concepts
- Define Context Map relationships

**Validate**:
- ✅ All stories assigned to exactly one unit
- ✅ Clear boundaries and interfaces
- ✅ Dependencies identified with types (Data/API/Event)
- ✅ No circular dependencies
- ✅ Infrastructure units with `Source: foundation` preserved from previous runs (do not remove or overwrite them — they are managed by the foundation skill)

**Update Manifest**: Add `decomposition` phase entry: `status: "draft"`, `timestamp`, `files: [units.md]`.

**Present**:

```
📍 Decomposition: Units of Work (3 of 6 phases)

- **Units**: [X] units — [list names]
- **Strategy**: [strategy]
- **Story Distribution**: [Unit1: X, Unit2: Y]
- **Dependencies**: [count] identified

Artifact at `{SPECS_DIR}/{feature}/units.md`.

---
🔲 **Your turn**:
- ✅ "approve" — approve units and choose delivery mode
- ✏️ "change [what]" — request edits
```

**STOP and wait.**

---

### Action: units-edit

1. Read current units.md
2. Apply changes (merge/split units, reassign stories, update dependencies)
3. Re-validate: all stories assigned, no circular deps, clear boundaries
4. Mark downstream artifacts as `outdated` in manifest (foundation, design, tasks — any that exist)
5. Present with `🔲 **Your turn**` block. **STOP.**

---

### After Units Approved — Mode Selection

On approval: update manifest (`artifacts.decomposition.status`: `"approved"`, add `"decomposition"` to `state.sharedPhases`). **Populate `units[]` array** — for each unit in the generated `units.md`, create an entry: `{ name: "{unit-name}", status: "not-started", phase: null, completedPhases: [], implementationMode: null, implementation: { totalTasks: 0, completedTasks: 0, currentTask: null, currentWave: null }, artifacts: {}, decisions: {} }`. Append audit entry. If platform is Claude Code, update `CLAUDE.md` (set Phase to "decomposition").

#### Determine Recommendation

Read context.md Summary section to check project type:
- **Brownfield**: The codebase already has established conventions (auth, error handling, repo structure, communication patterns). Foundation adds little value — recommend skipping it.
- **Greenfield**: No existing conventions. Foundation is important for aligning units — recommend it.

#### Present Mode Choice

```
📍 Units Approved — Choose Delivery Mode

Your project has [X] units. How do you want to proceed?

| Mode | Setup | Coupling | Best For |
|------|-------|----------|----------|
| **incremental** | Longer (foundation first) | Low — units designed independently | Teams, greenfield, 3+ units |
| **incremental (skip foundation)** | Faster (no foundation) | Low — uses existing conventions | Brownfield with established patterns |
| **comprehensive** | Fastest (single design pass) | Higher — all units designed together | Solo dev, tightly coupled units, ≤3 units |

👉 Recommendation: {incremental (skip foundation) for brownfield / incremental for greenfield / comprehensive for 2 tightly-coupled units}
Reason: {brief explanation}

---
🔲 **Your turn**:
- 🔹 "incremental" — proceed to foundation specification
- 🔹 "incremental skip foundation" — skip foundation, select first unit
- 🔹 "comprehensive" — skip foundation, single design for all units
```

**STOP and wait.**

**If incremental**: Update manifest (`state.mode: "incremental"`). Auto-continue to `aidlc-foundation` (see Skill Handoff).

**If incremental skip foundation**: Update manifest (`state.mode: "incremental"`, `state.foundationSkipped: true`). Skip foundation — proceed directly to unit selection (below).

**If comprehensive**: Update manifest (`state.mode: "comprehensive"`). Auto-continue to `aidlc-design` (see Skill Handoff).

---

### Unit Selection (After Skip Foundation)

When the user chooses "incremental skip foundation", present the unit list for selection:

```
📍 Foundation Skipped — Select First Unit

Using existing codebase conventions. Ready to design and implement units one at a time.

**Domain units**:
1. 📦 [Unit A] — [purpose] ([X] stories)
2. 📦 [Unit B] — [purpose] ([Y] stories)

---
🔲 **Your turn**:
- 🎯 "select [unit name]" — start working on that unit
- 📋 "show units" — see full unit details
```

**STOP and wait.**

When user selects a unit:
1. Update manifest: set `units[{unit}].status` to `"in-progress"`, set `units[{unit}].phase` to `"design"`
2. Auto-continue to `aidlc-design` (see Skill Handoff)

---

## Decomposition Strategies Reference

For decomposition strategies (domain-driven, layer-based, user-journey, hybrid), sizing guidance, DDD concepts, and common pitfalls, read `{SKILL_DIR}/references/decomposition-strategies.md` when generating units.

---

## Skill Handoff

When the user chooses a delivery mode, auto-continue:

1. **Incremental** → read `{PLATFORM_DIR}/skills/aidlc-foundation/SKILL.md` and follow its instructions
2. **Incremental (skip foundation)** → present unit selection (above), then on unit selection read `{PLATFORM_DIR}/skills/aidlc-design/SKILL.md` and follow its instructions scoped to the selected unit
3. **Comprehensive** → read `{PLATFORM_DIR}/skills/aidlc-design/SKILL.md` and follow its instructions

If the next skill's SKILL.md cannot be found, fall back to:
```
👉 Next: Activate **aidlc-foundation** (incremental), **aidlc-design** (skip foundation / comprehensive).
```

---

## Behavioral Rules

### Rules
- Language: user's language for content, English for paths/code/tech terms. Silent on internal operations (manifest, audit, templates, platform detection).
- Tools — Kiro: `fsWrite`, `readMultipleFiles`. Claude Code: `Write`/`Edit`, parallel `Read`. Cursor/Windsurf: `Write`/`Edit`, sequential reads.
- Recovery: read `{STEERING_DIR}/aidlc-workflow.md` → manifest → SKILL.md → resume from current action.
- Errors: report clearly with what happened and what to do. Offer rebuild/retry. Never lose work silently.
- Optional file reads: If a file read fails, check whether the file exists. If it exists but can't be read, warn: "⚠️ File exists but could not be read: {path}". If it doesn't exist, skip silently (expected for optional inputs).

### Audit Trail
Append to `{WORKFLOW_DIR}/{feature}/audit.md` after: decision gate, validation, generation, approval, edit.

Use the standard audit entry format:

```
### [{ISO timestamp}] {Phase}: {Action}

**Phase**: decomposition
**Action**: {decision-gate | validation | generation | approval | edit}
**Artifacts**: {files created or modified}
**Outcome**: {result summary — e.g., "4 units defined, domain-driven strategy, 12 stories assigned"}
```
