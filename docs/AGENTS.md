# Documentation des Agents

## 🤖 Vue d'Ensemble

Ce document détaille le rôle et le fonctionnement de chaque agent du système.

## 📋 Orchestrator Agent

### Responsabilités

- **Coordination** : Orchestre l'exécution de tous les agents
- **Workflow** : Gère le flux d'exécution
- **État** : Maintient l'état global
- **Erreurs** : Décide des actions en cas d'échec
- **Reporting** : Génère le rapport final

### Workflow d'Exécution

```python
def execute(self, agent_input: AgentInput) -> AgentOutput:
    # 1. Initialisation
    display_banner()
    
    # 2. Exécution séquentielle des agents
    for agent_name, description in workflow_steps:
        # 2.1 Préparer l'input
        step_input = prepare_input(previous_outputs)
        
        # 2.2 Mettre à jour le statut
        update_workflow_status(step_name)
        
        # 2.3 Exécuter l'agent
        result = agent.run(step_input)
        
        # 2.4 Vérifier le résultat
        if not result.success and is_critical:
            break  # Arrêt si agent critique échoue
    
    # 3. Générer le résumé
    display_summary(outputs, errors)
    
    return final_output
```

### Décisions Critiques

L'orchestrateur détermine quels agents sont critiques :

```python
def _is_critical_agent(self, agent_name: str) -> bool:
    critical_agents = {"planner", "infrastructure"}
    return agent_name in critical_agents
```

- **Critiques** : Planner, Infrastructure → Échec = Arrêt
- **Non-critiques** : Monitoring, Documentation → Échec = Warning

### Interface Utilisateur

L'orchestrateur gère l'affichage Rich console :
- Banner de démarrage
- Progress bars
- Table de résumé
- Accès finaux (URLs)

---

## 📊 Planner Agent

### Responsabilités

- **Analyse** : Comprendre les requirements utilisateur
- **Optimisation** : Utiliser l'IA pour optimiser la config
- **Planification** : Générer un plan d'exécution détaillé
- **Estimation** : Calculer ressources et temps nécessaires

### Intelligence Artificielle

Le Planner utilise l'IA pour optimiser la configuration :

```python
def _optimize_configuration(self, context: Dict) -> Dict:
    prompt = f"""
    You are a Kubernetes infrastructure expert. 
    Optimize this configuration for {platform} in {environment}:
    
    {json.dumps(context, indent=2)}
    
    Consider:
    1. Resource sizing (CPU, memory)
    2. High availability
    3. Security best practices
    4. Cost optimization
    5. Monitoring and observability
    
    Return ONLY a JSON object.
    """
    
    response = self.prompt_llm(prompt)
    return json.loads(response)
```

### Configuration par Environnement

Le Planner adapte la config selon l'environnement :

| Environnement | Nodes Min | Instance Type | Disk | HA |
|---------------|-----------|---------------|------|-----|
| Development   | 1         | t3.medium     | 50GB | No  |
| Staging       | 2         | t3.large      | 100GB| Partial |
| Production    | 3+        | t3.xlarge     | 200GB| Yes |

### Plan d'Exécution

Structure du plan généré :

```python
{
    "platform": "k3s",
    "environment": "development",
    "steps": [
        {
            "name": "infrastructure",
            "description": "Provisioning k3s cluster",
            "tasks": [
                "Initialize Terraform",
                "Create network resources",
                "Provision compute instances",
                "Configure Kubernetes"
            ],
            "estimated_time": 5  # minutes
        },
        # ... autres steps
    ],
    "total_steps": 4
}
```

### Validation

Le Planner valide le plan avant exécution :

- ✅ Plan a des étapes
- ✅ Chaque étape a des tâches
- ✅ Estimations cohérentes
- ⚠️ Warnings pour configurations sous-optimales

---

## 🏗️ Infrastructure Agent

### Responsabilités

- **Génération** : Créer le code Terraform
- **Initialisation** : `terraform init`
- **Planification** : `terraform plan`
- **Application** : `terraform apply`
- **Outputs** : Récupérer les informations du cluster

### Génération Terraform

Le code Terraform est généré dynamiquement :

```python
def _generate_terraform_files(self, workspace, platform, config):
    # main.tf
    main_tf = self._generate_main_tf(platform, config)
    
    # variables.tf
    variables_tf = self._generate_variables_tf(config)
    
    # terraform.tfvars
    tfvars = self._generate_tfvars(config)
    
    # outputs.tf
    outputs_tf = self._generate_outputs_tf(platform)
```

