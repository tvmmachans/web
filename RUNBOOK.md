# Runbook: AI Smart Social Media Manager

This runbook provides operational procedures for deploying, maintaining, and troubleshooting the AI Smart Social Media Manager application.

## Table of Contents

1. [Deployment](#deployment)
2. [Backup and Restore](#backup-and-restore)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Troubleshooting](#troubleshooting)
5. [Scaling](#scaling)
6. [Rollback Procedures](#rollback-procedures)
7. [Security Procedures](#security-procedures)

## Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- kubectl configured
- Helm (optional, for easier deployments)
- Docker registry access
- Domain name with DNS configured

### Initial Deployment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-smart-social-media-manager
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Build and push Docker images**:
   ```bash
   # Backend
   docker build -f Dockerfile.backend -t your-registry/backend:latest .
   docker push your-registry/backend:latest

   # Frontend
   docker build -f Dockerfile.frontend -t your-registry/frontend:latest .
   docker push your-registry/frontend:latest

   # Agent
   docker build -f Dockerfile.agent -t your-registry/agent:latest .
   docker push your-registry/agent:latest
   ```

4. **Deploy to Kubernetes**:
   ```bash
   # Create namespace
   kubectl apply -f infra/k8s/namespace.yaml

   # Create secrets (populate with actual values)
   kubectl apply -f infra/k8s/secrets.yaml

   # Create configmaps
   kubectl apply -f infra/k8s/configmaps.yaml

   # Deploy services
   kubectl apply -f infra/k8s/services.yaml

   # Deploy applications
   kubectl apply -f infra/k8s/backend-deployment.yaml
   kubectl apply -f infra/k8s/frontend-deployment.yaml
   kubectl apply -f infra/k8s/agent-deployment.yaml

   # Deploy ingress
   kubectl apply -f infra/k8s/ingress.yaml

   # Deploy HPA
   kubectl apply -f infra/k8s/hpa.yaml
   ```

5. **Verify deployment**:
   ```bash
   kubectl get pods -n social-media-automation
   kubectl get services -n social-media-automation
   kubectl get ingress -n social-media-automation
   ```

### Database Migration

After deployment, run database migrations:

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -n social-media-automation -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -n social-media-automation $BACKEND_POD -- alembic upgrade head
```

## Backup and Restore

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_$DATE.sql"

# Create backup
kubectl exec -n social-media-automation postgres-service -- pg_dump -U postgres -d social_media_db > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/database-backups/

# Clean up old backups (keep last 30 days)
aws s3 ls s3://your-backup-bucket/database-backups/ | while read -r line; do
    createDate=`echo $line|awk {'print $1" "$2'}`
    createDate=`date -d"$createDate" +%s`
    olderThan=`date -d'30 days ago' +%s`
    if [[ $createDate -lt $olderThan ]]; then
        fileName=`echo $line|awk {'print $4'}`
        if [[ $fileName != "" ]]; then
            aws s3 rm s3://your-backup-bucket/database-backups/$fileName
        fi
    fi
done
```

### Database Restore

```bash
# Restore from backup
BACKUP_FILE="backup_20231201_120000.sql"

# Download from S3
aws s3 cp s3://your-backup-bucket/database-backups/$BACKUP_FILE .

# Restore to database
kubectl exec -n social-media-automation postgres-service -- psql -U postgres -d social_media_db < $BACKUP_FILE
```

### File Storage Backup

MinIO/S3 data is automatically replicated. For additional backup:

```bash
# Sync MinIO data to backup bucket
mc mirror --overwrite local/your-bucket s3/your-backup-bucket/minio-backup/
```

## Monitoring and Alerting

### Health Checks

- **Backend**: `/health` endpoint returns `{"status": "healthy"}`
- **Frontend**: Nginx serves static files, check HTTP 200 response
- **Agent**: Check Celery worker status via `/metrics`

### Key Metrics to Monitor

- **Backend**:
  - Request latency (p95 should be <500ms)
  - Error rate (<1%)
  - Database connection pool usage
  - Rate limiting hits

- **Agent**:
  - Queue length (Redis)
  - Task success/failure rates
  - Memory usage

- **Infrastructure**:
  - Pod restarts
  - Resource utilization (CPU/Memory)
  - Network I/O

### Alerting Rules

Example PrometheusRule:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: social-media-alerts
  namespace: social-media-automation
spec:
  groups:
  - name: social-media
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
    - alert: PodRestarting
      expr: increase(kube_pod_container_status_restarts_total[10m]) > 0
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Pod is restarting frequently"
```

## Troubleshooting

### Common Issues

#### Backend Not Starting

```bash
# Check logs
kubectl logs -n social-media-automation -l app=backend --tail=100

# Check environment variables
kubectl exec -n social-media-automation -l app=backend -- env

# Check database connectivity
kubectl exec -n social-media-automation -l app=backend -- python -c "import psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])"
```

#### Agent Not Processing Tasks

```bash
# Check Redis connectivity
kubectl exec -n social-media-automation -l app=agent -- redis-cli -h redis-service ping

# Check Celery worker status
kubectl exec -n social-media-automation -l app=agent -- celery -A celery_app inspect active

# Check queue length
kubectl exec -n social-media-automation -l app=agent -- redis-cli -h redis-service LLEN celery
```

#### Frontend Not Loading

```bash
# Check ingress configuration
kubectl describe ingress -n social-media-automation

# Check service endpoints
kubectl get endpoints -n social-media-automation

# Check pod logs
kubectl logs -n social-media-automation -l app=frontend --tail=50
```

#### Database Connection Issues

```bash
# Check database pod status
kubectl get pods -n social-media-automation -l app=postgres

# Check database logs
kubectl logs -n social-media-automation -l app=postgres

# Test connection from backend pod
kubectl exec -n social-media-automation -l app=backend -- nc -zv postgres-service 5432
```

### Log Analysis

```bash
# View logs with timestamps
kubectl logs -n social-media-automation -l app=backend --timestamps

# Follow logs in real-time
kubectl logs -n social-media-automation -l app=backend -f

# Search for specific errors
kubectl logs -n social-media-automation -l app=backend | grep "ERROR"
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend deployment
kubectl scale deployment backend --replicas=5 -n social-media-automation

# Scale agent deployment
kubectl scale deployment agent --replicas=3 -n social-media-automation
```

### Vertical Scaling

Update resource requests/limits in deployment YAML:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Auto-scaling

The HPA is configured to scale based on CPU and memory usage. Adjust thresholds as needed:

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

## Rollback Procedures

### Application Rollback

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/backend -n social-media-automation

# Check rollout status
kubectl rollout status deployment/backend -n social-media-automation

# Rollback specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n social-media-automation
```

### Database Rollback

```bash
# List available migrations
kubectl exec -n social-media-automation -l app=backend -- alembic history

# Rollback to specific migration
kubectl exec -n social-media-automation -l app=backend -- alembic downgrade <revision-id>
```

### Full Environment Rollback

```bash
# Delete current deployments
kubectl delete -f infra/k8s/ -n social-media-automation

# Deploy previous version
kubectl apply -f infra/k8s/ -n social-media-automation

# Restore database from backup
# (Follow restore procedure above)
```

## Security Procedures

### Certificate Management

```bash
# Renew TLS certificates (if using cert-manager)
kubectl get certificate -n social-media-automation
kubectl describe certificate your-cert -n social-media-automation

# Manual certificate update
kubectl create secret tls your-tls-secret --cert=path/to/cert --key=path/to/key -n social-media-automation
```

### Secret Rotation

```bash
# Update secrets
kubectl create secret generic backend-secrets --from-literal=DATABASE_URL=new-url --dry-run=client -o yaml | kubectl apply -f -

# Restart affected pods
kubectl rollout restart deployment/backend -n social-media-automation
```

### Access Control

- Use RBAC for Kubernetes access
- Implement network policies
- Regular security scans with tools like Trivy
- Keep dependencies updated

### Incident Response

1. **Assess the situation**: Check monitoring dashboards and alerts
2. **Contain the issue**: Scale down affected services if needed
3. **Investigate**: Review logs and metrics
4. **Fix**: Deploy patch or rollback
5. **Learn**: Update runbook with new procedures

## Maintenance Tasks

### Weekly
- Review monitoring dashboards
- Check for security updates
- Verify backup integrity

### Monthly
- Update dependencies
- Review and rotate secrets
- Test disaster recovery procedures

### Quarterly
- Performance optimization
- Architecture review
- Update runbook procedures
