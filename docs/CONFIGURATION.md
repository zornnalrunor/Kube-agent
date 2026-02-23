# Configuration Guide

## 🎛️ Global Configuration

### .env File

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
nano .env
```

### LLM Provider

#### Option 1: OpenAI (Recommended for production)

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-your-key-here
```

**Pros**:
- High performance
- Reliable
- Multimodal

**Cons**:
- Cost per token
- Requires internet connection
- External dependency

#### Option 2: Anthropic Claude

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Pros**:
- Excellent analysis capabilities
- Good context (200K tokens)
- Security & privacy

#### Option 3: Ollama (Local/Free)

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**Pros**:
- Free
- Local (no external dependency)
- Total privacy

**Cons**:
- Requires GPU for good performance
- Variable quality by model
- Additional installation

**Ollama Installation**:

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2

# Start server (if not already running)
ollama serve
```

### State Management

#### Option 1: SQLite (Default)

```bash
STATE_BACKEND=sqlite
STATE_DB_PATH=./data/state.db
```

**Usage**: Dev, test, single-user

#### Option 2: PostgreSQL

```bash
STATE_BACKEND=postgresql
STATE_DB_URL=postgresql://user:password@localhost:5432/terraform_agent
```

**Usage**: Production, multi-instance, team

**PostgreSQL Setup**:

```bash
# Create database
createdb terraform_agent

# Create user
createuser terraform_agent_user -P

# Grant permissions
psql -d terraform_agent -c "GRANT ALL PRIVILEGES ON DATABASE terraform_agent TO terraform_agent_user;"
```

#### Option 3: File

```bash
STATE_BACKEND=file
```

Simple JSON file. **Usage**: Debug only.

---

## 📝 YAML File Configuration

### Structure

```yaml
# Platform (required)
platform: k3s  # k3s, eks, aks

# Environment (required)
environment: development  # development, staging, production

# Nodes
nodes: 3

# Resources per node
resources:
  memory: 4Gi
  cpu: 2
  disk_size: 50

# Networking
networking:
  pod_cidr: 10.244.0.0/16
  service_cidr: 10.96.0.0/16

# Monitoring
monitoring:
  enabled: true
  retention: 7d
  alerting: false
  dashboards:
    - kubernetes-cluster
    - node-exporter

# Security
security:
  rbac_enabled: true
  network_policies: false
  pod_security_policy: false

# Addons
addons:
  metrics_server: true
  ingress_nginx: true
  cert_manager: false
```

### Platform Examples

#### K3s (Local/Dev)

See [`examples/k3s-local.yaml`](../examples/k3s-local.yaml)

```yaml
platform: k3s
environment: development
nodes: 3

k3s_config:
  disable:
    - traefik  # Using nginx instead
  write_kubeconfig_mode: "644"
```

**Usage**:

```bash
python main.py --config examples/k3s-local.yaml
```

#### EKS (AWS Production)

See [`examples/eks-prod.yaml`](../examples/eks-prod.yaml)

```yaml
platform: eks
environment: production
region: eu-west-1

node_groups:
  - name: general
    instance_type: t3.large
    min_size: 3
    max_size: 10

eks_config:
  endpoint_private_access: true
  enabled_cluster_log_types:
    - api
    - audit
```

**Prerequisites**:

```bash
# AWS CLI configured
aws configure

# Or environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=eu-west-1
```

#### AKS (Azure)

See [`examples/aks-dev.yaml`](../examples/aks-dev.yaml)

```yaml
platform: aks
environment: development
location: eastus

node_pools:
  - name: default
    vm_size: Standard_B2ms
    node_count: 2
    enable_auto_scaling: true

aks_config:
  sku_tier: Free
  identity_type: SystemAssigned
```

**Prerequisites**:

```bash
# Azure CLI
az login

# Or environment variables
export ARM_CLIENT_ID=...
export ARM_CLIENT_SECRET=...
export ARM_SUBSCRIPTION_ID=...
export ARM_TENANT_ID=...
```

---

## ⚙️ Advanced Options

### Custom Monitoring

```yaml
monitoring:
  enabled: true
  retention: 30d
  
  # Alerting
  alerting: true
  slack_webhook: https://hooks.slack.com/services/XXX
  
  # Custom dashboards
  dashboards:
    - kubernetes-cluster
    - node-exporter
    - custom-app-metrics  # Your dashboard
  
  # Prometheus configuration
  prometheus:
    scrape_interval: 30s
    evaluation_interval: 30s
    
  # Grafana configuration
  grafana:
    admin_password: SecurePassword123!
    plugins:
      - grafana-piechart-panel
