# Data Model — Output Template

**Path**: `{OUTPUT_DIR}/data-model.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Data Model

## Summary

[detected] entities extracted from [source: ORM models / SQL migrations / schema files]. [Brief characterization of data architecture.]

## Entities

| Entity | Source | Fields | Relationships |
|---|---|---|---|
| [name] | [file:line] | [count] | [list] |

## Entity Details

### [Entity Name]

**Source**: `[file:line]`

#### Fields

| Field | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| [name] | [type] | [yes/no] | [value] | [unique/fk/check] |

#### Relationships

| Target | Type | FK | Cascade |
|---|---|---|---|
| [entity] | [1:1/1:N/N:M] | [field] | [delete/update behavior] |

#### Indexes

| Name | Fields | Type |
|---|---|---|
| [name] | [fields] | [unique/btree/gin] |

#### Access Patterns

- [detected query patterns — e.g., "lookup by email", "list by status with pagination"]

## ER Diagram

```
[ASCII ER diagram]

  ┌──────────┐       ┌──────────┐
  │   User   │──1:N──│  Order   │
  └──────────┘       └────┬─────┘
                          │ N:M
                     ┌────▼─────┐
                     │ Product  │
                     └──────────┘
```
~~~
