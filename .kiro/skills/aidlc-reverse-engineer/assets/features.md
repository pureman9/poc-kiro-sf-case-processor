# Features — Output Template

**Path**: `{OUTPUT_DIR}/features.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Features

## Summary

[detected] features identified. [count] complete, [count] partial, [count] stubbed. [Brief characterization.]

## Feature Inventory

| Feature | Status | Maturity | Modules | Routes | Entities |
|---|---|---|---|---|---|
| [name] | [complete/partial/stubbed] | [MVP/stable/mature/deprecated] | [list] | [list] | [list] |

## Feature Details

### [Feature Name]

- **Status**: [complete/partial/stubbed]
- **Maturity**: [MVP/stable/mature/deprecated]
- **Description**: [what this feature does from a user perspective]

#### User-Facing Capabilities

- [capability 1]
- [capability 2]

#### Implementing Code Paths

| Component | File | Function/Class |
|---|---|---|
| [route/service/model] | [file:line] | [name] |

#### Dependencies

- **Requires**: [other features this depends on]
- **Required By**: [features that depend on this]

## User Journeys

### [Journey Name — e.g., "User Registration & Onboarding"]

**Actor**: [user type]
**Goal**: [what the user is trying to accomplish]

| Step | Action | Feature | Endpoint/UI | Module |
|---|---|---|---|---|
| 1 | [user action] | [feature name] | [route or page] | [module] |
| 2 | [user action] | [feature name] | [route or page] | [module] |
| 3 | [user action] | [feature name] | [route or page] | [module] |

```
[ASCII flow diagram for complex journeys]

  User ──▶ Register ──▶ Verify Email ──▶ Complete Profile ──▶ Dashboard
                              │
                              ▼ (timeout)
                        Resend Email
```

## Feature Dependencies

```
[ASCII dependency graph showing which features depend on which]

  Authentication ◀── User Management
       │                    │
       ▼                    ▼
  Authorization ◀── Content Management
       │
       ▼
  Audit Logging
```

## Missing / Incomplete Features

| Feature | Evidence | Status | Notes |
|---|---|---|---|
| [name] | [TODO comment / stub / disabled route / empty handler] | [stubbed/planned/abandoned] | [file:line and context] |
~~~
