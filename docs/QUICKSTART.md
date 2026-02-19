# Guide de Démarrage Rapide

## 🚀 Installation en 5 Minutes

### 1. Prérequis

```bash
# Python 3.11+
python --version

# Terraform
terraform --version

# kubectl
kubectl version --client

# Git
git --version
```

### 2. Cloner et Installer

```bash
# Cloner le repo (ou l'extraire si fichier local)
cd Terraform-agent-eks-aks

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copier l'exemple de config
cp .env.example .env

# Éditer la config
nano .env
```

**Configuration minimale** :

```bash
# Choisir un provider LLM
LLM_PROVIDER=ollama  # Gratuit et local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Ou OpenAI (payant mais performant)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
```

Si vous utilisez Ollama :

```bash
# Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Télécharger un modèle
ollama pull llama2

# Vérifier que ça fonctionne
ollama list
```

### 4. Premier Test - Mode Interactif

```bash
python main.py
```

Suivez les prompts :
1. Choisir **K3s** (option 1)
2. Environnement **Development** (option 1)
3. **3 nœuds**
4. **Activer le monitoring** (Y)
5. Confirmer (Y)

🎉 Le système va :
- Analyser vos besoins
- Optimiser la configuration
- Générer le Terraform
- Créer le cluster (simulation pour la démo)
- Déployer Prometheus/Grafana
- Valider le cluster
- Générer la documentation

### 5. Résultat

Vous obtiendrez :

```
✅ Déploiement terminé avec succès!

📊 Grafana: http://localhost:3000 (admin/admin)
📈 Prometheus: http://localhost:9090
📝 Documentation: ./output/docs/k3s-development-xxxxx/
```

---

## 🎯 Cas d'Usage Courants

### Cas 1 : Dev Local Rapide

**Objectif** : Cluster K3s minimal pour dev

```bash
python main.py create \
  --platform k3s \
  --environment development \
  --nodes 1 \
  --monitoring false
```

**Durée** : ~2 minutes

### Cas 2 : Dev avec Monitoring

**Objectif** : Cluster complet pour tester le monitoring

```bash
python main.py --config examples/k3s-local.yaml
```

**Durée** : ~5 minutes

### Cas 3 : Production EKS

**Objectif** : Cluster production AWS avec HA

**Prérequis** :
```bash
# Configurer AWS CLI
aws configure
```

**Commande** :
```bash
python main.py --config examples/eks-prod.yaml
```

**Durée** : ~15-20 minutes

### Cas 4 : Staging AKS

**Objectif** : Cluster staging Azure

**Prérequis** :
```bash
# Login Azure
az login
```

**Commande** :
```bash
python main.py --config examples/aks-dev.yaml
```

**Durée** : ~10-15 minutes

---

## 📊 Accéder au Monitoring

### Grafana

```bash
# Récupérer l'URL depuis le résultat du déploiement
# Ou dans la documentation générée

# Accéder
open http://localhost:3000

# Credentials (par défaut)
Username: admin
Password: admin
```

**Dashboards disponibles** :
- Kubernetes Cluster Monitoring
- Node Exporter Full
- Prometheus Stats
- Pod Monitoring

### Prometheus

```bash
# Accéder
open http://localhost:9090

# Queries utiles
up{}  # Tous les targets
node_cpu_seconds_total  # CPU usage
node_memory_MemAvailable_bytes  # Memory disponible
```

---

## 🔍 Vérifier le Cluster

### Via kubectl

```bash
# Obtenir le kubeconfig depuis la doc générée
export KUBECONFIG=./output/kubeconfigs/k3s-development-xxxxx.kubeconfig

# Vérifier les nodes
kubectl get nodes

# Vérifier tous les pods
kubectl get pods --all-namespaces

# Vérifier le monitoring
kubectl get pods -n monitoring
```

### Via le Script de Validation

```bash
# Obtenir le workflow ID depuis le résultat
python main.py status k3s-development-xxxxx
```

---

## 📚 Explorer la Documentation

Chaque déploiement génère une documentation complète :

