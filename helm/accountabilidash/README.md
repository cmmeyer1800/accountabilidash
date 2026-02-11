# Accountabilidash Helm Chart

Deploys the full Accountabilidash stack: FastAPI backend and Vite React frontend. PostgreSQL is only deployed when using CloudNative-PG; otherwise you configure an external connection.

## Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.x
- Ingress controller (e.g. nginx-ingress) if using ingress
- PostgreSQL (external or via CloudNative-PG)

## PostgreSQL Options

### CloudNative-PG (operator deploys Postgres)

When the CloudNative-PG operator is installed, enable it to deploy a PostgreSQL cluster. The operator is added as a chart dependency:

```bash
helm install accountabilidash ./helm/accountabilidash -n accountabilidash --create-namespace \
  --set postgres.useCloudNativePG=true
```

This installs the operator and creates a Cluster CR. The backend connects to `<cluster-name>-rw`.

### External PostgreSQL (default)

When `postgres.useCloudNativePG` is false, the chart does not deploy any database. You must provide an external connection:

```bash
# 1. Create a secret with your DB password
kubectl create secret generic my-postgres-secret \
  --from-literal=password=YOUR_DB_PASSWORD \
  -n accountabilidash

# 2. Install with external postgres config
helm install accountabilidash ./helm/accountabilidash -n accountabilidash --create-namespace \
  --set postgres.external.host=my-postgres.example.com \
  --set postgres.external.existingSecret=my-postgres-secret \
  --set postgres.auth.username=postgres \
  --set postgres.auth.database=accountabilidash
```

Use `postgres.external.passwordKey` if your secret uses a different key (default: `password`).

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgres.useCloudNativePG` | Deploy Postgres via CloudNative-PG operator | `false` |
| `postgres.external.host` | External Postgres host (required when useCloudNativePG=false) | `""` |
| `postgres.external.port` | External Postgres port | `5432` |
| `postgres.external.existingSecret` | Secret with DB password (required when useCloudNativePG=false) | `""` |
| `postgres.external.passwordKey` | Key in secret for password | `password` |
| `postgres.cnpg.clusterName` | CNPG cluster name (service: `<name>-rw`) | `accountabilidash-db` |
| `postgres.cnpg.instances` | Number of PostgreSQL instances (CNPG) | `1` |
| `global.imageOwner` | GHCR org for app images | `cmmeyer1800` |
| `ingress.enabled` | Create Ingress | `true` |

## Production

Override sensitive values:

```bash
helm install accountabilidash ./helm/accountabilidash \
  -n accountabilidash --create-namespace \
  --set postgres.auth.password=$(openssl rand -base64 24) \
  --set backend.secretKey=$(openssl rand -base64 32)
```

With CloudNative-PG:

```bash
helm install accountabilidash ./helm/accountabilidash \
  -n accountabilidash --create-namespace \
  --set postgres.useCloudNativePG=true \
  --set postgres.cnpg.instances=3 \
  --set postgres.auth.password=$(openssl rand -base64 24) \
  --set backend.secretKey=$(openssl rand -base64 32)
```
