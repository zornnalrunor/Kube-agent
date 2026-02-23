# 🤖 Terraform K8s Agent - GitOps Automation

Système agentique IA pour l'automatisation complète de clusters Kubernetes avec ArgoCD, monitoring (Prometheus/Grafana/Headlamp) et GitOps.

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Planner   │ => │ Infrastructure│ => │   ArgoCD    │ => │  Monitoring  │
│    Agent    │    │     Agent     │    │    Agent    │    │    Agent     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │   GitOps Pattern   │
                                    │  (Auto-sync Apps)  │
                                    └───────────────────┘
```

## ✨ Features

- 🚀 **Multi-plateforme**: K3s (local), EKS (AWS), AKS (Azure)
- 🔄 **GitOps**: ArgoCD gère tous les déploiements applicatifs
- 📊 **Monitoring**: Prometheus + Grafana + Headlamp (K8s UI)
- 🤖 **IA-Powered**: LLM (Ollama) pour la planification intelligente
- 🎯 **Multi-agents**: Architecture modulaire et extensible
- 📦 **Simple**: Un seul commande pour tout déployer
- 🧹 **Clean**: Script de nettoyage complet fourni

## 🏗️ Architecture

### Agents

| Agent | Rôle | Output |
|-------|------|--------|
| **Planner** | Analyse les besoins, planifie le déploiement | Configuration optimisée |
| **Infrastructure** | Provisionne K3s avec Terraform | Cluster K8s + kubeconfig |
| **ArgoCD** | Installe ArgoCD (GitOps) | ArgoCD opérationnel |
| **Monitoring** | Déploie le stack via ArgoCD | Prometheus/Grafana/Headlamp |
| **Validation** | Vérifie la santé du cluster | Rapport de santé + score |
| **Documentation** | Génère la doc technique | Runbooks + diagrammes |

### GitOps Flow

```
1. Infrastructure Agent  →  K3s cluster
2. ArgoCD Agent          →  ArgoCD installé
3. Monitoring Agent      →  Crée Git repo local + ArgoCD Applications
4. ArgoCD                →  Sync automatique des manifests
5. Validation Agent      →  Vérifie ArgoCD Apps (synced/healthy)
```

## 🚀 Quick Start

### Prérequis

```bash
# Python 3.14+
python --version

# Terraform v1.14+
terraform --version

# kubectl v1.35+
kubectl version --client

# Ollama (LLM local)
ollama --version
ollama pull llama3.2:1b
```

### Installation

```bash
cd Terraform-agent-eks-aks

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # ou .venv/bin/activate.fish

# Dépendances
pip install -r requirements-minimal.txt
```

### Utilisation

#### Mode Interactif (Recommandé)

```bash
python main.py interactive
```

Questions posées:
- Plateforme: K3s, EKS, AKS?
- Environnement: dev, staging, prod?
- Nœuds: combien?
- Monitoring: activer?
- Headlamp: activer (UI Kubernetes)?
- Mode: démo (simulation) ou réel?

#### Mode CLI

```bash
# Déploiement complet K3s avec tout
python main.py create \
  --platform k3s \
  --nodes 3 \
  --environment production \
  --monitoring \
  --headlamp \
  --real-deployment

# Démo rapide (simulation)
python main.py create -p k3s -n 1 --monitoring --headlamp
```

## 🎯 Modes de déploiement

### 📺 Mode Démo (par défaut)
- Simulation ultra-rapide (~10 secondes)
- Aucune installation réelle
- Parfait pour tester le workflow

### 🚀 Mode Réel
- Installation complète de K3s
- Déploiement ArgoCD + Monitoring
- Nécessite sudo pour K3s
- Durée: 2-5 minutes

```bash
# Activer le mode réel
python main.py create -p k3s -n 1 --monitoring --headlamp --real-deployment
```

## 🌐 Accès aux services

Après un déploiement réel:

| Service | URL | Credentials |
|---------|-----|-------------|
| **ArgoCD** | http://localhost:30080 | `admin` / voir commande ci-dessous |
| **Grafana** | http://localhost:30300 | `admin` / `admin` |
| **Prometheus** | http://localhost:30090 | - |
| **Headlamp** | http://localhost:30466 | In-cluster auth |

### Récupérer le mot de passe ArgoCD

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

## 🔧 Configuration

### Environnement

```bash
# Mode de déploiement (auto-détecté sinon)
export DEPLOYMENT_MODE=real  # ou demo

