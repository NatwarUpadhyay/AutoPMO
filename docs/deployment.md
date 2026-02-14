# Deployment Guide
## Production Deployment Instructions for AutoPMO

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [OpenShift Deployment](#openshift-deployment)
4. [Configuration](#configuration)
5. [Security Hardening](#security-hardening)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### System Requirements
- **OpenShift**: 4.12 or later
- **CPU**: Minimum 32 cores across cluster
- **Memory**: Minimum 64GB RAM
- **Storage**: 500GB persistent storage

### Access Requirements
- OpenShift cluster admin access
- Red Hat SSO administrator access
- Container registry credentials (Quay.io)
- AWS/Cloud provider credentials (for ML models)

### Tools Required
```bash
# Install required CLI tools
oc version  # OpenShift CLI >= 4.12
helm version  # Helm >= 3.10
kubectl version  # Kubernetes CLI >= 1.25
terraform version  # Terraform >= 1.6
```

---

## 2. Quick Start

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/NatwarUpadhyay/AutoPMO.git
cd AutoPMO

# Run automated deployment
./scripts/deploy.sh --environment production \
  --openshift-url https://api.cluster.example.com:6443 \
  --registry quay.io/autopmo
```

This script will:
1. Validate prerequisites
2. Create OpenShift namespace
3. Deploy Red Hat SSO (Keycloak)
4. Deploy PostgreSQL database
5. Deploy Redis message queue
6. Deploy ML models to OpenShift AI
7. Deploy agent services
8. Configure networking and security
9. Run smoke tests

**Estimated Time**: 30-45 minutes

---

## 3. OpenShift Deployment

### Step-by-Step Manual Deployment

#### 3.1 Create Namespace

```bash
oc new-project autopmo --display-name="AutoPMO AI Platform"
```

#### 3.2 Create Service Account

```yaml
# sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: autopmo-sa
  namespace: autopmo

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: autopmo-role
  namespace: autopmo
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "jobs", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: autopmo-rolebinding
  namespace: autopmo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: autopmo-role
subjects:
- kind: ServiceAccount
  name: autopmo-sa
  namespace: autopmo
```

```bash
oc apply -f sa.yaml
```

#### 3.3 Deploy Database (PostgreSQL)

```bash
# Using OpenShift Templates
oc new-app postgresql-persistent \
  -p DATABASE_SERVICE_NAME=autopmo-db \
  -p POSTGRESQL_USER=autopmo \
  -p POSTGRESQL_PASSWORD=<secure-password> \
  -p POSTGRESQL_DATABASE=autopmo \
  -p VOLUME_CAPACITY=50Gi

# Initialize schema
oc exec -it autopmo-db-1-xxxxx -- psql -U autopmo -d autopmo < schema.sql
```

#### 3.4 Deploy Redis

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install autopmo-redis bitnami/redis \
  --namespace autopmo \
  --set auth.password=<secure-password> \
  --set master.persistence.size=10Gi \
  --set replica.replicaCount=2
```

#### 3.5 Deploy Keycloak (Red Hat SSO)

```bash
# Deploy Keycloak Operator
oc apply -f https://operatorhub.io/install/keycloak-operator.yaml

# Create Keycloak instance
cat <<EOF | oc apply -f -
apiVersion: keycloak.org/v1alpha1
kind: Keycloak
metadata:
  name: autopmo-sso
  namespace: autopmo
spec:
  instances: 2
  externalAccess:
    enabled: true
EOF

# Import realm configuration
oc exec -it keycloak-0 -- /opt/jboss/keycloak/bin/kcadm.sh create realms \
  -s realm=autopmo -s enabled=true -f /config/realm-export.json
```

#### 3.6 Deploy ML Models (OpenShift AI)

```bash
# Deploy KServe
oc apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve.yaml

# Deploy Risk Predictor Model
cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: risk-predictor
  namespace: autopmo
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://autopmo-models/risk-predictor/v1.0
      resources:
        requests:
          cpu: "1"
          memory: 2Gi
        limits:
          cpu: "2"
          memory: 4Gi
EOF
```

#### 3.7 Deploy Agents

```bash
# Deploy Orchestrator
oc apply -f deployments/orchestrator-deployment.yaml

# Deploy Specialized Agents
for agent in planning risk infrastructure communications audit; do
  oc apply -f deployments/${agent}-agent-deployment.yaml
done

# Wait for deployments
oc rollout status deployment/orchestrator-agent -n autopmo
```

#### 3.8 Create Routes

```bash
# Expose services
oc expose svc orchestrator-service --hostname=autopmo.apps.cluster.example.com
oc expose svc keycloak --hostname=sso.autopmo.apps.cluster.example.com

# Enable TLS
oc patch route orchestrator-service -p '{"spec":{"tls":{"termination":"edge"}}}'
```

---

## 4. Configuration

### 4.1 Environment Variables

Create ConfigMap for application configuration:

```yaml
# config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: autopmo-config
  namespace: autopmo
data:
  DATABASE_URL: "postgresql://autopmo:password@autopmo-db:5432/autopmo"
  REDIS_URL: "redis://autopmo-redis-master:6379/0"
  KEYCLOAK_URL: "https://sso.autopmo.apps.cluster.example.com"
  KEYCLOAK_REALM: "autopmo"
  MISTRAL_API_ENDPOINT: "http://mistral-llm:8080/v1"
  RISK_PREDICTOR_ENDPOINT: "http://risk-predictor.autopmo.svc.cluster.local/v1/models/risk-predictor:predict"
  LOG_LEVEL: "INFO"
  AGENT_TIMEOUT: "300"
  MAX_CONCURRENT_TASKS: "10"
```

### 4.2 Secrets Management

```bash
# Create secrets
oc create secret generic autopmo-secrets \
  --from-literal=db-password=<db-password> \
  --from-literal=redis-password=<redis-password> \
  --from-literal=mistral-api-key=<mistral-key> \
  --from-literal=jwt-secret=<jwt-secret> \
  -n autopmo

# Alternatively, use HashiCorp Vault
oc apply -f vault/vault-deployment.yaml
```

### 4.3 Network Policies

```bash
# Apply network policies for security
oc apply -f network-policies/default-deny.yaml
oc apply -f network-policies/allow-orchestrator.yaml
oc apply -f network-policies/allow-database.yaml
```

---

## 5. Security Hardening

### 5.1 SELinux Policies

```bash
# Apply custom SELinux policies
oc apply -f selinux/autopmo-policies.yaml

# Verify policies
oc exec -it orchestrator-agent-xxxxx -- sestatus
```

### 5.2 Pod Security Standards

```yaml
# pss.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: autopmo
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 5.3 Service Mesh (Istio)

```bash
# Install Istio Operator
oc apply -f https://istio.io/latest/docs/setup/install/operator/deploy/istio-operator.yaml

# Create Istio instance
oc apply -f istio/istio-controlplane.yaml

# Enable mTLS
oc apply -f istio/peer-authentication.yaml
```

---

## 6. Monitoring Setup

### 6.1 Prometheus & Grafana

```bash
# Deploy Prometheus Operator
oc apply -f monitoring/prometheus-operator.yaml

# Deploy ServiceMonitors
oc apply -f monitoring/servicemonitors/

# Deploy Grafana
helm install autopmo-grafana grafana/grafana \
  --namespace autopmo \
  --values monitoring/grafana-values.yaml

# Import dashboards
oc exec -it grafana-xxxxx -- grafana-cli admin reset-admin-password <new-password>
# Then import dashboards from monitoring/dashboards/
```

### 6.2 EFK Stack (Logging)

```bash
# Deploy Elasticsearch
oc apply -f logging/elasticsearch-deployment.yaml

# Deploy Fluentd
oc apply -f logging/fluentd-daemonset.yaml

# Deploy Kibana
oc apply -f logging/kibana-deployment.yaml

# Create index patterns
curl -X POST "http://kibana:5601/api/saved_objects/index-pattern/autopmo-logs" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{"attributes":{"title":"autopmo-*","timeFieldName":"@timestamp"}}'
```

### 6.3 Alerting

```yaml
# alerting-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
  namespace: autopmo
data:
  alerts.yaml: |
    groups:
    - name: autopmo
      interval: 30s
      rules:
      - alert: HighErrorRate
        expr: rate(autopmo_requests_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: AgentDown
        expr: up{job="autopmo-agents"} == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.instance }} is down"
```

---

## 7. Troubleshooting

### 7.1 Common Issues

#### Issue: Pods not starting

```bash
# Check pod status
oc get pods -n autopmo

# View pod events
oc describe pod <pod-name> -n autopmo

# Check logs
oc logs <pod-name> -n autopmo --tail=100

# Common causes:
# - ImagePullBackOff: Check registry credentials
# - CrashLoopBackOff: Check application logs
# - Pending: Check resource quotas and node capacity
```

#### Issue: Database connection failures

```bash
# Test database connectivity
oc exec -it orchestrator-agent-xxxxx -- nc -zv autopmo-db 5432

# Check database logs
oc logs autopmo-db-1-xxxxx

# Verify secrets
oc get secret autopmo-secrets -o yaml

# Test connection manually
oc exec -it orchestrator-agent-xxxxx -- psql \
  -h autopmo-db -U autopmo -d autopmo -c "SELECT 1"
```

#### Issue: ML model inference failures

```bash
# Check model service status
oc get inferenceservice -n autopmo

# Test model endpoint
curl -X POST http://risk-predictor.autopmo.svc.cluster.local/v1/models/risk-predictor:predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"feature1": 0.5, "feature2": 1.2}]}'

# View KServe logs
oc logs -l serving.kserve.io/inferenceservice=risk-predictor -n autopmo
```

### 7.2 Health Checks

```bash
# Run comprehensive health check
./scripts/health-check.sh

# Sample output:
✅ OpenShift Cluster: Healthy
✅ Namespace: autopmo exists
✅ Database: PostgreSQL reachable
✅ Cache: Redis reachable
✅ SSO: Keycloak reachable
✅ Orchestrator: 3/3 pods running
✅ Planning Agent: 2/2 pods running
✅ Risk Agent: 2/2 pods running
✅ Infrastructure Agent: 2/2 pods running
✅ Communications Agent: 2/2 pods running
✅ Audit Agent: 2/2 pods running
✅ ML Models: 4/4 models serving
✅ Monitoring: Prometheus operational
✅ Logging: EFK stack operational
```

### 7.3 Performance Tuning

```bash
# Adjust resource limits based on load
oc set resources deployment orchestrator-agent \
  --requests=cpu=1,memory=2Gi \
  --limits=cpu=2,memory=4Gi

# Scale horizontally
oc scale deployment orchestrator-agent --replicas=5

# Enable autoscaling
oc autoscale deployment orchestrator-agent \
  --min=3 --max=10 --cpu-percent=70
```

---

## Deployment Checklist

Pre-Deployment:
- [ ] OpenShift cluster provisioned and accessible
- [ ] Required CLI tools installed
- [ ] Container images built and pushed to registry
- [ ] Secrets prepared (DB passwords, API keys, certificates)
- [ ] Network policies reviewed and approved
- [ ] Monitoring infrastructure ready

Deployment:
- [ ] Namespace created
- [ ] Database deployed and initialized
- [ ] Redis deployed
- [ ] Keycloak deployed and configured
- [ ] ML models deployed to OpenShift AI
- [ ] Agent services deployed
- [ ] Routes created and TLS configured
- [ ] Network policies applied

Post-Deployment:
- [ ] Smoke tests passed
- [ ] Health checks passing
- [ ] Monitoring dashboards configured
- [ ] Alerting rules tested
- [ ] Documentation updated
- [ ] Team trained on operations

---

## Support

For deployment issues:
- GitHub Issues: https://github.com/NatwarUpadhyay/AutoPMO/issues
- Documentation: https://github.com/NatwarUpadhyay/AutoPMO/tree/main/docs
- Community Forum: https://discuss.autopmo.dev

---

**Version**: 1.0  
**Last Updated**: 2024-02-14  
**Maintainer**: AutoPMO DevOps Team
