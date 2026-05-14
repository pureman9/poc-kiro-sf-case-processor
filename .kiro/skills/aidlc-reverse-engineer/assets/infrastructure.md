# Infrastructure & Deployment — Output Template

**Path**: `{OUTPUT_DIR}/infrastructure.md`

~~~markdown
<!-- Analyzed: {ISO timestamp} | Scope: {scope} -->
# Infrastructure & Deployment

## Summary

[Brief characterization: hosting approach, CI/CD maturity, containerization status, IaC coverage.]

## Containerization

| Component | Dockerfile | Base Image | Multi-Stage | Health Check |
|---|---|---|---|---|
| [service name] | [path] | [image:tag] | [yes/no] | [yes/no] |

### Docker Compose / Local Dev

- **File**: `[path or N/A]`
- **Services**: [list of services defined]
- **Volumes**: [persistent data mounts]
- **Networks**: [network topology]

## CI/CD Pipeline

| Stage | Tool | Config File | What It Does |
|---|---|---|---|
| [lint] | [GitHub Actions/GitLab CI/Jenkins/etc.] | [path] | [description] |
| [test] | [same] | [path] | [description] |
| [build] | [same] | [path] | [description] |
| [deploy] | [same] | [path] | [description] |

### Pipeline Characteristics

- **Trigger**: [on push / on PR / manual / scheduled]
- **Environments**: [which environments are deployed automatically]
- **Approval Gates**: [manual approval required? where?]
- **Artifacts**: [what gets built — container images, packages, binaries]
- **Duration**: [estimated from config if detectable]

## Infrastructure as Code

| Tool | Files | Resources Managed |
|---|---|---|
| [Terraform/CDK/CloudFormation/Pulumi/none] | [paths] | [what infrastructure is defined] |

### Cloud Resources (detected from IaC or config)

| Resource | Type | Purpose | Config Location |
|---|---|---|---|
| [name] | [database/cache/queue/storage/compute/CDN] | [description] | [file:line] |

## Hosting & Runtime

- **Platform**: [AWS/GCP/Azure/Vercel/Heroku/self-hosted/unknown]
- **Compute**: [ECS/Lambda/EC2/K8s/App Engine/containers/VMs]
- **Database**: [RDS/DynamoDB/Cloud SQL/self-managed/etc.]
- **Cache**: [ElastiCache/Redis/Memcached/none]
- **Queue/Events**: [SQS/SNS/Kafka/RabbitMQ/none]
- **Storage**: [S3/GCS/local filesystem/none]
- **CDN**: [CloudFront/Cloudflare/none]

## Database Management

- **Migration Tool**: [Flyway/Alembic/Prisma Migrate/knex/ActiveRecord/none]
- **Migration Location**: `[path]`
- **Migration Count**: [number of migrations]
- **Seed Data**: [present/absent — path if present]
- **Backup Strategy**: [detected or unknown]

## Monitoring & Observability

| Aspect | Tool | Config | Coverage |
|---|---|---|---|
| Logging | [detected] | [path] | [all services / partial / none] |
| Metrics | [detected or none] | [path] | [coverage] |
| Tracing | [detected or none] | [path] | [coverage] |
| Alerting | [detected or none] | [path] | [coverage] |
| Error tracking | [Sentry/Bugsnag/none] | [path] | [coverage] |
~~~