### Adaptation par Plateforme

#### K3s (Local/VMs)

```hcl
resource "null_resource" "k3s_cluster" {
  provisioner "local-exec" {
    command = "k3s server --cluster-init"
  }
}
```

#### EKS (AWS)

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  # ...
}
```

#### AKS (Azure)

```hcl
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  # ...
}
```

### Kubeconfig Management

```python
def _save_kubeconfig(self, workflow_id: str, content: str) -> str:
    kubeconfig_path = output_dir / "kubeconfigs" / f"{workflow_id}.kubeconfig"
    kubeconfig_path.write_text(content)
    kubeconfig_path.chmod(0o600)  # Sécurité
    return str(kubeconfig_path)
```

### Error Handling

L'agent Infrastructure gère les erreurs Terraform :

```python
return_code, stdout, stderr = tf.apply()

if return_code != 0:
    # Parse l'erreur Terraform
    error_msg = parse_terraform_error(stderr)
    
    # Log
    self.log_error(f"Terraform failed: {error_msg}")
    
    # Décide de la suite
    if should_rollback:
        terraform_destroy()
```

---

## 📈 Monitoring Agent

### Responsabilités

- **Prometheus** : Déployer et configurer Prometheus Operator
- **Grafana** : Déployer Grafana avec datasources
- **Dashboards** : Importer les dashboards pré-configurés
- **Alertes** : Configurer les règles d'alerte
- **ServiceMonitors** : Créer les ServiceMonitors

### Stack Monitoring

```
Grafana (Visualization)
    ↓ queries
Prometheus (Metrics DB)
    ↑ scrapes
ServiceMonitors (Targets)
    ↑ expose
Applications/Infrastructure
```

### Manifests Kubernetes

L'agent génère les manifests K8s :

```python
def _generate_monitoring_manifests(self, workflow_id, config):
    # Namespace
    namespace = {"apiVersion": "v1", "kind": "Namespace", ...}
    
    # Prometheus ConfigMap
    prometheus_cm = self._generate_prometheus_manifest(config)
    
    # Grafana ConfigMap (datasources)
    grafana_cm = self._generate_grafana_manifest(config)
    
    # ServiceMonitors
    service_monitors = self._generate_service_monitors()
