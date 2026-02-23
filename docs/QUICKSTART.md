# Quick Start Guide

## 🚀 5-Minute Installation

### 1. Prerequisites

```bash
# Python 3.14+
python --version

# Terraform
terraform --version

# kubectl
kubectl version --client

# Git
git --version
```

### 2. Clone and Install

```bash
# Clone the repo (or extract if local file)
cd Terraform-agent-eks-aks

# Install dependencies
pip install -r requirements-minimal.txt
```

### 3. Configuration

```bash
# Copy example config
cp .env.example .env

# Edit config
nano .env
```

**Minimal configuration**:

```bash
# Choose an LLM provider
LLM_PROVIDER=ollama  # Free and local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Or OpenAI (paid but performant)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
```

If using Ollama:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download a model
ollama pull llama3.2:1b

# Verify it works
ollama list
```

### 4. First Test - Interactive Mode

```bash
python main.py interactive
```

Follow the prompts:
1. Choose **K3s** (option 1)
2. Environment **Development** (option 1)
3. **3 nodes**
4. **Enable monitoring** (Y)
5. **Enable Headlamp** (Y)
6. Confirm (Y)

🎉 The system will:
- Analyze your requirements
- Optimize the configuration
- Generate Terraform code
- Create the cluster (simulation for demo)
- Deploy ArgoCD + Prometheus + Grafana + Headlamp
- Validate the cluster
- Generate documentation

### 5. Result

You'll get:

```
✅ Deployment completed successfully!

Access:
  🔄 ArgoCD: http://localhost:30080 (admin/xxx)
  📊 Grafana: http://localhost:30300 (admin/admin)
  📈 Prometheus: http://localhost:30090
  🎛️  Headlamp: http://localhost:30466

Cluster:
  Nodes: 3/3
  Pods: 15/15
```

---

## 🎯 Common Use Cases

### Case 1: Quick Local Dev

**Objective**: Minimal K3s cluster for development

```bash
python main.py create \
  --platform k3s \
  --environment development \
  --nodes 1 \
  --no-monitoring
```

**Duration**: ~2 minutes

### Case 2: Dev with Full Stack

**Objective**: Complete cluster with monitoring and GitOps

```bash
python main.py create -p k3s -n 2 --monitoring --headlamp --real-deployment
```

**Duration**: ~5 minutes

### Case 3: Production EKS

**Objective**: Production AWS cluster with HA

**Prerequisites**:
```bash
# Configure AWS CLI
aws configure
```

**Command**:
```bash
python main.py --config examples/eks-prod.yaml --real-deployment
```

**Duration**: ~15-20 minutes

---

## 📊 Accessing Monitoring

### ArgoCD (GitOps UI)

```bash
# Get the URL from deployment output
open http://localhost:30080

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Login
Username: admin
Password: [from command above]
```

**Features**:
- View all Applications
- See sync status
- Manual sync/refresh
- Check Application health

### Grafana

```bash
# Access
open http://localhost:30300

# Default credentials
Username: admin
Password: admin
```

**Pre-configured dashboards**:
- Kubernetes Cluster Monitoring
- Node Exporter Full
- Prometheus Stats
- Pod Monitoring
- ArgoCD Metrics

### Prometheus

```bash
# Access
open http://localhost:30090

# Useful queries
up{}  # All targets
node_cpu_seconds_total  # CPU usage
node_memory_MemAvailable_bytes  # Available memory
argocd_app_info  # ArgoCD applications
```

### Headlamp (Kubernetes UI)

```bash
# Access
open http://localhost:30466

# In-cluster authentication (no login needed)
```

**Features**:
- Browse all Kubernetes resources
- View logs
- Edit resources
- Pod shell access

---

## 🔍 Verify the Cluster

### Via kubectl

```bash
# Get kubeconfig from generated docs
export KUBECONFIG=~/.kube/config

# Check nodes
kubectl get nodes

# Check all pods
kubectl get pods --all-namespaces

# Check monitoring
kubectl get pods -n monitoring

# Check ArgoCD
kubectl get pods -n argocd
kubectl get applications -n argocd
```

### Via Validation Script

```bash
# Get workflow ID from output
python main.py status k3s-development-xxxxx
```

---

## 📚 Explore Documentation

Each deployment generates complete documentation:

```bash
cd output/docs/k3s-development-xxxxx/

# Read the README
cat README.md

# Architecture
cat ARCHITECTURE.md

