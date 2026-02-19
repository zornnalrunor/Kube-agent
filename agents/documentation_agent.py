"""
Documentation Agent
Agent responsable de la génération automatique de la documentation
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class DocumentationAgent(BaseAgent):
    """
    Agent de documentation
    
    Responsabilités:
    - Générer la documentation technique
    - Créer les runbooks
    - Documenter l'architecture déployée
    - Générer des diagrammes
    - Créer les guides d'opération
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Génère la documentation complète
        
        Args:
            agent_input: Input contenant tous les outputs précédents
            
        Returns:
            AgentOutput: Documentation générée
        """
        logs = []
        errors = []
        
        try:
            self.log("Generating documentation")
            
            # Récupérer tous les outputs
            planner_output = agent_input.previous_outputs.get("planner", {})
            infra_output = agent_input.previous_outputs.get("infrastructure", {})
            monitoring_output = agent_input.previous_outputs.get("monitoring", {})
            validation_output = agent_input.previous_outputs.get("validation", {})
            
            config = planner_output.get("optimized_config", agent_input.context)
            platform = config.get("platform", "k3s")
            environment = config.get("environment", "development")
            
            # Créer le répertoire de documentation
            docs_dir = self._prepare_docs_directory(agent_input.workflow_id)
            logs.append(f"Documentation directory: {docs_dir}")
            
            # Générer README principal
            self.log("Generating README...")
            readme_path = self._generate_readme(
                docs_dir,
                agent_input.workflow_id,
                config,
                planner_output,
                infra_output,
                monitoring_output,
                validation_output
            )
            logs.append(f"README generated: {readme_path}")
            self.log_success("README.md generated")
            
            # Générer le document d'architecture
            self.log("Generating architecture documentation...")
            arch_path = self._generate_architecture_doc(
                docs_dir,
                config,
                infra_output,
                monitoring_output
            )
            logs.append(f"Architecture doc: {arch_path}")
            self.log_success("ARCHITECTURE.md generated")
            
            # Générer le runbook opérationnel
            self.log("Generating operational runbook...")
            runbook_path = self._generate_runbook(
                docs_dir,
                config,
                infra_output,
                monitoring_output
            )
            logs.append(f"Runbook: {runbook_path}")
            self.log_success("RUNBOOK.md generated")
            
            # Générer le guide de troubleshooting
            self.log("Generating troubleshooting guide...")
            troubleshooting_path = self._generate_troubleshooting(
                docs_dir,
                platform,
                monitoring_output
            )
            logs.append(f"Troubleshooting: {troubleshooting_path}")
            self.log_success("TROUBLESHOOTING.md generated")
            
            # Générer les configurations exportées
            self.log("Exporting configurations...")
            config_path = self._export_configurations(
                docs_dir,
                agent_input.workflow_id,
                config,
                infra_output
            )
            logs.append(f"Configurations exported: {config_path}")
            self.log_success("Configurations exported")
            
            # Générer un diagramme d'architecture ASCII
            self.log("Generating architecture diagram...")
            diagram = self._generate_architecture_diagram(config, monitoring_output)
            diagram_path = docs_dir / "ARCHITECTURE_DIAGRAM.txt"
            diagram_path.write_text(diagram)
            logs.append(f"Diagram: {diagram_path}")
            self.log_success("Architecture diagram generated")
            
            # Liste de tous les fichiers générés
            generated_files = list(docs_dir.glob("*"))
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=True,
                data={
                    "docs_directory": str(docs_dir),
                    "readme_path": str(readme_path),
                    "architecture_path": str(arch_path),
                    "runbook_path": str(runbook_path),
                    "troubleshooting_path": str(troubleshooting_path),
                    "config_path": str(config_path),
                    "generated_files": [str(f) for f in generated_files],
                    "summary": f"Documentation generated in {docs_dir.name}"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Documentation generation failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _prepare_docs_directory(self, workflow_id: str) -> Path:
        """Prépare le répertoire de documentation"""
        docs_dir = self.config.output_dir / "docs" / workflow_id
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir
    
    def _generate_readme(
        self,
        docs_dir: Path,
        workflow_id: str,
        config: Dict[str, Any],
        planner_output: Dict[str, Any],
        infra_output: Dict[str, Any],
        monitoring_output: Dict[str, Any],
        validation_output: Dict[str, Any]
    ) -> Path:
        """Génère le README principal"""
        
        platform = config.get("platform", "k3s")
        environment = config.get("environment", "development")
        nodes = config.get("nodes", 1)
        
        grafana_url = monitoring_output.get("grafana_url", "N/A")
        prometheus_url = monitoring_output.get("prometheus_url", "N/A")
        health_score = validation_output.get("health_score", "N/A")
        
        content = f"""# Cluster Kubernetes - {workflow_id}