```

### Dashboards Pré-configurés

Dashboards automatiquement importés :

1. **Kubernetes Cluster Monitoring**
   - Vue d'ensemble du cluster
   - CPU/Memory par node
   - Pods status

2. **Node Exporter Full**
   - Métriques système détaillées
   - Disk I/O
   - Network traffic

3. **Prometheus Stats**
   - Métriques Prometheus lui-même
   - Scrape duration
   - Rule evaluation

4. **Pod Monitoring**
   - Métriques par pod
   - Restart count
   - Resource usage

5. **Namespace Resources**
   - Vue par namespace
   - Quotas
   - Limits vs requests

### Configuration des Alertes

Si `alerting: true` dans la config :

```yaml
groups:
  - name: kubernetes-alerts
    interval: 30s
    rules:
      - alert: NodeDown
        expr: up{job="kubernetes-nodes"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Node {{ $labels.node }} is down"
```

---

## ✅ Validation Agent

### Responsabilités

- **Nodes** : Vérifier que tous les nœuds sont Ready
- **Pods** : Vérifier que les pods système fonctionnent
- **Monitoring** : Tester les endpoints Prometheus/Grafana
- **Networking** : Valider la configuration réseau
- **Health Score** : Calculer un score de santé global

### Checks Effectués

#### 1. Node Status

```python
def _check_nodes(self, kubeconfig_path: str) -> Dict:
    # kubectl get nodes
    return {
        "total": 3,
        "ready": 3,
        "not_ready": 0,
        "nodes": [...]
    }
```

#### 2. Pod Status

```python
def _check_system_pods(self, kubeconfig_path: str) -> Dict:
    # kubectl get pods -n kube-system
    # kubectl get pods -n monitoring
    return {
        "total": 12,
        "running": 12,
        "pending": 0,
        "failed": 0
    }
```

#### 3. Monitoring Endpoints

```python
def _check_monitoring_endpoints(self, monitoring_output: Dict) -> Dict:
    prometheus_url = monitoring_output["prometheus_url"]
    grafana_url = monitoring_output["grafana_url"]
    
    # HTTP GET requests
    prometheus_ok = check_endpoint(prometheus_url)
    grafana_ok = check_endpoint(grafana_url)
    
    return {
        "prometheus_ok": prometheus_ok,
        "grafana_ok": grafana_ok,
        "targets": {...}
    }
```

#### 4. Networking

```python
def _check_networking(self, kubeconfig_path: str) -> Dict:
    return {
        "ok": True,
        "pod_cidr": "10.244.0.0/16",
        "service_cidr": "10.96.0.0/16",
        "dns_ok": True,
        "connectivity_ok": True
    }
```

### Health Score

Calcul du score de santé (0-100) :

```python
def _calculate_health_score(self, health_report: Dict) -> int:
    checks = health_report["checks"]
    passed = sum(1 for c in checks if c["status"] == "passed")
    total = len(checks)
    return int((passed / total) * 100)
```

Statut selon le score :
- **90-100** : Excellent ✅
- **80-89** : Bon ⚠️
- **< 80** : Problèmes ❌

### Rapport de Santé

```python
health_report = {
    "checks": [
        {"category": "Nodes", "status": "passed", "message": "3/3 ready"},
        {"category": "Pods", "status": "passed", "message": "12/12 running"},
        {"category": "Monitoring", "status": "passed", "message": "Operational"},
        {"category": "Networking", "status": "passed", "message": "Valid"},
    ],
    "timestamp": "2024-02-19T10:00:00Z",
    "overall_status": "healthy"
}
```

---

## 📚 Documentation Agent

### Responsabilités

- **README** : Document principal avec infos d'accès
- **Architecture** : Documentation d'architecture détaillée
- **Runbook** : Procédures opérationnelles
- **Troubleshooting** : Guide de dépannage
- **Configs** : Export des configurations
- **Diagrammes** : Schémas ASCII de l'architecture

### Documents Générés

#### 1. README.md

Contient :
- Informations générales du cluster
- Architecture déployée
- Accès (Kubeconfig, Grafana, Prometheus)
- État du cluster
- Commandes utiles
- Procédure de destruction

#### 2. ARCHITECTURE.md

Documente :
- Configuration infrastructure
- Configuration réseau
- Stack monitoring
- Sécurité (RBAC, Network Policies)
- Addons installés

#### 3. RUNBOOK.md

Procédures pour :
- Monitoring quotidien
- Métriques à surveiller
- Procédures d'urgence (node down, pod crash, etc.)
- Opérations de maintenance
- Scaling
- Backups

#### 4. TROUBLESHOOTING.md

Guide de dépannage :
- Problèmes courants
- Commandes de diagnostic
- Solutions step-by-step
- Contacts et escalade

#### 5. Configurations Exportées

```
configs/
├── cluster-config.json      # Config complète
├── terraform-info.json      # Infos Terraform
└── metadata.json            # Metadata du workflow
```

### Diagramme ASCII

L'agent génère un diagramme d'architecture :

```
╔════════════════════════════════════════╗
║        ARCHITECTURE - K3S CLUSTER       ║
╚════════════════════════════════════════╝

┌────────────────────────────────────────┐
│           CONTROL PLANE                 │
│  ┌──────────┐  ┌──────────┐           │
│  │API Server│  │Scheduler │           │
│  └──────────┘  └──────────┘           │
└────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│ Node 1 │      │ Node 2  │
└────────┘      └─────────┘
```

---

## 🔄 Cycle de Vie d'un Agent

### 1. Initialisation

```python
agent = MyAgent(config, state_manager, llm)
```

### 2. Enregistrement

```python
orchestrator.register_agent("myagent", agent)
```

### 3. Exécution

```python
# L'orchestrateur appelle
result = agent.run(agent_input)

# Qui wrapper execute()
def run(self, input):
    # Log start
    # Create execution record
    # Call execute()
    # Handle errors
    # Log end
    # Update execution record
```

### 4. Implémentation de execute()

```python
def execute(self, agent_input: AgentInput) -> AgentOutput:
    logs = []
    errors = []
    
    try:
        # 1. Récupérer le contexte
        context = agent_input.context
        previous_outputs = agent_input.previous_outputs
        
        # 2. Logique métier
        result = do_work(context)
        
        # 3. Logs
        self.log_success("Work completed")
        logs.append("Work done")
        
        # 4. Return
        return AgentOutput(
            agent_name=self.agent_name,
            success=True,
            data={"result": result},
            logs=logs
        )
    except Exception as e:
        errors.append(str(e))
        return AgentOutput(
            agent_name=self.agent_name,
            success=False,
            errors=errors,
            logs=logs
        )
```

---

**Next**: Voir [CONFIGURATION.md](CONFIGURATION.md) pour les options de configuration
