# Guide de Configuration

## 🎛️ Configuration Globale

### Fichier .env

Copiez `.env.example` vers `.env` et configurez :

```bash
cp .env.example .env
nano .env
```

### LLM Provider

#### Option 1 : OpenAI (Recommandé pour production)

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-your-key-here
```

**Avantages** :
- Très performant
- Fiable
- Multimodal

**Inconvénients** :
- Coût par token
- Nécessite connexion internet
- Dépendance externe

#### Option 2 : Anthropic Claude

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Avantages** :
- Excellentes capacités d'analyse
- Bon contexte (200K tokens)
- Sécurité & privacy

#### Option 3 : Ollama (Local/Gratuit)

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**Avantages** :
- Gratuit
- Local (pas de dépendance externe)
- Privacy totale

**Inconvénients** :
- Nécessite GPU pour de bonnes perfs
- Qualité variable selon le modèle
- Installation supplémentaire

**Installation Ollama** :

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Télécharger un modèle
ollama pull llama2

# Lancer le serveur (si pas déjà démarré)
ollama serve
```

### State Management

#### Option 1 : SQLite (Par défaut)

```bash
STATE_BACKEND=sqlite
STATE_DB_PATH=./data/state.db
```

**Usage** : Dev, test, single-user

#### Option 2 : PostgreSQL

```bash
STATE_BACKEND=postgresql
STATE_DB_URL=postgresql://user:password@localhost:5432/terraform_agent
```

**Usage** : Production, multi-instance, team

**Setup PostgreSQL** :

```bash
# Créer la base
createdb terraform_agent

# Créer l'utilisateur
createuser terraform_agent_user -P

# Grant permissions
psql -d terraform_agent -c "GRANT ALL PRIVILEGES ON DATABASE terraform_agent TO terraform_agent_user;"
```

#### Option 3 : File

```bash
STATE_BACKEND=file
```

Simple fichier JSON. **Usage** : Debug uniquement.

---

## 📝 Configuration par Fichier YAML

### Structure

```yaml
# Plateforme (obligatoire)
platform: k3s  # k3s, eks, aks

# Environnement (obligatoire)
environment: development  # development, staging, production

# Nœuds
nodes: 3

# Ressources par nœud
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

# Sécurité
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

### Exemples par Plateforme

#### K3s (Local/Dev)

Voir [`examples/k3s-local.yaml`](../examples/k3s-local.yaml)

```yaml
platform: k3s
environment: development
nodes: 3

k3s_config:
  disable:
    - traefik  # On utilise nginx
  write_kubeconfig_mode: "644"
```

**Usage** :

```bash
python main.py --config examples/k3s-local.yaml
```

#### EKS (AWS Production)

Voir [`examples/eks-prod.yaml`](../examples/eks-prod.yaml)

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

**Prérequis** :

```bash
# AWS CLI configuré
aws configure

# Ou variables d'environnement
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=eu-west-1
```

#### AKS (Azure)

Voir [`examples/aks-dev.yaml`](../examples/aks-dev.yaml)

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

**Prérequis** :

```bash
# Azure CLI
az login

# Ou variables d'environnement
export ARM_CLIENT_ID=...
export ARM_CLIENT_SECRET=...
export ARM_SUBSCRIPTION_ID=...
export ARM_TENANT_ID=...
```

---

## ⚙️ Options Avancées

### Monitoring Personnalisé

```yaml
monitoring:
  enabled: true
  retention: 30d
  
  # Alerting
  alerting: true
  slack_webhook: https://hooks.slack.com/services/XXX
  
  # Dashboards personnalisés
  dashboards:
    - kubernetes-cluster
    - node-exporter
    - custom-app-metrics  # Votre dashboard
  
  # Configuration Prometheus
  prometheus:
    scrape_interval: 30s
    evaluation_interval: 30s
    
  # Configuration Grafana
  grafana:
    admin_password: SecurePassword123!
    plugins:
      - grafana-piechart-panel
```

### Sécurité Avancée

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

### Networking Avancé

```yaml
networking:
  # CIDRs
  pod_cidr: 10.244.0.0/16
  service_cidr: 10.96.0.0/16
  
  # CNI
  cni_plugin: calico  # flannel, calico, weave
  
  # Service Mesh (optionnel)
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

### Tags Cloud (EKS/AKS)

```yaml
tags:
  Environment: production
  ManagedBy: terraform-k8s-agent
  Project: my-project
  CostCenter: engineering
  Owner: platform-team
```

### Labels Kubernetes

```yaml
labels:
  app: my-application
  version: v1.0.0
  tier: backend
  environment: production
```

---

## 🔧 Configuration des Agents

### Timeouts

```bash
# .env
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=3600  # secondes (1h)
```

### Verbosity

```bash
# .env
DEBUG=true  # Active les logs détaillés
TF_LOG=DEBUG  # Logs Terraform détaillés
```

---

## 📊 Configuration du Monitoring

### Prometheus

Custom configuration via ConfigMap :

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
    # Datasources supplémentaires
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

## 🚀 Profils Pré-configurés

### Profil "Quick Start"

Minimal, rapide, pour tests :

```bash
python main.py create \
  --platform k3s \
  --nodes 1 \
  --monitoring false
```

### Profil "Development"

Dev local avec monitoring :

```bash
python main.py --config examples/k3s-local.yaml
```

### Profil "Production"

HA, monitoring avancé, sécurité :

```bash
python main.py --config examples/eks-prod.yaml
```

---

## 📁 Hiérarchie des Configurations

Ordre de priorité (du plus haut au plus bas) :

1. **Arguments CLI** : `--nodes 5`
2. **Fichier YAML** : `--config config.yaml`
3. **Variables d'environnement** : `.env`
4. **Valeurs par défaut** : Dans le code

Exemple :

```bash
# nodes=5 (CLI override le YAML)
python main.py --config examples/k3s-local.yaml --nodes 5
```

---

## ✅ Validation de Configuration

Avant de lancer, validez votre config :

```bash
# Dry-run (plan seulement, pas d'apply)
DEBUG=true python main.py --config my-config.yaml
```

L'agent Planner validera et optimisera la config.

---

## 🔍 Troubleshooting Configuration

### Problème : LLM ne répond pas

```bash
# Vérifier la config
echo $OPENAI_API_KEY

# Tester manuellement
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Problème : Terraform errors

```bash
# Augmenter la verbosity
export TF_LOG=DEBUG
python main.py ...
```

### Problème : State database locked

```bash
# SQLite
rm ./data/state.db-*

# PostgreSQL
psql -d terraform_agent -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='terraform_agent';"
```

---

**Next**: Voir le [README.md](../README.md) principal pour les cas d'usage