## 📋 Informations Générales

- **Workflow ID**: `{workflow_id}`
- **Plateforme**: {platform.upper()}
- **Environnement**: {environment}
- **Nombre de nœuds**: {nodes}
- **Date de création**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Score de santé**: {health_score}/100

## 🏗️ Architecture

Ce cluster a été automatiquement provisionné et configuré via le système Terraform K8s Agent.

### Composants Déployés

#### Infrastructure
- **Plateforme**: {platform}
- **Nodes**: {nodes} nœuds
- **Version Kubernetes**: {config.get('kubernetes_version', '1.28')}

#### Monitoring
- **Prometheus**: {prometheus_url}
- **Grafana**: {grafana_url}
  - Username: `admin`
  - Password: `{config.get('monitoring', {}).get('grafana_password', 'admin')}`

#### Addons
"""
        
        addons = config.get('addons', {})
        for addon, enabled in addons.items():
            if enabled:
                content += f"- ✅ {addon}\n"
        
        content += f"""
## 🚀 Accès au Cluster

### Kubeconfig

```bash
export KUBECONFIG={infra_output.get('kubeconfig_path', 'N/A')}
kubectl get nodes
kubectl get pods --all-namespaces
```

### Monitoring

#### Grafana
- URL: {grafana_url}
- Dashboards pré-configurés:
"""
        
        for dashboard in monitoring_output.get('dashboards', []):
            content += f"  - {dashboard}\n"
        
        content += f"""
#### Prometheus
- URL: {prometheus_url}
- Targets: {validation_output.get('monitoring_status', {}).get('targets', {}).get('up', 'N/A')} up

## 📊 État du Cluster

### Nœuds
```
{validation_output.get('nodes_ready', 'N/A')} nœuds ready
```

### Pods
```
{validation_output.get('pods_running', 'N/A')} pods running
```

### Capacité
- **CPU**: {validation_output.get('capacity', {}).get('cpu', 'N/A')}
- **Memory**: {validation_output.get('capacity', {}).get('memory', 'N/A')}
- **Storage**: {validation_output.get('capacity', {}).get('storage', 'N/A')}

## 📚 Documentation

- [Architecture détaillée](ARCHITECTURE.md)
- [Runbook opérationnel](RUNBOOK.md)
- [Guide de troubleshooting](TROUBLESHOOTING.md)
- [Configurations exportées](configs/)

## 🔧 Commandes Utiles

### Vérifier la santé du cluster
```bash
kubectl get nodes
kubectl get pods --all-namespaces
kubectl top nodes
kubectl top pods --all-namespaces
```

### Accéder aux logs
```bash
# Logs Prometheus
kubectl logs -n monitoring -l app=prometheus

# Logs Grafana
kubectl logs -n monitoring -l app=grafana
```

