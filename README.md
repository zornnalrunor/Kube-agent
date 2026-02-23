# 🤖 Terraform K8s Agent - AI-Powered GitOps Automation

Multi-agent AI system for complete Kubernetes cluster automation with ArgoCD, monitoring (Prometheus/Grafana/Headlamp), and GitOps workflow.

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Planner   │ => │Infrastructure│ => │   ArgoCD    │ => │  Monitoring  │
│    Agent    │    │     Agent     │    │    Agent    │    │    Agent     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │   GitOps Pattern   │
                                    │  (Auto-sync Apps)  │
                                    └───────────────────┘
```

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![K3s](https://img.shields.io/badge/K3s-v1.34+-green.svg)](https://k3s.io/)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-orange.svg)](https://argoproj.github.io/cd/)

## ✨ Features

- 🚀 **Multi-Platform**: K3s (local), EKS (AWS), AKS (Azure) - *currently K3s only*
- 🔄 **GitOps Ready**: ArgoCD manages all application deployments
- 📊 **Full Observability**: Prometheus + Grafana + Headlamp (K8s UI)
- 🤖 **AI-Powered**: LLM (Ollama) for intelligent planning and optimization
- 🎯 **Multi-Agent Architecture**: Modular, extensible agent system
- 📦 **One-Command Deploy**: Single command deploys everything
- 🧹 **Clean Reset**: Complete cleanup script included
- 🔐 **Secure by Design**: mTLS ready, RBAC enabled

## 🏗️ Architecture

### Agent System

| Agent | Role | Output |
|-------|------|--------|
| **Planner** | Analyzes requirements, plans deployment | Optimized configuration |
| **Infrastructure** | Provisions K3s cluster with Terraform | K8s cluster + kubeconfig |
| **ArgoCD** | Installs ArgoCD (GitOps engine) | ArgoCD operational |
| **Monitoring** | Deploys stack via ArgoCD | Prometheus/Grafana/Headlamp |
| **Validation** | Verifies cluster health | Health report + score |
| **Documentation** | Generates technical docs | Runbooks + diagrams |

### GitOps Workflow

```
1. Infrastructure Agent  →  K3s cluster running
2. ArgoCD Agent          →  ArgoCD installed
3. Monitoring Agent      →  Creates local Git repo + ArgoCD Applications
4. ArgoCD                →  Auto-syncs manifests to cluster
5. Validation Agent      →  Verifies ArgoCD Apps (synced/healthy)
```

**Benefits:**
- ✅ Git as single source of truth
- ✅ Automatic drift detection & self-healing
- ✅ Complete audit trail
- ✅ Easy rollbacks

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.14+
python --version

# Terraform v1.14+
terraform --version

# kubectl v1.35+
kubectl version --client

# Ollama (local LLM)
ollama --version
ollama pull llama3.2:1b
```

### Installation

```bash
cd Terraform-agent-eks-aks

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements-minimal.txt
```

### Usage

#### Interactive Mode (Recommended)

```bash
python main.py interactive
```

You'll be prompted for:
- Platform: K3s, EKS, or AKS?
- Environment: dev, staging, or production?
- Number of nodes
- Enable monitoring?
- Enable Headlamp (Kubernetes UI)?
- Deployment mode: demo (simulation) or real?

#### CLI Mode

```bash
# Full K3s deployment with everything
python main.py create \
  --platform k3s \
  --nodes 3 \
  --environment production \
  --monitoring \
  --headlamp \
  --real-deployment

# Quick demo (simulation - 10 seconds)
python main.py create -p k3s -n 1 --monitoring --headlamp
```

## 🎯 Deployment Modes

### 📺 Demo Mode (default)
- Ultra-fast simulation (~10 seconds)
- No actual installation
- Perfect for testing the workflow
- Shows what would happen in real mode

### 🚀 Real Mode
- Complete K3s installation
- ArgoCD + Monitoring stack deployment
- Requires sudo for K3s
- Duration: 2-5 minutes

```bash
# Enable real mode
python main.py create -p k3s -n 1 --monitoring --headlamp --real-deployment
```

## 🌐 Access Services

After a real deployment:

| Service | URL | Credentials |
|---------|-----|-------------|
| **ArgoCD** | http://localhost:30080 | `admin` / see command below |
| **Grafana** | http://localhost:30300 | `admin` / `admin` |
| **Prometheus** | http://localhost:30090 | - |
| **Headlamp** | http://localhost:30466 | In-cluster auth |

### Retrieve ArgoCD Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

## 🔧 Configuration

### Environment Variables

```bash
# Deployment mode (auto-detected otherwise)
export DEPLOYMENT_MODE=real  # or demo

# LLM Configuration (optional)
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2:1b
```

### Config File (Advanced)

```yaml
# config.yaml
platform: k3s
environment: production
nodes: 3
deployment_mode: real
monitoring:
  enabled: true
  headlamp: true
  retention: 30d
```

```bash
python main.py create --config config.yaml
```

## 📁 Project Structure

```
Terraform-agent-eks-aks/
├── agents/                     # Specialized agents
│   ├── planner_agent.py
│   ├── infrastructure_agent.py
│   ├── argocd_agent.py        # 🆕 GitOps engine
│   ├── monitoring_agent.py
│   ├── validation_agent.py
│   ├── documentation_agent.py
│   └── orchestrator_agent.py
├── core/                       # Core system
│   ├── agent_base.py
│   ├── config.py
│   ├── llm_provider.py
│   └── state_manager.py
├── output/                     # Generated files
│   ├── terraform/              # Terraform code
│   ├── kubeconfigs/            # K8s configs
│   ├── manifests/              # K8s manifests
│   ├── gitops/                 # 🆕 Local Git repos
│   ├── argocd-apps/            # 🆕 ArgoCD Applications
│   └── docs/                   # Documentation
├── main.py                     # CLI entry point
├── cleanup.sh                  # Cleanup script
└── README.md                   # This file
```

