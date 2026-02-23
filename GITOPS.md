# GitOps Architecture with ArgoCD

## 🚀 Overview

The system has been extended with a **GitOps** layer using **ArgoCD** to manage all application deployments (monitoring, future applications).

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
                           │         Installs ArgoCD
                           │         App of Apps
                           │               │
                           ▼               ▼
                    ┌─────────────────────────────┐
                    │   Monitoring Agent          │
                    │  (GitOps Mode)              │
                    │   - Generate manifests      │
                    │   - Create local Git repo   │
                    │   - Create ArgoCD Apps      │
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

## 🔄 GitOps Workflow

### 1. **Infrastructure Agent** (Unchanged)
- Deploys K3s with Terraform
- Generates kubeconfig
- Configures network

### 2. **ArgoCD Agent** (NEW)
- Installs ArgoCD in `argocd` namespace
- Configures NodePort for UI access (port 30080)
- Retrieves initial admin password
- Prepares App of Apps infrastructure

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

### 3. **Monitoring Agent** (MODIFIED - GitOps Mode)

#### GitOps Mode (if ArgoCD installed):
1. **Generate Kubernetes manifests** (unchanged)
   - Prometheus, Grafana, Headlamp
   - Namespaces, ConfigMaps, Services

2. **Create local Git repo**
   ```
   output/gitops/{workflow-id}/
   ├── .git/
   ├── monitoring/
   │   ├── 00-namespace.yaml
   │   ├── 10-prometheus.yaml
   │   ├── 20-grafana.yaml
   │   └── 25-headlamp.yaml (if enabled)
   ```

3. **Create ArgoCD Application**
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

4. **ArgoCD automatically syncs** resources

#### Direct Mode (fallback if no ArgoCD):
- Direct kubectl deployment (old behavior)

### 4. **Validation Agent** (MODIFIED)

Adds ArgoCD checks:
- ✅ ArgoCD pods running
- ✅ Applications synced
- ✅ Applications healthy
- ✅ Health score including ArgoCD

## 🎯 Architecture Benefits

### ✅ Separation of responsibilities
- **Infrastructure**: Network, K3s (Terraform)
- **GitOps**: Everything else (ArgoCD)

### ✅ Git traceability
- All manifests versioned in Git
- Complete change history
- Easy rollback

### ✅ Automatic reconciliation
- Self-heal: ArgoCD recreates deleted resources
- Prune: Removes obsolete resources
- Automatic sync on changes

### ✅ Extensibility
- Easy addition of new applications
- App of Apps pattern for structure
- Simple multi-environment

### ✅ Visibility
- ArgoCD UI to see deployment state
- Drift detection
- Centralized logs

## 🔧 Usage

### Demo Mode (simulation)
```bash
python main.py create -p k3s -n 2 --monitoring --headlamp
```

### Real Mode (complete installation)
```bash
python main.py create -p k3s -n 2 --monitoring --headlamp --real-deployment
```

### UI Access

After deployment in real mode:

| Service    | URL                      | Credentials      |
|------------|--------------------------|------------------|
| ArgoCD     | http://localhost:30080   | admin / {secret} |
| Grafana    | http://localhost:30300   | admin / admin    |
| Prometheus | http://localhost:30090   | -                |
| Headlamp   | http://localhost:30466   | In-cluster auth  |

**Retrieve ArgoCD password:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

## 📁 File Structure

```
output/
├── gitops/
│   └── {workflow-id}/          # Local Git repo
│       ├── .git/
│       └── monitoring/
│           ├── 00-namespace.yaml
│           ├── 10-prometheus.yaml
│           ├── 20-grafana.yaml
│           └── 25-headlamp.yaml
├── argocd-apps/
│   └── {workflow-id}/
│       └── monitoring-app.yaml  # ArgoCD Application
└── manifests/
    └── {workflow-id}/
        └── monitoring/          # Original manifests
```

## 🔮 Future Evolutions

### Complete App of Apps
```
root/
├── argocd/          # ArgoCD self-management
├── monitoring/      # Monitoring stack
├── apps/
│   ├── webapp/      # Business applications
│   ├── database/
│   └── cache/
```

### Multi-sources
- Manifests from remote Git (GitHub/GitLab)
- Helm charts from registries
- Kustomize overlays

### Multi-clusters
- ArgoCD ApplicationSets
- Cluster generators
- Matrix generators

### CI/CD integration
- Webhooks on Git push
- Automatic image updater
- Progressive delivery (Argo Rollouts)

## 🐛 Troubleshooting

### ArgoCD not syncing
```bash
# Force refresh
kubectl -n argocd get app monitoring-{workflow-id} -o yaml
argocd app sync monitoring-{workflow-id}
```

### Pods in CrashLoop
```bash
# ArgoCD logs
kubectl -n argocd logs -l app.kubernetes.io/name=argocd-server

# Application logs
kubectl -n monitoring logs -l app=prometheus
```

### Local Git repo not found
- Verify absolute path is correct in Application
- Verify ArgoCD can access filesystem (permissions)

## 📚 References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [App of Apps Pattern](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/)
- [GitOps Principles](https://www.gitops.tech/)