### Port-forwarding local
```bash
# Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

## 🆘 Support

En cas de problème, consultez le [guide de troubleshooting](TROUBLESHOOTING.md) ou les logs des agents:
- Planner: Analyse et optimisation de la configuration
- Infrastructure: Provisioning Terraform
- Monitoring: Déploiement Prometheus/Grafana
- Validation: Vérifications de santé

## 🗑️ Destruction

Pour détruire ce cluster:

```bash
cd {infra_output.get('workspace', 'N/A')}
terraform destroy -auto-approve
```

---
*Documentation générée automatiquement par Terraform K8s Agent*
"""
        
        readme_path = docs_dir / "README.md"
        readme_path.write_text(content)
        return readme_path
    
    def _generate_architecture_doc(
        self,
        docs_dir: Path,
        config: Dict[str, Any],
        infra_output: Dict[str, Any],
        monitoring_output: Dict[str, Any]
    ) -> Path:
        """Génère la documentation d'architecture"""
        
        platform = config.get("platform", "k3s")
        
        content = f"""# Architecture du Cluster

## Vue d'Ensemble

Ce document décrit l'architecture du cluster Kubernetes déployé sur **{platform}**.

## Infrastructure

### Plateforme: {platform.upper()}

#### Configuration Réseau
- **Pod CIDR**: {config.get('networking', {}).get('pod_cidr', '10.244.0.0/16')}
- **Service CIDR**: {config.get('networking', {}).get('service_cidr', '10.96.0.0/16')}

#### Nœuds
- **Nombre**: {config.get('nodes', 1)}
- **Type**: {config.get('resources', {}).get('instance_type', 'N/A')}
- **CPU**: {config.get('resources', {}).get('cpu', 'N/A')}
- **Memory**: {config.get('resources', {}).get('memory', 'N/A')}

## Stack Monitoring

### Prometheus
- **Namespace**: monitoring
- **Retention**: {config.get('monitoring', {}).get('retention', '15d')}
- **Scrape Interval**: 15s

#### Targets
- kubernetes-nodes
- kubernetes-pods
- kubernetes-services

### Grafana
- **Namespace**: monitoring
- **Datasource**: Prometheus (par défaut)
- **Dashboards**: {len(monitoring_output.get('dashboards', []))} pré-configurés

## Sécurité

### RBAC
- **Activé**: {config.get('security', {}).get('rbac_enabled', True)}

### Network Policies
- **Activées**: {config.get('security', {}).get('network_policies', False)}

### Pod Security
- **Policy activée**: {config.get('security', {}).get('pod_security_policy', False)}

## Addons

### Installés
"""
        
        for addon, enabled in config.get('addons', {}).items():
            status = "✅" if enabled else "❌"
            content += f"- {status} **{addon}**\n"
        
        content += """
## Flux de Données

1. **Metrics Collection**: Les node-exporters et kube-state-metrics collectent les métriques
2. **Prometheus**: Scrape et stocke les métriques
3. **Grafana**: Visualise les métriques depuis Prometheus
4. **Alertmanager**: (si configuré) Gère les alertes

## Haute Disponibilité

"""
        
        if config.get('environment') == 'production':
            content += """
- Multi-nodes pour la redondance
- Prometheus avec retention longue
- Sauvegardes automatiques configurées
"""
        else:
            content += """
- Configuration simple-node (non-production)
- Retention courte pour économiser les ressources
"""
        
        content += """
## Schéma d'Architecture

Voir [ARCHITECTURE_DIAGRAM.txt](ARCHITECTURE_DIAGRAM.txt)

---
*Généré automatiquement*
"""
        
        arch_path = docs_dir / "ARCHITECTURE.md"
        arch_path.write_text(content)
        return arch_path
    
    def _generate_runbook(
        self,
        docs_dir: Path,
        config: Dict[str, Any],
        infra_output: Dict[str, Any],
        monitoring_output: Dict[str, Any]
    ) -> Path:
        """Génère le runbook opérationnel"""
        
        content = f"""# Runbook Opérationnel

## 🔍 Monitoring Quotidien

### Vérifications Journalières

```bash
# Vérifier les nœuds
kubectl get nodes

# Vérifier les pods critiques
kubectl get pods -n kube-system
kubectl get pods -n monitoring

