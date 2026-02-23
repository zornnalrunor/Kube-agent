# Architecture GitOps avec ArgoCD

## 🚀 Vue d'ensemble

Le système a été étendu avec une couche **GitOps** utilisant **ArgoCD** pour gérer tous les déploiements applicatifs (monitoring, futures applications).

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Agent                       │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌───────────┐   ┌────────────┐  ┌─────────────┐
    │  Planner  │   │    Infra   │  │   ArgoCD    │
    │   Agent   │   │   Agent    │  │    Agent    │
    └───────────┘   └────────────┘  └─────────────┘
                           │               │
                           │         Installe ArgoCD
                           │         App of Apps
                           │               │
                           ▼               ▼
                    ┌─────────────────────────────┐
                    │   Monitoring Agent          │
                    │  (GitOps Mode)              │
                    │   - Génère manifests        │
                    │   - Crée Git repo local     │
                    │   - Crée ArgoCD Apps        │
                    └─────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Validation Agent         │
                    │   - Check ArgoCD health     │
                    │   - Check Applications      │
                    │   - Check sync status       │
                    └─────────────────────────────┘
```

## 🔄 Workflow GitOps

### 1. **Infrastructure Agent** (Unchanged)
- Déploie K3s avec Terraform
- Génère le kubeconfig
- Configure le réseau

### 2. **ArgoCD Agent** (NOUVEAU)
- Installe ArgoCD dans le namespace `argocd`
- Configure le NodePort pour accès UI (port 30080)
- Récupère le mot de passe admin initial
- Prépare l'infrastructure App of Apps

**Outputs:**
```python
{
    "argocd_installed": bool,
    "argocd_namespace": "argocd",
    "argocd_url": "http://localhost:30080",
    "argocd_admin_password": str,
    "bootstrap_app": "root"
}
```

### 3. **Monitoring Agent** (MODIFIÉ - GitOps Mode)

#### Mode GitOps (si ArgoCD installé):
1. **Génère les manifests Kubernetes** (inchangé)
   - Prometheus, Grafana, Headlamp
   - Namespaces, ConfigMaps, Services

2. **Crée un repo Git local**
   ```
   output/gitops/{workflow-id}/
   ├── .git/
   ├── monitoring/
   │   ├── 00-namespace.yaml
   │   ├── 10-prometheus.yaml
   │   ├── 20-grafana.yaml
   │   └── 25-headlamp.yaml (si activé)
   ```

3. **Crée une ArgoCD Application**
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: monitoring-{workflow-id}
     namespace: argocd
   spec:
     project: default
     source:
       repoURL: file://{absolute-path}/output/gitops/{workflow-id}
       targetRevision: HEAD
       path: monitoring
     destination:
       server: https://kubernetes.default.svc
       namespace: monitoring
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   ```

4. **ArgoCD sync automatiquement** les ressources

#### Mode Direct (fallback si pas ArgoCD):
- Déploiement kubectl direct (ancien comportement)

### 4. **Validation Agent** (MODIFIÉ)

Ajoute des checks ArgoCD:
- ✅ Pods ArgoCD running
- ✅ Applications synced
- ✅ Applications healthy
- ✅ Health score incluant ArgoCD

## 🎯 Avantages de cette architecture

### ✅ Séparation des responsabilités
- **Infrastructure**: Réseau, K3s (Terraform)
- **GitOps**: Tout le reste (ArgoCD)

### ✅ Traçabilité Git
- Tous les manifests versionnés dans Git
- Historique complet des changements
- Rollback facile

### ✅ Reconciliation automatique
- Self-heal: ArgoCD recrée les ressources supprimées
- Prune: Supprime les ressources obsolètes
- Sync automatique sur changement

### ✅ Extensibilité
- Ajout facile de nouvelles applications
- Pattern App of Apps pour structurer
- Multi-environnements simple

### ✅ Visibilité
- UI ArgoCD pour voir l'état des déploiements
- Drift detection
- Logs centralisés

## 🔧 Utilisation

### Mode Démo (simulation)
```bash
python main.py create -p k3s -n 2 --monitoring --headlamp
```

### Mode Réel (installation complète)
```bash
python main.py create -p k3s -n 2 --monitoring --headlamp --real-deployment
```

### Accès aux UIs

Après déploiement en mode réel:

| Service    | URL                      | Credentials      |
|------------|--------------------------|------------------|
| ArgoCD     | http://localhost:30080   | admin / {secret} |
| Grafana    | http://localhost:30300   | admin / admin    |
| Prometheus | http://localhost:30090   | -                |
| Headlamp   | http://localhost:30466   | In-cluster auth  |

**Récupérer le mot de passe ArgoCD:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

## 📁 Structure des fichiers

```
output/
├── gitops/
│   └── {workflow-id}/          # Repo Git local
│       ├── .git/
│       └── monitoring/
│           ├── 00-namespace.yaml
│           ├── 10-prometheus.yaml
│           ├── 20-grafana.yaml
│           └── 25-headlamp.yaml
├── argocd-apps/
│   └── {workflow-id}/
│       └── monitoring-app.yaml  # Application ArgoCD
└── manifests/
    └── {workflow-id}/
        └── monitoring/          # Manifests originaux
```

## 🔮 Évolutions futures

### App of Apps complet
```
root/
├── argocd/          # ArgoCD s'auto-gère
├── monitoring/      # Stack monitoring
├── apps/
│   ├── webapp/      # Applications métier
│   ├── database/
│   └── cache/
```

### Multi-sources
- Manifests depuis Git distant (GitHub/GitLab)
- Helm charts depuis registries
- Kustomize overlays

### Multi-clusters
- ArgoCD ApplicationSets
- Cluster generators
- Matrix generators

### CI/CD intégration
- Webhooks sur Git push
- Image updater automatique
- Progressive delivery (Argo Rollouts)

## 🐛 Troubleshooting

### ArgoCD ne synchro pas
```bash
# Forcer un refresh
kubectl -n argocd get app monitoring-{workflow-id} -o yaml
argocd app sync monitoring-{workflow-id}
```

### Pods en CrashLoop
```bash
# Logs ArgoCD
kubectl -n argocd logs -l app.kubernetes.io/name=argocd-server

# Logs Application
kubectl -n monitoring logs -l app=prometheus
```

### Repo Git local non trouvé
- Vérifier que le path absolu est correct dans l'Application
- Vérifier que ArgoCD peut accéder au filesystem (permissions)

## 📚 Références

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [App of Apps Pattern](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/)
- [GitOps Principles](https://www.gitops.tech/)