# LLM Configuration (optionnel)
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2:1b
```

### Fichier de config (avancé)

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

## 📁 Structure du projet

```
Terraform-agent-eks-aks/
├── agents/                    # Agents spécialisés
│   ├── planner_agent.py
│   ├── infrastructure_agent.py
│   ├── argocd_agent.py       # 🆕 GitOps
│   ├── monitoring_agent.py
│   ├── validation_agent.py
│   ├── documentation_agent.py
│   └── orchestrator_agent.py
├── core/                      # Core système
│   ├── agent_base.py
│   ├── config.py
│   ├── llm_provider.py
│   └── state_manager.py
├── output/                    # Fichiers générés
│   ├── terraform/             # Code Terraform
│   ├── kubeconfigs/           # Configs K8s
│   ├── manifests/             # Manifests K8s
│   ├── gitops/                # 🆕 Repos Git locaux
│   ├── argocd-apps/           # 🆕 Applications ArgoCD
│   └── docs/                  # Documentation
├── main.py                    # Point d'entrée CLI
├── cleanup.sh                 # Script de nettoyage
└── README.md                  # Ce fichier
```

## 🧹 Nettoyage

Pour supprimer complètement le cluster et tout nettoyer:

```bash
./cleanup.sh
```

Le script nettoie:
- ✅ Namespaces K8s (`monitoring`, `argocd`)
- ✅ K3s (désinstallation complète)
- ✅ Fichiers générés (`output/`, `data/`, `logs/`)
- ✅ Contextes k3s dans `~/.kube/config`
- ✅ États Terraform

## 🎓 Concepts

### GitOps avec ArgoCD

**Avant (kubectl apply direct):**
```
Agent → kubectl apply → Cluster
```
❌ Pas de source de vérité  
❌ Drift non détecté  
❌ Pas d'historique

**Après (GitOps + ArgoCD):**
```
Agent → Git repo → ArgoCD → Cluster
                      ↑
                   Reconcile
```
✅ Git = source de vérité  
✅ Self-heal automatique  
✅ Historique complet  
✅ Rollback facile

### App of Apps Pattern

ArgoCD peut se gérer lui-même + toutes les apps:

```
root-app (Bootstrap)
├── argocd-app           # ArgoCD s'auto-gère
├── monitoring-app       # Prometheus + Grafana + Headlamp
└── apps/
    ├── webapp-app       # Applications métier
    └── database-app
```

## 🐛 Troubleshooting

### K3s ne démarre pas

```bash
# Logs K3s
sudo journalctl -u k3s -f

# Réinstaller
sudo /usr/local/bin/k3s-uninstall.sh
curl -sfL https://get.k3s.io | sh -
```

### ArgoCD ne sync pas

```bash
# Vérifier l'Application
kubectl -n argocd get applications

# Forcer un sync
kubectl -n argocd get app monitoring-{workflow-id} -o yaml
```

### Pods en CrashLoop

```bash
# Logs détaillés
kubectl -n monitoring logs -l app=prometheus
kubectl -n monitoring describe pod {pod-name}

# Events du namespace
kubectl -n monitoring get events --sort-by='.lastTimestamp'
```

### Contextes k3s en double

```bash
# Lister
kubectl config get-contexts | grep k3s

# Supprimer manuellement
kubectl config delete-context k3s-{workflow-id}
```

## 🔒 Sécurité

⚠️ **Attention**: Ce projet est pour du développement/testing local.

Pour la production:
- [ ] Changer les mots de passe par défaut
- [ ] Utiliser des secrets externes (Vault, AWS Secrets Manager)
- [ ] Activer l'authentification RBAC
- [ ] Configurer Network Policies
- [ ] Activer mTLS (Istio/Linkerd)
- [ ] Mettre en place des PSP/PSA

## 📊 Métriques

Dashboards Grafana pré-configurés:
- Cluster Overview
- Node Exporter Full
- Prometheus Stats
- Pod Monitoring
- ArgoCD Metrics

## 🚧 Roadmap

- [ ] Support Istio (Service Mesh + Kiali)
- [ ] Support multi-clusters
- [ ] Applications Helm via ArgoCD
- [ ] Image Updater ArgoCD (CD complet)
- [ ] Support EKS/AKS (actuellement K3s only)
- [ ] Notifications (Slack, Discord)
- [ ] Backup/Restore avec Velero

## 🤝 Contrib

Contributions bienvenues! Le code est structuré en agents indépendants, facile d'en ajouter.

Architecture:
1. Créer un nouveau fichier agent dans `agents/`
2. Hériter de `BaseAgent`
3. Implémenter `execute()`
4. Enregistrer dans `orchestrator_agent.py`

## 📄 License

MIT

## 🙏 Credits

- **K3s**: Lightweight Kubernetes by Rancher
- **ArgoCD**: GitOps continuous delivery tool
- **Prometheus/Grafana**: Monitoring stack
- **Headlamp**: Kubernetes UI
- **Ollama**: Local LLM runtime
