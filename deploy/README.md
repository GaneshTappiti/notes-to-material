## Deployment (GCP Cloud Run / GKE)

### Container Images
Build images:
```
docker build -t gcr.io/PROJECT_ID/studyforge-backend:$(git rev-parse --short HEAD) backend
docker build -t gcr.io/PROJECT_ID/studyforge-frontend:$(git rev-parse --short HEAD) frontend
docker push gcr.io/PROJECT_ID/studyforge-backend:$(git rev-parse --short HEAD)
docker push gcr.io/PROJECT_ID/studyforge-frontend:$(git rev-parse --short HEAD)
```

### Cloud Run (simplest)
```
gcloud run deploy studyforge-backend \
  --image gcr.io/PROJECT_ID/studyforge-backend:SHA \
  --region REGION --allow-unauthenticated \
  --set-env-vars JWT_SECRET=change,GOOGLE_API_KEY=xxx

gcloud run deploy studyforge-frontend \
  --image gcr.io/PROJECT_ID/studyforge-frontend:SHA \
  --region REGION --allow-unauthenticated
```

### GKE (Helm sketch)
values.yaml excerpt:
```yaml
backend:
  image: gcr.io/PROJECT_ID/studyforge-backend:SHA
  env:
    JWT_SECRET: change
    GOOGLE_API_KEY: xxx
frontend:
  image: gcr.io/PROJECT_ID/studyforge-frontend:SHA
```

Deploy:
```
helm upgrade --install studyforge ./chart -f values.yaml
```

### Terraform Skeleton
```hcl
resource "google_artifact_registry_repository" "containers" {
  repository_id = "studyforge"
  format       = "DOCKER"
  location     = var.region
}

resource "google_cloud_run_service" "backend" {
  name     = "studyforge-backend"
  location = var.region
  template {
    spec { containers { image = var.backend_image env { name="JWT_SECRET" value=var.jwt_secret } } }
  }
  traffics { percent = 100 latest_revision = true }
}
```

## Environment Variables
See `monitoring/README.md` for full list. Minimum:
JWT_SECRET, GOOGLE_API_KEY (optional), DATABASE_URL (optional), ECHO_SQL, UVICORN_WORKERS.

## Secrets Management
Use Google Secret Manager or GitHub Actions OIDC -> workload identity. Do not bake secrets into images.

## Cost Controls
Scale Cloud Run min instances = 0. Set concurrency 80 for backend. Restrict egress.