# Vérifier les events
kubectl get events --sort-by='.lastTimestamp'
```

### Métriques à Surveiller

#### Dans Grafana ({monitoring_output.get('grafana_url', 'N/A')})
- **CPU Utilization**: doit rester < 80%
- **Memory Utilization**: doit rester < 85%
- **Disk Usage**: doit rester < 80%
- **Pod Restarts**: max 3 restarts / 1h

#### Dans Prometheus ({monitoring_output.get('prometheus_url', 'N/A')})
- Vérifier que tous les targets sont UP
- Vérifier qu'il n'y a pas de gaps dans les métriques

## 🚨 Procédures d'Urgence

### Nœud Down

```bash
# 1. Identifier le nœud
kubectl get nodes

# 2. Vérifier les logs
kubectl describe node <node-name>

# 3. Drainer le nœud si nécessaire
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 4. Redémarrer ou remplacer le nœud
```

### Pod CrashLooping

```bash
# 1. Identifier le pod
kubectl get pods --all-namespaces | grep -v Running

# 2. Vérifier les logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # Logs du container précédent

# 3. Décrire le pod
kubectl describe pod <pod-name> -n <namespace>

# 4. Redémarrer si nécessaire
kubectl delete pod <pod-name> -n <namespace>
```

### Prometheus Down

```bash
# 1. Vérifier le statut
kubectl get pods -n monitoring -l app=prometheus

# 2. Vérifier les logs
kubectl logs -n monitoring -l app=prometheus

# 3. Redémarrer
kubectl rollout restart deployment/prometheus -n monitoring
```

### Grafana Inaccessible

```bash
# 1. Vérifier le service
kubectl get svc -n monitoring grafana

# 2. Vérifier le pod
kubectl get pods -n monitoring -l app=grafana

# 3. Port-forward manuel
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

## 🔄 Opérations de Maintenance

### Mise à Jour des Composants

#### Prometheus
```bash
# Edit la configuration
kubectl edit configmap prometheus-config -n monitoring

# Reload Prometheus
kubectl exec -n monitoring prometheus-0 -- kill -HUP 1
```

#### Grafana
```bash
# Mettre à jour les dashboards
kubectl apply -f dashboards/

# Redémarrer Grafana
kubectl rollout restart deployment/grafana -n monitoring
```

### Backups

#### Prometheus Data
```bash
# Snapshot des données
kubectl exec -n monitoring prometheus-0 -- curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

#### Grafana Dashboards
```bash
# Export des dashboards via API
# (voir scripts de backup)
```

## 📈 Scaling

### Scale Up des Nœuds

```bash
# Modifier le count dans Terraform
cd {infra_output.get('workspace', 'N/A')}
# Éditer terraform.tfvars: nodes = X
terraform apply
```

### Scale des Pods

```bash
# Scale horizontal
kubectl scale deployment <deployment-name> --replicas=X -n <namespace>

# Ou utiliser HPA
kubectl autoscale deployment <deployment-name> --min=2 --max=10 --cpu-percent=80 -n <namespace>
```

## 📊 Rapports

### Générer un Rapport de Santé

```bash
# Nodes
kubectl get nodes -o wide

# Pods
kubectl get pods --all-namespaces -o wide

# Ressources
kubectl top nodes
kubectl top pods --all-namespaces

# Events récents
kubectl get events --sort-by='.lastTimestamp' | head -20
```

---
*Maintenir ce runbook à jour après chaque changement*
"""
        
        runbook_path = docs_dir / "RUNBOOK.md"
        runbook_path.write_text(content)
        return runbook_path
    
    def _generate_troubleshooting(
        self,
        docs_dir: Path,
        platform: str,
        monitoring_output: Dict[str, Any]
    ) -> Path:
        """Génère le guide de troubleshooting"""
        
        content = f"""# Guide de Troubleshooting

## ❌ Problèmes Courants

### 1. Nœud Not Ready

**Symptômes**:
```bash
kubectl get nodes
NAME     STATUS     ROLES    AGE   VERSION
node-1   NotReady   <none>   1d    v1.28.0
```

**Diagnostic**:
```bash
# Vérifier les détails
kubectl describe node node-1

# Vérifier kubelet
systemctl status kubelet

