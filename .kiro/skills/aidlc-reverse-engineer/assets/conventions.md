# Conventions — Output Template

**Path**: `{OUTPUT_DIR}/conventions.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Conventions

## Summary

[Brief characterization of codebase consistency, detected patterns, and notable deviations.]

## Naming Conventions

| Element | Convention | Example | Consistency |
|---|---|---|---|
| Files | [detected — e.g., kebab-case] | [example] | [high/medium/low] |
| Functions | [detected — e.g., camelCase] | [example] | [high/medium/low] |
| Classes | [detected — e.g., PascalCase] | [example] | [high/medium/low] |
| Variables | [detected] | [example] | [high/medium/low] |
| DB Tables | [detected] | [example] | [high/medium/low] |
| Routes | [detected] | [example] | [high/medium/low] |

## Error Handling

- **Pattern**: [detected — e.g., centralized middleware, per-handler try/catch, Result type]
- **Location**: `[file:line]`
- **Custom Errors**: [yes/no — list if yes]
- **Consistency**: [high/medium/low]

## Auth Pattern

- **Pattern**: [detected — e.g., middleware guard, decorator-based, manual check]
- **Location**: `[file:line]`
- **Applied Via**: [middleware/decorator/manual]
- **Consistency**: [high/medium/low]

## Logging Pattern

- **Library**: [detected or built-in]
- **Format**: [detected — e.g., structured JSON, plain text]
- **Levels Used**: [list]
- **Consistency**: [high/medium/low]

## Testing Pattern

- **Framework**: [detected]
- **Style**: [detected — e.g., unit + integration, BDD, TDD]
- **Location**: [co-located / separate `__tests__` / `test/` directory]
- **Mocking**: [detected approach]
- **Consistency**: [high/medium/low]

## Code Organization

- **Pattern**: [detected — e.g., feature-based, layer-based, hybrid]
- **Example Structure**:
```
[detected directory layout snippet]
src/
  [module]/
    [controller/handler]
    [service]
    [model/entity]
    [test]
```
~~~
