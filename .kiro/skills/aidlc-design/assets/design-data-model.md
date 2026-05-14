# Data Model Template

**Path**: `{SPECS_DIR}/{feature}/design/data-model.md`

Entities, relationships, and storage strategy.

```markdown
# Data Model

## Overview
**Database**: [PostgreSQL/MongoDB/DynamoDB/etc.]
**ORM/Client**: [Prisma/TypeORM/Mongoose/etc.]

---

## Entities

### [Entity 1 Name]

**Purpose**: [What this entity represents]

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | Yes | PK | Unique identifier |
| [field] | [type] | [Yes/No] | [constraints] | [description] |
| createdAt | Timestamp | Yes | Auto | Creation time |

**Relationships**:
- Has Many: `[RelatedEntity]` via `[foreign_key]`
- Belongs To: `[ParentEntity]` via `[foreign_key]`

**Indexes**:
- Unique: `[field]`
- Composite: `[field1, field2]` — [purpose]

**Business Rules**:
1. [Rule 1]
2. [Rule 2]

---

### [Entity 2 Name]

[Same structure]

---

## Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│   Entity1   │         │   Entity2   │
├─────────────┤         ├─────────────┤
│ PK: id      │────1:N──│ FK: entity1 │
│     name    │         │     value   │
└─────────────┘         └─────────────┘
```

---

## Data Access Patterns

| Query | Frequency | Index Used |
|-------|-----------|------------|
| [Description] | [High/Medium/Low] | [Index name] |

---

## Document Database Schema (if D3 database = MongoDB/DocumentDB)

> Include this section ONLY if D3 chose a document database. Adapt the Entities section above to use document schemas instead of tables.

### Collection: [collection_name]

**Purpose**: [What this collection stores]

```json
{
  "_id": "ObjectId",
  "[field]": "[type]",
  "[embedded]": {
    "[subfield]": "[type]"
  },
  "[array_field]": ["[type]"],
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

**Embedding vs Referencing**:
| Related Data | Strategy | Rationale |
|---|---|---|
| [Related entity] | Embed / Reference | [Why — e.g., "Always accessed together" or "Updated independently"] |

**Indexes**:
- `{ [field]: 1 }` — [purpose]
- `{ [field1]: 1, [field2]: -1 }` — compound, [purpose]
- `{ [field]: "text" }` — text search (if needed)

---

## DynamoDB Table Design (if D3 database = DynamoDB)

> Include this section ONLY if D3 chose DynamoDB. Replace the Entities section above with access-pattern-driven design.

### Table: [table_name]

**Key Schema**:
| Key | Attribute | Type | Description |
|-----|-----------|------|-------------|
| PK | `[partition_key]` | S | [e.g., `USER#<userId>`] |
| SK | `[sort_key]` | S | [e.g., `ORDER#<orderId>`] |

**Access Patterns**:
| # | Access Pattern | Key Condition | Index | Example |
|---|---|---|---|---|
| 1 | [Get user by ID] | `PK = USER#<id>` AND `SK = PROFILE` | Table | `PK=USER#123, SK=PROFILE` |
| 2 | [List user orders] | `PK = USER#<id>` AND `SK begins_with ORDER#` | Table | `PK=USER#123, SK=ORDER#*` |
| 3 | [Get order by ID] | `GSI1PK = ORDER#<id>` | GSI1 | `GSI1PK=ORDER#456` |

**Global Secondary Indexes**:
| GSI | PK | SK | Projection | Purpose |
|-----|----|----|------------|---------|
| GSI1 | `GSI1PK` | `GSI1SK` | ALL / KEYS_ONLY | [purpose] |

**Item Types** (single-table design):
| Entity | PK Pattern | SK Pattern | Attributes |
|--------|-----------|------------|------------|
| [User] | `USER#<id>` | `PROFILE` | name, email, role |
| [Order] | `USER#<userId>` | `ORDER#<orderId>` | status, total, items |
```
