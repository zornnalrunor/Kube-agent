# Terraform Agent - Kubernetes Cluster Automation

## 🎯 Objectif

Système agentique IA pour l'automatisation complète de la création de clusters Kubernetes avec monitoring intégré (Prometheus/Grafana).

## 🏗️ Architecture Agentique

Ce projet utilise une architecture multi-agents orchestrée pour gérer l'ensemble du processus de provisioning et configuration :

### Agents Spécialisés

1. **Orchestrator Agent** (`orchestrator_agent.py`)
   - Coordonne l'exécution de tous les agents
   - Gère le workflow global
   - Maintient l'état du système

2. **Planner Agent** (`planner_agent.py`)
   - Analyse les requirements utilisateur
   - Génère un plan d'exécution détaillé
   - Détermine les ressources nécessaires
   - Choisit la plateforme (K3s/EKS/AKS)

3. **Infrastructure Agent** (`infrastructure_agent.py`)
   - Génère et applique le code Terraform
   - Provisionne le cluster Kubernetes
   - Gère les providers cloud (AWS/Azure/local)
   - Configure le réseau et la sécurité

4. **Monitoring Agent** (`monitoring_agent.py`)
   - Déploie Prometheus Operator
   - Configure Grafana avec dashboards
   - Met en place les alertes
   - Configure les ServiceMonitors

5. **Validation Agent** (`validation_agent.py`)
   - Vérifie la santé du cluster
   - Teste les endpoints
   - Valide le monitoring
   - Génère un rapport de statut

6. **Documentation Agent** (`documentation_agent.py`)
   - Génère la documentation technique
   - Crée les runbooks
   - Documente l'architecture déployée
   - Génère les diagrammes

## 🚀 Quick Start

### Prérequis

```bash
# Python 3.11+
python --version

# Terraform
terraform --version

# kubectl
kubectl version --client

# Optionnel: Docker (pour K3s local)
docker --version
```

### Installation

```bash
# Cloner et installer les dépendances
cd Terraform-agent-eks-aks
pip install -r requirements.txt

# Configurer les credentials (pour EKS/AKS)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
# ou
az login
```

### Utilisation

#### Mode Interactif

```bash
python main.py
```

L'orchestrateur IA vous guidera à travers les questions pour :
- Choisir la plateforme (K3s/EKS/AKS)
- Définir la taille du cluster
- Configurer le monitoring
- Sélectionner les options avancées

#### Mode Configuration

```bash
# Utiliser un fichier de configuration
python main.py --config examples/k3s-local.yaml

# Exemples fournis
python main.py --config examples/eks-prod.yaml
python main.py --config examples/aks-dev.yaml
```

#### Mode CLI Direct

```bash
# Créer un cluster K3s local
python main.py create --platform k3s --nodes 3 --monitoring true

# Créer un cluster EKS
python main.py create --platform eks --region us-east-1 --nodes 3 --instance-type t3.medium

# Détruire un cluster
python main.py destroy --cluster-id my-cluster
```

## 📁 Structure du Projet

```
.
├── main.py                      # Point d'entrée principal
├── requirements.txt             # Dépendances Python
├── pyproject.toml              # Configuration Poetry
├── README.md
│
├── agents/                      # Système multi-agents
│   ├── __init__.py
│   ├── orchestrator_agent.py   # Chef d'orchestre
│   ├── planner_agent.py        # Planification
│   ├── infrastructure_agent.py # Provisioning
│   ├── monitoring_agent.py     # Monitoring
│   ├── validation_agent.py     # Validation
│   └── documentation_agent.py  # Documentation
│
├── core/                        # Core framework
│   ├── __init__.py
│   ├── agent_base.py           # Classe de base pour agents
│   ├── state_manager.py        # Gestion d'état
│   ├── llm_provider.py         # Interface LLM (OpenAI/Anthropic/Ollama)
│   └── config.py               # Configuration globale
│
├── terraform/                   # Modules Terraform
│   ├── k3s/                    # Module K3s (local/VMs)
│   ├── eks/                    # Module AWS EKS
│   ├── aks/                    # Module Azure AKS
│   └── modules/                # Modules réutilisables
│       ├── monitoring/         # Stack Prometheus/Grafana
│       ├── ingress/            # Ingress controllers
│       └── storage/            # Storage classes
│
├── kubernetes/                  # Manifests K8s
│   ├── monitoring/             # Prometheus/Grafana
│   ├── dashboards/             # Grafana dashboards
│   └── alerts/                 # Alerting rules
│
├── examples/                    # Configurations d'exemple
│   ├── k3s-local.yaml
│   ├── eks-prod.yaml
│   └── aks-dev.yaml
│
├── tests/                       # Tests
│   ├── test_agents.py
│   ├── test_infrastructure.py
│   └── test_integration.py
│
└── docs/                        # Documentation
    ├── ARCHITECTURE.md
    ├── AGENTS.md
    ├── CONFIGURATION.md
    └── TROUBLESHOOTING.md
```

## 🤖 Comment ça Marche ?

### Workflow Agentique

```
1. User Input → Orchestrator Agent
        ↓
2. Orchestrator → Planner Agent
        ↓ (Plan d'exécution)
3. Orchestrator → Infrastructure Agent
        ↓ (Terraform apply)
4. Orchestrator → Monitoring Agent
        ↓ (Deploy Prometheus/Grafana)
5. Orchestrator → Validation Agent
        ↓ (Health checks)
6. Orchestrator → Documentation Agent
        ↓ (Generate docs)
7. Return → Complete deployment report
```