```bash
cd output/docs/k3s-development-xxxxx/

# Lire le README
cat README.md

# Architecture
cat ARCHITECTURE.md

# Runbook opérationnel
cat RUNBOOK.md

# Guide de troubleshooting
cat TROUBLESHOOTING.md

# Voir le diagramme
cat ARCHITECTURE_DIAGRAM.txt
```

---

## 🔧 Mode CLI Avancé

### Créer un Cluster

```bash
python main.py create \
  --platform k3s \
  --environment production \
  --nodes 5 \
  --monitoring true \
  --region us-east-1  # pour EKS/AKS
```

### Vérifier le Statut

```bash
# Liste des workflows
python main.py list-workflows

# Détails d'un workflow
python main.py status <workflow-id>
```

### Détruire un Cluster

```bash
python main.py destroy <workflow-id>
```

---

## 🐛 Troubleshooting Rapide

### Problème : Import errors

```bash
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Problème : LLM timeout

```bash
# Si Ollama
# Vérifier le service
systemctl status ollama

# Relancer
ollama serve

# Si OpenAI
# Vérifier la clé API
echo $OPENAI_API_KEY
```

### Problème : Terraform errors

```bash
# Vérifier Terraform
terraform --version

# Réinstaller si nécessaire
# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Problème : Ports déjà utilisés

Si les ports 3000 (Grafana) ou 9090 (Prometheus) sont occupés :

```bash
# Identifier le process
sudo lsof -i :3000
sudo lsof -i :9090

# Tuer si nécessaire
sudo kill -9 <PID>
```

---

## 🎓 Prochaines Étapes

### 1. Comprendre l'Architecture

Lire [ARCHITECTURE.md](ARCHITECTURE.md) pour comprendre :
- Le système multi-agents
- Le workflow d'exécution
- La gestion de l'état

### 2. Personnaliser la Configuration

Lire [CONFIGURATION.md](CONFIGURATION.md) pour :
- Adapter aux besoins spécifiques
- Configurer le monitoring avancé
- Gérer les secrets

### 3. Comprendre les Agents

Lire [AGENTS.md](AGENTS.md) pour :
- Détail de chaque agent
- Étendre le système
- Ajouter des agents

### 4. Déployer en Production

```bash
# 1. Configurer les credentials cloud
# AWS
aws configure

# 2. Adapter la config production
cp examples/eks-prod.yaml my-prod-config.yaml
nano my-prod-config.yaml

# 3. Déployer
python main.py --config my-prod-config.yaml

# 4. Vérifier
kubectl get nodes
```

---

## 💡 Tips & Best Practices

### 1. Naming Convention

```yaml
# Utiliser des noms descriptifs
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

Toujours activer le monitoring, même en dev :

```yaml
monitoring:
  enabled: true
```

### 4. Documentation

La doc est générée automatiquement. La partager avec l'équipe :

```bash
# Générer et commit
git add output/docs/
git commit -m "Add cluster documentation"
```

### 5. State Management

Pour le travail en équipe, utiliser PostgreSQL :

```bash
STATE_BACKEND=postgresql
STATE_DB_URL=postgresql://user:pass@db-server:5432/terraform_agent
```

---

## 📞 Support

### Documentation

- [README.md](../README.md) - Overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture détaillée
- [AGENTS.md](AGENTS.md) - Documentation des agents
- [CONFIGURATION.md](CONFIGURATION.md) - Options de configuration

### Logs

```bash
# Activer les logs détaillés
DEBUG=true python main.py ...

# Logs Terraform
TF_LOG=DEBUG python main.py ...
```

### État du Système

```bash
# Vérifier la base de données d'état
sqlite3 ./data/state.db

# Lister les workflows
SELECT workflow_id, status, platform FROM workflows;

# Lister les exécutions d'agents
SELECT agent_name, status FROM agent_executions WHERE workflow_id='xxx';
```

---

**Vous êtes prêt !** 🚀

Commencez par le mode interactif et explorez les fonctionnalités progressivement.
