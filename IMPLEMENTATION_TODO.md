# Detailed Implementation TODO List for Production Readiness

## 1. Repository Layout Adjustments
- [x] Move contents from dashboard/ to frontend/ directory (frontend/ already exists)
- [x] Remove the old dashboard/ directory after moving contents
- [x] Update any references to 'dashboard' in code or configs to 'frontend'

## 2. Docker and Containerization
- [x] Create multi-stage Dockerfile.backend with production optimizations (non-root user, minimal image)
- [x] Create multi-stage Dockerfile.frontend with production optimizations (non-root user, minimal image)
- [x] Update infra/docker-compose.yml to use 'frontend' service instead of 'dashboard'
- [x] Add frontend service to docker-compose.yml with proper build context and ports
- [x] Create .env.example with all required environment variables (DATABASE_URL, REDIS_URL, S3_BUCKET, etc.)

## 3. Database and Migrations
- [x] Install Alembic in backend (add to requirements.txt)
- [x] Create alembic.ini configuration file in backend/
- [x] Create alembic/versions/ directory and env.py for migrations
- [x] Create scripts/init_local.sh script for local DB bootstrap and running migrations

## 4. Monitoring and Observability
- [x] Install prometheus-fastapi-instrumentator in backend
- [x] Add /metrics endpoint to backend/main.py
- [x] Add /metrics endpoint to agent/core/monitoring.py (or create new metrics module)
- [x] Create infra/grafana-dashboard.json with example dashboard
- [x] Create infra/prometheus-alerts.yml with example alert rules

## 5. Security Enhancements
- [x] Install slowapi in backend
- [x] Add rate limiting middleware to backend/main.py
- [x] Update backend/services/video_service.py to generate signed URLs for S3 uploads

## 6. Orchestration and Deployment
- [ ] Create infra/k8s/ directory
- [ ] Create infra/k8s/namespace.yaml
- [ ] Create infra/k8s/backend-deployment.yaml
- [ ] Create infra/k8s/frontend-deployment.yaml
- [ ] Create infra/k8s/agent-deployment.yaml
- [ ] Create infra/k8s/services.yaml (for backend, frontend, agent)
- [ ] Create infra/k8s/ingress.yaml
- [ ] Create infra/k8s/secrets.yaml
- [ ] Create infra/k8s/configmaps.yaml
- [ ] Create infra/k8s/hpa.yaml (Horizontal Pod Autoscaler)
- [ ] Create .github/workflows/ci-cd.yml for linting, testing, building, pushing images, deploying to staging

## 7. Testing Improvements
- [ ] Add more unit tests in backend/tests/ (e.g., for routes, services)
- [ ] Add integration tests in backend/tests/
- [ ] Install Playwright in frontend
- [ ] Create frontend/e2e/ directory with basic E2E test stub

## 8. Documentation Updates
- [ ] Update README.md with one-click local startup instructions
- [ ] Add environment setup instructions to README.md
- [ ] Add architecture diagram to README.md
- [ ] Create RUNBOOK.md with deployment, backup, restore, migration, rollback steps

## Followup Steps After Implementation
- [ ] Install new dependencies: prometheus-fastapi-instrumentator, slowapi, alembic, playwright
- [ ] Test locally with docker-compose up --build
- [ ] Verify K8s manifests with kubectl apply --dry-run
- [ ] Run CI/CD pipeline on push
- [ ] Test metrics endpoints with curl localhost:8000/metrics