## 🧹 Cleanup

To completely remove the cluster and clean everything:

```bash
./cleanup.sh
```

The script cleans:
- ✅ Kubernetes namespaces (`monitoring`, `argocd`)
- ✅ K3s (complete uninstall)
- ✅ Generated files (`output/`, `data/`, `logs/`)
- ✅ k3s contexts in `~/.kube/config`
- ✅ Terraform states

## 🎓 Concepts

### GitOps with ArgoCD

**Before (kubectl apply):**
```
Agent → kubectl apply → Cluster
```
❌ No single source of truth  
❌ Drift undetected  
❌ No history

**After (GitOps + ArgoCD):**
```
Agent → Git repo → ArgoCD → Cluster
                      ↑
                 Auto-reconcile
```
✅ Git as source of truth  
✅ Automatic self-healing  
✅ Complete history  
✅ Easy rollbacks

### App of Apps Pattern

ArgoCD can manage itself + all applications:

```
root-app (Bootstrap)
├── argocd-app           # ArgoCD manages itself
├── monitoring-app       # Prometheus + Grafana + Headlamp
└── apps/
    ├── webapp-app       # Business applications
    └── database-app
```

## 🐛 Troubleshooting

### K3s Won't Start

```bash
# Check K3s logs
sudo journalctl -u k3s -f

# Reinstall
sudo /usr/local/bin/k3s-uninstall.sh
curl -sfL https://get.k3s.io | sh -
```

### ArgoCD Not Syncing

```bash
# Check Application status
kubectl -n argocd get applications

# Describe specific app
kubectl -n argocd get app monitoring-{workflow-id} -o yaml

# Force sync
kubectl -n argocd patch app monitoring-{workflow-id} \
  --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

### Pods in CrashLoopBackOff

```bash
# Detailed logs
kubectl -n monitoring logs -l app=prometheus --tail=100

# Describe pod
kubectl -n monitoring describe pod {pod-name}

# Check events
kubectl -n monitoring get events --sort-by='.lastTimestamp'
```

### Duplicate k3s Contexts

```bash
# List all contexts
kubectl config get-contexts | grep k3s

# Delete manually
kubectl config delete-context k3s-{workflow-id}

# Or use cleanup script
./cleanup.sh
```

## 🔒 Security

⚠️ **Warning**: This project is designed for development/testing environments.

For production use:
- [ ] Change default passwords
- [ ] Use external secrets (Vault, AWS Secrets Manager)
- [ ] Enable RBAC authentication
- [ ] Configure Network Policies
- [ ] Enable mTLS (Istio/Linkerd)
- [ ] Implement Pod Security Policies/Standards
- [ ] Use private container registries
- [ ] Enable audit logging
- [ ] Implement backup strategy

## 📊 Monitoring & Metrics

Pre-configured Grafana dashboards:
- **Cluster Overview**: Overall cluster health
- **Node Exporter Full**: Detailed node metrics
- **Prometheus Stats**: Prometheus self-monitoring
- **Pod Monitoring**: Per-pod resource usage
- **ArgoCD Metrics**: GitOps deployment insights

Access Grafana: http://localhost:30300 (admin/admin)

## 🚧 Roadmap

- [ ] **Istio Integration**: Service Mesh + Kiali UI
- [ ] **Multi-cluster Support**: Manage multiple clusters
- [ ] **Helm Charts**: Deploy Helm charts via ArgoCD
- [ ] **Image Updater**: Automatic CD with ArgoCD Image Updater
- [ ] **EKS/AKS Support**: Currently K3s only
- [ ] **Notifications**: Slack, Discord, email alerts
- [ ] **Backup/Restore**: Velero integration
- [ ] **Cost Optimization**: Resource recommendations
- [ ] **Security Scanning**: Trivy, Falco integration

## 🤝 Contributing

Contributions are welcome! The codebase is structured with independent agents, making it easy to add new ones.

**Adding a new agent:**
1. Create a new file in `agents/`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Register in `orchestrator_agent.py`
5. Add tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📚 Documentation

- 🇫🇷 [README en Français](README-french.md)
- 📖 [GitOps Architecture](GITOPS.md)
- 🏗️ [Project Structure](PROJECT_STRUCTURE.md)
- ⚡ [Demo vs Real Mode](DEMO_VS_REAL.md)
- 📝 [Implementation Summary](IMPLEMENTATION_SUMMARY.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[K3s](https://k3s.io/)**: Lightweight Kubernetes by Rancher
- **[ArgoCD](https://argoproj.github.io/cd/)**: Declarative GitOps CD for Kubernetes
- **[Prometheus](https://prometheus.io/)**: Monitoring system and time series database
- **[Grafana](https://grafana.com/)**: Analytics and monitoring platform
- **[Headlamp](https://headlamp.dev/)**: Kubernetes web UI
- **[Ollama](https://ollama.ai/)**: Local LLM runtime
- **[Terraform](https://www.terraform.io/)**: Infrastructure as Code

## 💬 Support

- 🐛 [Report a Bug](https://github.com/yourusername/terraform-agent-eks-aks/issues)
- 💡 [Request a Feature](https://github.com/yourusername/terraform-agent-eks-aks/issues)
- 📧 [Contact](mailto:your.email@example.com)

---

Made with ❤️ by the AI Agent Team