# Vérifier les logs
journalctl -u kubelet -f
```

**Solutions**:
- Redémarrer kubelet: `systemctl restart kubelet`
- Vérifier la connectivity réseau
- Vérifier les ressources disponibles (disk, memory)

### 2. Pod Pending

**Symptômes**:
```bash
kubectl get pods
NAME    READY   STATUS    RESTARTS   AGE
app-1   0/1     Pending   0          5m
```

**Diagnostic**:
```bash
kubectl describe pod app-1
# Regarder les Events
```

**Causes communes**:
- Ressources insuffisantes (CPU/Memory)
- Node selector ne matche aucun nœud
- PV non disponible
- Taints sur les nœuds

**Solutions**:
- Ajouter des nœuds
- Ajuster les requests/limits
- Vérifier les labels et selectors

### 3. ImagePullBackOff

**Symptômes**:
```bash
NAME    READY   STATUS             RESTARTS   AGE
app-1   0/1     ImagePullBackOff   0          2m
```

**Diagnostic**:
```bash
kubectl describe pod app-1
# Vérifier "Failed to pull image"
```

**Solutions**:
- Vérifier que l'image existe
- Vérifier les credentials (imagePullSecrets)
- Vérifier la connectivity au registry

### 4. CrashLoopBackOff

**Symptômes**:
```bash
NAME    READY   STATUS              RESTARTS   AGE
app-1   0/1     CrashLoopBackOff    5          5m
```

**Diagnostic**:
```bash
# Logs actuels
kubectl logs app-1

# Logs du container précédent
kubectl logs app-1 --previous

# Describe
kubectl describe pod app-1
```

**Solutions communes**:
- Corriger l'erreur applicative  
- Ajuster les probes (liveness/readiness)
- Vérifier les variables d'environnement
- Vérifier les volumes montés

### 5. Prometheus Ne Scrape Pas

**Symptômes**:
- Targets "Down" dans Prometheus
- Métriques manquantes dans Grafana

**Diagnostic**:
```bash
# Vérifier les targets
# Aller sur {monitoring_output.get('prometheus_url', 'N/A')}/targets

# Vérifier les ServiceMonitors
kubectl get servicemonitors -n monitoring

# Logs Prometheus
kubectl logs -n monitoring -l app=prometheus
```

**Solutions**:
- Vérifier les labels des services/pods
- Vérifier les ServiceMonitors
- Vérifier les NetworkPolicies
- Redémarrer Prometheus

### 6. Grafana Dashboard Vide

**Symptômes**:
- Dashboards sans données
- "No data" dans les panels

**Diagnostic**:
```bash
# Vérifier le datasource dans Grafana
# Settings > Data Sources

# Tester dans Prometheus directement
# Query: up{{}}
```

**Solutions**:
- Vérifier que Prometheus scrape les données
- Vérifier les queries PromQL
- Vérifier la time range
- Refresh le datasource

## 🔍 Commandes de Diagnostic

### Informations Cluster
```bash
kubectl cluster-info
kubectl version
kubectl get componentstatuses
```

### État des Ressources
```bash
kubectl get all --all-namespaces
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
kubectl top nodes
kubectl top pods --all-namespaces
```

### Logs
```bash
# Logs d'un pod
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> -f  # Follow
kubectl logs <pod-name> -n <namespace> --previous  # Container précédent

# Logs d'un container spécifique
kubectl logs <pod-name> -c <container-name> -n <namespace>
```

### Exec dans un Pod
```bash
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
```

### Debug
```bash
# Créer un pod de debug
kubectl run debug --image=busybox --rm -it -- /bin/sh

