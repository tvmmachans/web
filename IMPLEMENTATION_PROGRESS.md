# Production Readiness Implementation Progress

## 1. Repository Layout Adjustments
- [ ] Rename dashboard/ to frontend/ (move contents and remove old directory)

## 2. Docker and Containerization
- [ ] Create multi-stage Dockerfile.backend with non-root user and production optimizations
- [ ] Create multi-stage Dockerfile.frontend with non-root user and production optimizations
- [ ] Update infra/docker-compose.yml to use frontend instead of dashboard

## 3. Database and Migrations
- [ ] Set up Alembic in backend (alembic.ini, versions/, env.py)
- [ ] Create scripts/init_local.sh for local DB bootstrap and migrations

## 4. Monitoring and Observability
- [ ] Add Prometheus metrics endpoints (/metrics) to backend using prometheus-fastapi-instrumentator
- [ ] Add Prometheus metrics endpoints (/metrics) to agent
- [ ] Create Grafana dashboard JSON example (infra/grafana-dashboard.json)
- [ ] Create alert rules example for Prometheus (infra/prometheus-alerts.yml)

## 5. Security Enhancements
- [ ] Implement rate limiting middleware in backend using slowapi
- [ ] Add signed URL support for S3 storage in video_service.py

## 6. Orchestration and Deployment
- [ ] Create Kubernetes manifests in infra/k8s/ (namespace, deployments, services, ingress, secrets, configmaps, HPA)
- [ ] Create GitHub Actions workflow (.github/workflows/ci-cd.yml) for CI/CD

## 7. Testing Improvements
- [ ] Add more unit tests for backend endpoints and integration tests
- [ ] Create basic E2E test stub for frontend using Playwright

## 8. Documentation Updates
- [ ] Update README.md with startup, environment instructions, architecture diagram
- [ ] Create RUNBOOK.md with deployment, backup, restore, migration, rollback steps

## 9. Environment Configuration
- [ ] Update .env.example with all required environment variables

## Dependencies to Install
- [ ] Backend: prometheus-fastapi-instrumentator, slowapi, alembic
- [ ] Frontend: playwright for E2E tests
