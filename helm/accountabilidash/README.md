# Accountabilidash Helm Chart

Deploys the full Accountabilidash stack: PostgreSQL, FastAPI backend, and Vite React frontend.

## Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.x
- Ingress controller (e.g. nginx-ingress) if using ingress

## CI/CD (GitHub Container Registry)

A GitHub Actions workflow builds and pushes images to ghcr.io on every push to `main`:

- `ghcr.io/<owner>/accountabilidash-backend:latest`
- `ghcr.io/<owner>/accountabilidash-frontend:latest`

To use these images, set `global.imageOwner` to your GitHub org:

```bash
helm install accountabilidash ./helm/accountabilidash -n accountabilidash --create-namespace \
  --set global.imageOwner=YOUR_GITHUB_ORG
```

**Note:** If your GHCR images are private, create an image pull secret and add it to `global.imagePullSecrets`. For public images, go to your repo → Packages → Package settings → Change visibility.

## Quick Start (with GHCR)

1. **Ensure CI has built images** (push to `main` or trigger the workflow manually).

2. **Install the chart** (replace `YOUR_GITHUB_ORG` with your org):

   ```bash
   helm install accountabilidash ./helm/accountabilidash -n accountabilidash --create-namespace \
     --set global.imageOwner=YOUR_GITHUB_ORG
   ```

3. **Access the app** (with ingress enabled):

   Add to `/etc/hosts`:
   ```
   127.0.0.1 accountabilidash.local
   ```

   Then visit http://accountabilidash.local (ensure your ingress controller is running).

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Image registry | `ghcr.io` |
| `global.imageOwner` | GHCR org/owner (e.g. `myorg`) | `owner` |
| `postgres.enabled` | Deploy PostgreSQL | `true` |
| `postgres.auth.password` | Postgres password | `postgres` |
| `postgres.persistence.size` | PVC size for postgres | `8Gi` |
| `backend.image.repository` | Backend image name | `accountabilidash-backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.secretKey` | JWT secret (auto-generated if empty) | `""` |
| `frontend.image.repository` | Frontend image name | `accountabilidash-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `ingress.enabled` | Create Ingress | `true` |
| `ingress.hosts[0].host` | Ingress hostname | `accountabilidash.local` |

## Production

Override sensitive values:

```bash
helm install accountabilidash ./helm/accountabilidash \
  -n accountabilidash --create-namespace \
  --set postgres.auth.password=$(openssl rand -base64 24) \
  --set backend.secretKey=$(openssl rand -base64 32)
```

Or use a custom values file:

```yaml
# values-prod.yaml
postgres:
  auth:
    password: <secure-password>
  persistence:
    size: 20Gi

backend:
  secretKey: <secure-secret>
  replicaCount: 2
  env:
    ALLOW_REGISTRATION: "false"

ingress:
  enabled: true
  className: nginx
  tls:
    - secretName: accountabilidash-tls
      hosts:
        - accountabilidash.example.com
```

## Local Development (Minikube/Kind)

```bash
# Use Minikube's Docker daemon so images are available
eval $(minikube docker-env)
docker build -t accountabilidash-backend:latest backend/
docker build -t accountabilidash-frontend:latest --build-arg VITE_API_BASE_URL= frontend/

helm install accountabilidash ./helm/accountabilidash -n accountabilidash --create-namespace
minikube addons enable ingress
```
