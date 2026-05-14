# Security Assessment — Output Template

**Path**: `{OUTPUT_DIR}/security.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Security Assessment

## Summary

[Brief characterization of security posture: auth coverage, input validation maturity, dependency health, secrets management, and overall risk level (low/medium/high).]

## Authentication & Authorization

### Auth Coverage

| Area | Protected | Mechanism | Gaps |
|---|---|---|---|
| [route group or module] | [yes/partial/no] | [JWT/session/API-key/OAuth/none] | [unprotected endpoints or weak enforcement] |

### Authorization Model

- **Pattern**: [RBAC/ABAC/ACL/custom/none]
- **Roles Defined**: [list]
- **Enforcement**: [middleware/decorator/manual check/none]
- **Gaps**: [endpoints without role checks, privilege escalation risks]

## Input Validation & Sanitization

| Area | Validation Present | Library/Approach | Gaps |
|---|---|---|---|
| [API inputs] | [yes/partial/no] | [Zod/Joi/class-validator/manual/none] | [unvalidated fields, missing sanitization] |
| [Database queries] | [parameterized/raw/mixed] | [ORM/prepared statements/string concat] | [SQL injection vectors] |
| [User-generated content] | [sanitized/raw] | [DOMPurify/bleach/manual/none] | [XSS vectors] |
| [File uploads] | [validated/unvalidated] | [type check/size limit/none] | [unrestricted upload risks] |

## Secrets & Credentials

| Finding | Type | Location | Risk |
|---|---|---|---|
| [description] | [hardcoded-secret/env-var-in-code/weak-default/exposed-in-logs] | [file:line] | [high/medium/low] |

### Secrets Management

- **Approach**: [env vars / secrets manager / config files / hardcoded]
- **Rotation**: [automated/manual/none detected]
- **.gitignore coverage**: [adequate/gaps — list unignored sensitive files]

## Dependency Vulnerabilities

| Package | Current Version | Issue | Severity | CVE |
|---|---|---|---|---|
| [name] | [version] | [known vulnerability / EOL / unmaintained] | [critical/high/medium/low] | [CVE-ID or N/A] |

## Security Headers & Configuration

| Header/Config | Status | Value | Recommendation |
|---|---|---|---|
| CORS | [configured/missing/overly-permissive] | [value] | [recommendation] |
| CSP | [configured/missing] | [value] | [recommendation] |
| Rate Limiting | [present/absent] | [config] | [recommendation] |
| HTTPS enforcement | [yes/no/partial] | [config] | [recommendation] |

## Data Exposure Risks

| Risk | Type | Location | Description |
|---|---|---|---|
| [description] | [PII-in-logs/overly-broad-response/missing-field-filtering/debug-endpoints] | [file:line] | [details] |

## Security Debt Summary

| # | Issue | Severity | Category | Location | Remediation |
|---|---|---|---|---|---|
| 1 | [description] | [critical/high/medium/low] | [auth/input/secrets/deps/config/data] | [file:line] | [suggested fix] |
~~~