### Communication Inter-Agents

Les agents communiquent via un **State Manager** centralisé qui :
- Maintient l'état global du workflow
- Permet les rollbacks en cas d'erreur
- Stocke les outputs de chaque agent
- Gère la persistance (SQLite/PostgreSQL)

### Intelligence Artificielle

Chaque agent utilise un LLM (configurable) pour :
- **Planner** : Optimiser le plan en fonction du contexte
- **Infrastructure** : Générer du Terraform idiomatique
- **Monitoring** : Configurer les alertes pertinentes
- **Validation** : Analyser les logs et diagnostiquer
- **Documentation** : Créer une doc contextuelle

LLM supportés :
- OpenAI GPT-4
- Anthropic Claude
- Ollama (local, gratuit)

## 🎨 Exemples d'Usage

### Exemple 1 : K3s Local pour Dev

```yaml
# examples/k3s-local.yaml
platform: k3s
environment: development
nodes: 3
resources:
  memory: 4Gi
  cpu: 2
monitoring:
  enabled: true
  retention: 7d
  dashboards:
    - kubernetes-cluster
    - node-exporter
```

```bash
python main.py --config examples/k3s-local.yaml
```

### Exemple 2 : EKS Production

```yaml
# examples/eks-prod.yaml
platform: eks
environment: production
region: eu-west-1
kubernetes_version: "1.28"
node_groups:
  - name: general
    instance_type: t3.large
    min_size: 3
    max_size: 10
    disk_size: 100
monitoring:
  enabled: true
  retention: 90d
  alerting: true
  slack_webhook: https://hooks.slack.com/...
```

### Exemple 3 : Mode Conversationnel IA

```bash
$ python main.py

🤖 Orchestrator Agent: Bonjour! Je vais vous aider à créer votre cluster Kubernetes.

? Quelle plateforme souhaitez-vous utiliser?
  1. K3s (local/VMs)
  2. AWS EKS
  3. Azure AKS
> 1

🤖 Planner Agent: Parfait! Pour K3s, combien de nœuds voulez-vous? (1-10)
> 3

🤖 Planner Agent: Voulez-vous activer le monitoring (Prometheus/Grafana)? (Y/n)
> Y

📋 Plan généré:
  ✓ Cluster K3s avec 3 nœuds
  ✓ Monitoring stack (Prometheus + Grafana)
  ✓ Dashboards pré-configurés
  ✓ Estimated time: ~5 minutes

? Confirmer le déploiement? (Y/n)
> Y

🔧 Infrastructure Agent: Génération du code Terraform...
✓ Terraform initialized
✓ Plan created (12 resources to add)

🚀 Infrastructure Agent: Application du plan...
✓ Cluster created (3/3 nodes ready)

📊 Monitoring Agent: Déploiement de la stack monitoring...
✓ Prometheus Operator deployed
✓ Grafana configured
✓ Dashboards imported (5)

✅ Validation Agent: Vérification du cluster...
✓ All nodes healthy
✓ Prometheus scraping (15 targets)
✓ Grafana accessible at http://localhost:3000

📚 Documentation Agent: Génération de la documentation...
✓ Architecture diagram created
✓ Runbook generated
✓ Configuration documented

🎉 Déploiement terminé!
📊 Grafana: http://localhost:3000 (admin/admin)
📈 Prometheus: http://localhost:9090
📝 Documentation: ./output/docs/
```

## 🔧 Configuration

### LLM Provider

```python
# .env ou core/config.py
LLM_PROVIDER=openai  # openai, anthropic, ollama
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_MODEL=llama2  # Pour usage local gratuit
```

### State Backend

```python
# Configuration du state manager
STATE_BACKEND=sqlite  # sqlite, postgresql, file
STATE_DB_PATH=./data/state.db
```

## 🧪 Tests

```bash
# Tests unitaires
pytest tests/test_agents.py

# Tests d'intégration
pytest tests/test_integration.py

# Test complet avec K3s local
./scripts/test-full-workflow.sh
```

## 📊 Monitoring Inclus

### Prometheus
- Metrics des nœuds (node-exporter)
- Metrics Kubernetes (kube-state-metrics)
- Metrics applicatives (ServiceMonitors)
- Alerting rules pré-configurées

### Grafana
- Dashboard : Kubernetes Cluster Monitoring
- Dashboard : Node Exporter Full
- Dashboard : Prometheus Stats
- Dashboard : Application Metrics
- Alerting intégré

## 🔒 Sécurité

- Secrets gérés via Terraform Vault ou Sealed Secrets
- RBAC configuré par défaut
- Network Policies
- Pod Security Standards

## 🤝 Contribution

Les contributions sont bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 License

MIT License - voir [LICENSE](LICENSE)

## 🆘 Support

- Documentation : [docs/](docs/)
- Issues : GitHub Issues
- Discussions : GitHub Discussions

## 🗺️ Roadmap

- [ ] Support GKE (Google Kubernetes Engine)
- [ ] Support pour Rancher
- [ ] UI Web pour le dashboard agent
- [ ] Plugin Terraform pour provider custom
- [ ] GitOps integration (ArgoCD/Flux)
- [ ] Cost optimization agent
- [ ] Security scanning agent
- [ ] Backup & disaster recovery agent

---

**Made with ❤️ and 🤖 AI Agents**