# Debug réseau
kubectl run debug-net --image=nicolaka/netshoot --rm -it -- /bin/sh
```

## 📱 Contacts & Escalade

### Niveau 1 - Self-Service
- Consulter ce guide
- Consulter le [Runbook](RUNBOOK.md)
- Vérifier les logs et métriques

### Niveau 2 - Support
- Contacter l'équipe plateforme
- Fournir: workflow ID, logs, captures Grafana

### Niveau 3 - Escalade
- Incident critique affectant la production
- Perte de données
- Cluster inaccessible

## 🔗 Ressources Utiles

- Kubernetes Documentation: https://kubernetes.io/docs/
- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Documentation: https://grafana.com/docs/

---
*Guide mis à jour régulièrement*
"""
        
        troubleshooting_path = docs_dir / "TROUBLESHOOTING.md"
        troubleshooting_path.write_text(content)
        return troubleshooting_path
    
    def _export_configurations(
        self,
        docs_dir: Path,
        workflow_id: str,
        config: Dict[str, Any],
        infra_output: Dict[str, Any]
    ) -> Path:
        """Exporte les configurations"""
        
        configs_dir = docs_dir / "configs"
        configs_dir.mkdir(exist_ok=True)
        
        # Config complète en JSON
        config_json = configs_dir / "cluster-config.json"
        config_json.write_text(json.dumps(config, indent=2))
        
        # Info Terraform
        terraform_info = {
            "workspace": infra_output.get("workspace"),
            "outputs": infra_output.get("outputs", {}),
        }
        terraform_json = configs_dir / "terraform-info.json"
        terraform_json.write_text(json.dumps(terraform_info, indent=2))
        
        # Export metadata
        metadata = {
            "workflow_id": workflow_id,
            "created_at": datetime.now().isoformat(),
            "platform": config.get("platform"),
            "environment": config.get("environment"),
        }
        metadata_json = configs_dir / "metadata.json"
        metadata_json.write_text(json.dumps(metadata, indent=2))
        
        return configs_dir
    
    def _generate_architecture_diagram(
        self,
        config: Dict[str, Any],
        monitoring_output: Dict[str, Any]
    ) -> str:
        """Génère un diagramme ASCII de l'architecture"""
        
        platform = config.get("platform", "k3s").upper()
        nodes = config.get("nodes", 1)
        
        diagram = f"""
╔════════════════════════════════════════════════════════════════╗
║              ARCHITECTURE - {platform} CLUSTER                      ║
╚════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Server  │  │  Scheduler   │  │   etcd       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼─────────┐
│   WORKER NODE  │  │   WORKER NODE  │  │  WORKER NODE   │
│    (node-1)    │  │    (node-2)    │  │   (node-3)     │
│                │  │                │  │                │
│  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────────┐  │
│  │  Kubelet │  │  │  │  Kubelet │  │  │  │  Kubelet │  │
│  └──────────┘  │  │  └──────────┘  │  │  └──────────┘  │
│  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────────┐  │
│  │Application│  │  │  │Application│  │  │  │Application│  │
│  │   Pods   │  │  │  │   Pods   │  │  │  │   Pods   │  │
│  └──────────┘  │  │  └──────────┘  │  │  └──────────┘  │
└────────────────┘  └────────────────┘  └────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    MONITORING STACK                           │
│  ┌──────────────────────┐    ┌─────────────────────────┐    │
│  │     PROMETHEUS       │◄───│       GRAFANA           │    │
│  │  (Metrics Storage)   │    │   (Visualization)       │    │
│  │                      │    │                         │    │
│  │  • Scrape Interval   │    │  • Dashboards           │    │
│  │  • Alert Rules       │    │  • User Auth            │    │
│  │  • Retention: {config.get('monitoring', {}).get('retention', '15d'):6} │    │  • Datasources          │    │
│  └──────────────────────┘    └─────────────────────────┘    │
│           ▲                            │                      │
│           │ scrapes                    │ queries              │
│           │                            ▼                      │
│  ┌────────┴────────┐         ┌──────────────────┐           │
│  │  ServiceMonitor │         │     Users        │           │
│  │   kube-state    │         └──────────────────┘           │
│  │   node-exporter │                                         │
│  └─────────────────┘                                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      NETWORKING                               │
│  Pod CIDR:     {config.get('networking', {}).get('pod_cidr', '10.244.0.0/16'):20}                       │
│  Service CIDR: {config.get('networking', {}).get('service_cidr', '10.96.0.0/16'):20}                       │
└──────────────────────────────────────────────────────────────┘

Legend:
  ▲ = Data flow up
  ▼ = Data flow down
  ◄─ = Connection
  └─ = Hierarchy
"""
        
        return diagram
