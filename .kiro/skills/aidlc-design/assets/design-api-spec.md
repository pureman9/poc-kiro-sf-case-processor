# API Specification Template

**Path**: `{SPECS_DIR}/{feature}/design/api-spec.md`

```markdown
# API Specification

## Overview
**API Style**: [REST/GraphQL/gRPC]
**Base URL**: `https://api.example.com/v1`
**Auth**: [JWT/OAuth 2.0/API Keys] via `Authorization: Bearer <token>`

## API Conventions
- **Pagination**: [Cursor-based/Offset-based] — `?page=1&limit=20`
- **Filtering**: `?filter[field]=value`
- **Sorting**: `?sort=field:desc`
- **Rate Limit**: [X requests/minute authenticated, Y unauthenticated]
- **Versioning**: [URL-based `/api/v1/`]

## Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": [{"field": "fieldName", "message": "Error"}]
  }
}
```

---

## Endpoints

### [Resource Group 1]

#### [METHOD] /api/v1/[resource]
- **Description**: [What it does]
- **Auth**: [Required role or "Public"]
- **Source**: [D3 decisions / OpenAPI spec: operation ID / "Derived from requirements"]
- **Request**:
```json
{"field1": "string", "field2": 123}
```
- **Response 200**:
```json
{"id": "uuid", "field1": "string", "createdAt": "ISO-8601"}
```
- **Errors**: 400 Invalid request, 401 Unauthorized, 404 Not found

#### [METHOD] /api/v1/[resource]/{id}
- **Description**: [What it does]
- **Auth**: [Required role]
- **Response 200**:
```json
{"id": "uuid", "field1": "string"}
```
- **Errors**: 401 Unauthorized, 404 Not found

---

### [Resource Group 2]

[Same structure]

---

## GraphQL Schema (if D3 api-style = GraphQL)

> Include this section ONLY if D3 chose GraphQL. Remove the REST Endpoints section above.

### Type Definitions
```graphql
type [Entity] {
  id: ID!
  [field]: [Type]!
  [relation]: [RelatedType]
}

input Create[Entity]Input {
  [field]: [Type]!
}

input Update[Entity]Input {
  [field]: [Type]
}
```

### Queries
```graphql
type Query {
  [entity](id: ID!): [Entity]
  [entities](filter: [Entity]Filter, pagination: PaginationInput): [Entity]Connection!
}
```

### Mutations
```graphql
type Mutation {
  create[Entity](input: Create[Entity]Input!): [Entity]!
  update[Entity](id: ID!, input: Update[Entity]Input!): [Entity]!
  delete[Entity](id: ID!): Boolean!
}
```

### Subscriptions (if real-time needed)
```graphql
type Subscription {
  [entity]Updated(id: ID): [Entity]!
  [entity]Created: [Entity]!
}
```

### Error Handling
```graphql
type UserError {
  field: [String!]
  message: String!
  code: String!
}
```

---

## gRPC Service Definitions (if D3 api-style = gRPC)

> Include this section ONLY if D3 chose gRPC. Remove the REST Endpoints section above.

### Proto File: `[service].proto`
```protobuf
syntax = "proto3";
package [feature].[service];

service [Service]Service {
  rpc Get[Entity] (Get[Entity]Request) returns ([Entity]Response);
  rpc List[Entities] (List[Entities]Request) returns (List[Entities]Response);
  rpc Create[Entity] (Create[Entity]Request) returns ([Entity]Response);
  rpc Update[Entity] (Update[Entity]Request) returns ([Entity]Response);
  rpc Delete[Entity] (Delete[Entity]Request) returns (Empty);
  // Streaming (if applicable)
  rpc Stream[Events] (Stream[Events]Request) returns (stream [Event]Response);
}

message [Entity]Response {
  string id = 1;
  [type] [field] = 2;
  google.protobuf.Timestamp created_at = 3;
}

message Get[Entity]Request {
  string id = 1;
}

message List[Entities]Request {
  int32 page_size = 1;
  string page_token = 2;
  string filter = 3;
}

message List[Entities]Response {
  repeated [Entity]Response [entities] = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

### Error Handling
Use standard gRPC status codes: `NOT_FOUND`, `INVALID_ARGUMENT`, `PERMISSION_DENIED`, `INTERNAL`.
```
