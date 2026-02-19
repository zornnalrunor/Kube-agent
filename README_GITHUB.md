# 🤖 Terraform-Agent-EKS-AKS

> **AI-Powered Multi-Agent System for Kubernetes Cluster Automation**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Terraform](https://img.shields.io/badge/terraform-1.0+-purple.svg)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

An intelligent, **agentic AI system** that fully automates Kubernetes cluster creation with integrated monitoring (Prometheus/Grafana). Supports K3s (local), AWS EKS, and Azure AKS with **LLM-powered optimization**.

## ✨ Features

- 🤖 **6 Specialized AI Agents** working in orchestrated harmony
- 🧠 **LLM Integration** (OpenAI, Anthropic, Ollama) for intelligent configuration optimization
- 🚀 **Two Modes**: Demo (simulation) or Real (actual deployment)
- 📊 **Built-in Monitoring**: Prometheus + Grafana with pre-configured dashboards
- 🎯 **Multi-Platform**: K3s, AWS EKS, Azure AKS
- 📝 **Auto-Documentation**: Generates runbooks, architecture diagrams, and troubleshooting guides
- ✅ **Health Validation**: Automated cluster health checks with scoring
- 🎨 **Interactive CLI**: Beautiful terminal UI with Rich

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                        │
│              (Workflow Coordination)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼────┐  ┌─────▼──────┐
│  Planner  │  │ Infra   │  │ Monitoring │
│  Agent    │  │ Agent   │  │  Agent     │
│           │  │         │  │            │
│ AI-Powered│  │Terraform│  │Prometheus/ │
│ Config    │  │ K3s/EKS │  │Grafana     │
└───────────┘  └─────────┘  └────────────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼────────┐ ┌──▼──────────┐   │
│ Validation   │ │Documentation│   │
│   Agent      │ │   Agent     │   │
│              │ │             │   │
│Health Checks │ │Auto Docs    │   │
│& Scoring     │ │& Diagrams   │   │
└──────────────┘ └─────────────┘   │
                                    │
              State Manager (SQLAlchemy)
```

## 🎯 Multi-Agent System

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Planner** | Configuration Optimization | Uses LLM to analyze requirements and optimize cluster configuration based on best practices |
| **Infrastructure** | Resource Provisioning | Generates and applies Terraform code for K3s, EKS, or AKS clusters |
| **Monitoring** | Observability Setup | Deploys Prometheus Operator and Grafana with 5 pre-configured dashboards |
| **Validation** | Health Verification | Runs comprehensive checks and generates 0-100 health score |
| **Documentation** | Knowledge Generation | Auto-generates README, architecture docs, runbooks, and troubleshooting guides |
| **Orchestrator** | Workflow Coordination | Manages agent execution, handles failures, and ensures proper sequencing |

## 🚀 Quick Start

### Prerequisites

```bash
# Required
python >= 3.11
terraform >= 1.0
kubectl >= 1.28

# Optional (for real deployments)
docker or containerd
```

### Installation

```bash
# Clone the repository
git clone https://github.com/YourUsername/Terraform-agent-eks-aks.git
cd Terraform-agent-eks-aks

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure LLM provider (choose one)
cp .env.example .env
# Edit .env with your API keys or use Ollama (local, free)
```

### 30-Second Demo

```bash
# Quick demo (simulation mode)
python main.py create -p k3s -n 3

# Or interactive mode
python main.py interactive
```

### Real Deployment

```bash
# Install Ollama (local LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve  # In another terminal
ollama pull llama3.2:1b

# Deploy real K3s cluster
python main.py create --platform k3s --nodes 1 --real-deployment

# Check your cluster
kubectl get nodes
kubectl get pods --all-namespaces
```

## 📺 Demo vs Real Mode

### Demo Mode (Default)
- ⚡ Ultra-fast (2-3 seconds)
- 🎭 Simulates deployments
- ✅ Perfect for testing architecture
- 💡 No system modifications

```bash
python main.py create -p k3s -n 3
```

### Real Mode
- ⏱️ Takes 2-5 minutes
- 🔧 Actually installs K3s
- 📊 Deploys real Prometheus/Grafana
- ✅ Production-ready

```bash
python main.py create -p k3s -n 1 --real-deployment
```

See [DEMO_VS_REAL.md](DEMO_VS_REAL.md) for detailed comparison.

## 🎨 Usage Examples

### CLI Mode

```bash
# K3s local cluster with monitoring
python main.py create \
  --platform k3s \
  --nodes 3 \
  --monitoring \
  --real-deployment

# AWS EKS production cluster
python main.py create \
  --platform eks \
  --nodes 5 \
  --region us-east-1 \
  --environment production \
  --monitoring \
  --real-deployment

# Azure AKS staging cluster
python main.py create \
  --platform aks \
  --nodes 3 \
  --region eastus \
  --environment staging
```

### Interactive Mode

```bash
python main.py interactive

# Guided questions:
# 1. Platform? (K3s/EKS/AKS)
# 2. Environment? (dev/staging/prod)
# 3. How many nodes?
# 4. Enable monitoring?
# 5. Demo or Real deployment?
```

### Using Configuration File

```bash
python main.py create --config examples/k3s-local.yaml
```

## 🔧 Configuration

### LLM Providers

Configure in `.env`:

```bash
# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo-preview

# Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-sonnet-20240229

# Ollama (Local, Free)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

### State Management

```bash
# SQLite (default, local)
STATE_BACKEND=sqlite
STATE_DB_PATH=./data/state.db

# PostgreSQL (team/production)
STATE_BACKEND=postgresql
STATE_DB_URL=postgresql://user:pass@host:5432/dbname
```

## 📊 Monitoring Stack

Automatically deploys:

- **Prometheus Operator**: Metrics collection and storage
- **Grafana**: Visualization with 5 dashboards
  - Cluster Overview
  - Node Metrics
  - Pod Resources
  - Network Traffic
  - Storage Usage
- **Alertmanager**: Alert routing (production)

Access after deployment:
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

## 📚 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Architecture](docs/ARCHITECTURE.md) - System design and patterns
- [Agents Documentation](docs/AGENTS.md) - Detailed agent capabilities
- [Configuration Guide](docs/CONFIGURATION.md) - All configuration options
- [Demo vs Real](DEMO_VS_REAL.md) - Mode comparison
- [Contributing](CONTRIBUTING.md) - How to contribute

## 🧪 Testing

```bash
# Run system tests
python test_system.py

# Test both modes
./test_modes.sh

# Interactive demo
python demo_interactive.py
```

## 🛠️ Project Structure

```
Terraform-agent-eks-aks/
├── agents/                    # 6 specialized agents
│   ├── orchestrator_agent.py
│   ├── planner_agent.py
│   ├── infrastructure_agent.py
│   ├── monitoring_agent.py
│   ├── validation_agent.py
│   └── documentation_agent.py
├── core/                      # Core framework
│   ├── config.py             # Configuration management
│   ├── llm_provider.py       # LLM integrations
│   ├── state_manager.py      # State persistence
│   └── agent_base.py         # Base agent class
├── terraform/                 # Terraform modules
│   └── k3s/
├── examples/                  # Configuration examples
│   ├── k3s-local.yaml
│   ├── eks-prod.yaml
│   └── aks-dev.yaml
├── docs/                      # Documentation
└── main.py                    # CLI entry point
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain) and [CrewAI](https://github.com/joaomdmoura/crewAI)
- CLI powered by [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- Inspired by agentic AI patterns and DevOps automation

## 🔗 Related Projects

- [K3s](https://k3s.io/) - Lightweight Kubernetes
- [Prometheus Operator](https://prometheus-operator.dev/) - Kubernetes monitoring
- [Grafana](https://grafana.com/) - Observability platform

## 📧 Contact

- GitHub Issues: [Report a bug](https://github.com/YourUsername/Terraform-agent-eks-aks/issues)
- Discussions: [Ask questions](https://github.com/YourUsername/Terraform-agent-eks-aks/discussions)

---

Made with ❤️ by the community | ⭐ Star this repo if you find it useful!