# Operational runbook
cat RUNBOOK.md

# Troubleshooting guide
cat TROUBLESHOOTING.md
```

---

## 🔧 Advanced CLI Mode

### Create a Cluster

```bash
python main.py create \
  --platform k3s \
  --environment production \
  --nodes 5 \
  --monitoring \
  --headlamp \
  --real-deployment \
  --region us-east-1  # for EKS/AKS
```

### Check Status

```bash
# List workflows
python main.py list-workflows

# Workflow details
python main.py status <workflow-id>
```

### Destroy a Cluster

```bash
# Complete cleanup
./cleanup.sh
```

---

## 🐛 Quick Troubleshooting

### Problem: Import errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements-minimal.txt
```

### Problem: LLM timeout

```bash
# If using Ollama
# Check the service
systemctl status ollama

# Restart
ollama serve

# If using OpenAI
# Check API key
echo $OPENAI_API_KEY
```

### Problem: Terraform errors

```bash
# Check Terraform
terraform --version

# Reinstall if needed
# Linux
wget https://releases.hashicorp.com/terraform/1.14.5/terraform_1.14.5_linux_amd64.zip
unzip terraform_1.14.5_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Problem: Ports already in use

If ports 30080 (ArgoCD), 30300 (Grafana), or 30090 (Prometheus) are occupied:

```bash
# Identify the process
sudo lsof -i :30080
sudo lsof -i :30300

# Kill if necessary
sudo kill -9 <PID>
```

### Problem: ArgoCD not syncing

```bash
# Check Application status
kubectl -n argocd get applications

# Check ArgoCD logs
kubectl -n argocd logs -l app.kubernetes.io/name=argocd-server

# Force sync
kubectl -n argocd patch app monitoring-xxx \
  --type merge -p '{"operation":{"sync":{}}}'
```

---

## 🎓 Next Steps

### 1. Understand the Architecture

Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand:
- The multi-agent system
- Execution workflow
- State management
- GitOps patterns

### 2. Customize Configuration

Read [CONFIGURATION.md](CONFIGURATION.md) for:
- Adapting to specific needs
- Advanced monitoring configuration
- Managing secrets
- Platform-specific settings

### 3. Understand the Agents

Read [AGENTS.md](AGENTS.md) for:
- Details on each agent
- Extending the system
- Adding custom agents

### 4. Deploy to Production

```bash
# 1. Configure cloud credentials
# AWS
aws configure

# 2. Adapt production config
cp examples/eks-prod.yaml my-prod-config.yaml
nano my-prod-config.yaml

# 3. Deploy
python main.py --config my-prod-config.yaml --real-deployment

# 4. Verify
kubectl get nodes
kubectl get applications -n argocd
```

---

## 💡 Tips & Best Practices

### 1. Naming Convention

```yaml
# Use descriptive names
cluster_name: myapp-prod-eu-west-1
```

### 2. Tags

```yaml
tags:
  Environment: production
  Project: myapp
  ManagedBy: terraform-k8s-agent
  CostCenter: engineering
```

### 3. Monitoring

Always enable monitoring, even in dev:

```yaml
monitoring:
  enabled: true
  headlamp: true
```

### 4. GitOps

ArgoCD automatically manages your applications:
- Self-healing enabled
- Auto-sync on changes
- Complete audit trail

### 5. Documentation

Documentation is auto-generated. Share with team:

```bash
# Generate and commit
git add output/docs/
git commit -m "Add cluster documentation"
```

### 6. Cleanup

Always use the cleanup script:

```bash
./cleanup.sh
```

This ensures:
- K3s uninstalled properly
- Namespaces deleted
- k3s contexts removed
- Generated files cleaned

---

## 📞 Support

### Documentation

- [README.md](../README.md) - Overview
- [GITOPS.md](../GITOPS.md) - GitOps architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture
- [AGENTS.md](AGENTS.md) - Agent documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration options

### Debug Mode

```bash
# Enable detailed logs
DEBUG=true python main.py ...

# Terraform logs
TF_LOG=DEBUG python main.py ...
```

### System State

```bash
# Check state database
sqlite3 ./data/state.db

# List workflows
SELECT workflow_id, status, platform FROM workflows;

# List agent executions
SELECT agent_name, status FROM agent_executions WHERE workflow_id='xxx';
```

---

**You're ready!** 🚀

Start with interactive mode and explore features progressively.