```

### Advanced Security

```yaml
security:
  # RBAC
  rbac_enabled: true
  
  # Network Policies
  network_policies: true
  default_deny_ingress: true
  default_deny_egress: false
  
  # Pod Security
  pod_security_policy: true
  pod_security_standards: restricted  # restricted, baseline, privileged
  
  # Secrets
  sealed_secrets: true
  external_secrets: false
  
  # Audit
  audit_logging: true
```

### Advanced Networking

```yaml
networking:
  # CIDRs
  pod_cidr: 10.244.0.0/16
  service_cidr: 10.96.0.0/16
  
  # CNI
  cni_plugin: calico  # flannel, calico, weave
  
  # Service Mesh (optional)
  service_mesh:
    enabled: true
    provider: istio  # istio, linkerd
  
  # Ingress
  ingress:
    controller: nginx  # nginx, traefik, haproxy
    class: nginx
    ssl:
      enabled: true
      cert_manager: true
```

### Storage

```yaml
storage:
  # Storage Classes
  classes:
    - name: fast
      provisioner: kubernetes.io/aws-ebs
      parameters:
        type: gp3
        iops: 3000
    
    - name: standard
      provisioner: kubernetes.io/aws-ebs
      parameters:
        type: gp2
  
  # Volume Snapshots
  snapshots:
    enabled: true
    retention: 7d
```

### Autoscaling

```yaml
autoscaling:
  # Cluster Autoscaler
  cluster_autoscaler:
    enabled: true
    min_nodes: 3
    max_nodes: 20
  
  # Horizontal Pod Autoscaler
  hpa:
    enabled: true
    
  # Vertical Pod Autoscaler
  vpa:
    enabled: false
```

---

## 🏷️ Tags & Labels

### Cloud Tags (EKS/AKS)

```yaml
tags:
  Environment: production
  ManagedBy: terraform-k8s-agent
  Project: my-project
  CostCenter: engineering
  Owner: platform-team
```

### Kubernetes Labels

```yaml
labels:
  app: my-application
  version: v1.0.0
  tier: backend
  environment: production
```

---

## 🔧 Agent Configuration

### Timeouts

```bash
# .env
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=3600  # seconds (1h)
```

### Verbosity

```bash
# .env
DEBUG=true  # Enable detailed logs
TF_LOG=DEBUG  # Detailed Terraform logs
```

---

## 📊 Monitoring Configuration

### Prometheus

Custom configuration via ConfigMap:

```yaml
monitoring:
  prometheus:
    config: |
      global:
        scrape_interval: 15s
      
      scrape_configs:
        - job_name: 'my-custom-job'
          static_configs:
            - targets: ['my-app:9090']
```

### Grafana

```yaml
monitoring:
  grafana:
    # Additional datasources
    datasources:
      - name: Loki
        type: loki
        url: http://loki:3100
    
    # Plugins
    plugins:
      - grafana-piechart-panel
      - grafana-worldmap-panel
    
    # Configuration
    config:
      auth.anonymous.enabled: true
      auth.anonymous.org_role: Viewer
```

### Alerting Rules

```yaml
monitoring:
  alerting: true
  
  # Custom alerting rules
  alert_rules:
    - name: HighMemoryUsage
      expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
      for: 5m
      severity: warning
      annotations:
        summary: "High memory usage detected"
```

---

## 🚀 Pre-configured Profiles

### "Quick Start" Profile

Minimal, fast, for testing:

```bash
python main.py create \
  --platform k3s \
  --nodes 1 \
  --monitoring false
```

### "Development" Profile

Local dev with monitoring:

```bash
python main.py --config examples/k3s-local.yaml
```

### "Production" Profile

HA, advanced monitoring, security:

```bash
python main.py --config examples/eks-prod.yaml
```

---

## 📁 Configuration Hierarchy

Priority order (highest to lowest):

1. **CLI Arguments**: `--nodes 5`
2. **YAML File**: `--config config.yaml`
3. **Environment Variables**: `.env`
4. **Default Values**: In code

Example:

```bash
# nodes=5 (CLI overrides YAML)
python main.py --config examples/k3s-local.yaml --nodes 5
```

---

## ✅ Configuration Validation

Before launching, validate your config:

```bash
# Dry-run (plan only, no apply)
DEBUG=true python main.py --config my-config.yaml
```

The Planner agent will validate and optimize the config.

---

## 🔍 Configuration Troubleshooting

### Issue: LLM not responding

```bash
# Check config
echo $OPENAI_API_KEY

# Test manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: Terraform errors

```bash
# Increase verbosity
export TF_LOG=DEBUG
python main.py ...
```

### Issue: State database locked

```bash
# SQLite
rm ./data/state.db-*

# PostgreSQL
psql -d terraform_agent -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='terraform_agent';"
```

---

**Next**: See main [README.md](../README.md) for use cases
