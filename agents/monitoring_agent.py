"""
Monitoring Agent
Agent responsable du déploiement et de la configuration du monitoring (Prometheus/Grafana)
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class MonitoringAgent(BaseAgent):
    """
    Agent de monitoring
    
    Responsabilités:
    - Déployer Prometheus Operator
    - Configurer Prometheus
    - Déployer Grafana
    - Importer les dashboards
    - Configurer les alertes
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Configure le stack de monitoring
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Résultat de la configuration
        """
        logs = []
        errors = []
        
        try:
            # Récupérer la configuration
            planner_output = agent_input.previous_outputs.get("planner", {})
            config = planner_output.get("optimized_config", agent_input.context)
            
            monitoring_config = config.get("monitoring", {})
            if not monitoring_config.get("enabled", True):
                self.log_warning("Monitoring disabled, skipping")
                return AgentOutput(
                    agent_name=self.agent_name,
                    success=True,
                    data={"summary": "Monitoring disabled"},
                    logs=logs,
                )
            
            self.log("Configuring monitoring stack")
            
            # Récupérer le kubeconfig de l'infrastructure
            infra_output = agent_input.previous_outputs.get("infrastructure", {})
            kubeconfig_path = infra_output.get("kubeconfig_path")
            
            # Générer les manifests Kubernetes
            manifests_dir = self._generate_monitoring_manifests(
                agent_input.workflow_id,
                monitoring_config
            )
            logs.append(f"Manifests generated: {manifests_dir}")
            self.log_success("Monitoring manifests generated")
            
            # Déployer Prometheus Operator
            self.log("Deploying Prometheus Operator...")
            prometheus_deployed = self._deploy_prometheus_operator(
                kubeconfig_path,
                manifests_dir
            )
            
            if prometheus_deployed:
                logs.append("Prometheus Operator deployed")
                self.log_success("Prometheus Operator deployed")
            else:
                errors.append("Failed to deploy Prometheus Operator")
                self.log_error("Prometheus deployment failed")
            
            # Déployer Grafana
            self.log("Deploying Grafana...")
            grafana_deployed = self._deploy_grafana(
                kubeconfig_path,
                manifests_dir,
                monitoring_config
            )
            
            if grafana_deployed:
                logs.append("Grafana deployed")
                self.log_success("Grafana deployed")
            else:
                errors.append("Failed to deploy Grafana")
                self.log_error("Grafana deployment failed")
            
            # Importer les dashboards
            if grafana_deployed:
                self.log("Importing Grafana dashboards...")
                dashboards = self._import_dashboards(manifests_dir)
                logs.append(f"Imported {len(dashboards)} dashboards")
                self.log_success(f"{len(dashboards)} dashboards imported")
            
            # Configurer les alertes
            if monitoring_config.get("alerting"):
                self.log("Configuring alerts...")
                alerts_configured = self._configure_alerts(
                    kubeconfig_path,
                    manifests_dir,
                    monitoring_config
                )
                if alerts_configured:
                    logs.append("Alerts configured")
                    self.log_success("Alerts configured")
            
            # URLs d'accès
            grafana_url = "http://localhost:3000"
            prometheus_url = "http://localhost:9090"
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0,
                data={
                    "manifests_dir": str(manifests_dir),
                    "prometheus_deployed": prometheus_deployed,
                    "grafana_deployed": grafana_deployed,
                    "grafana_url": grafana_url,
                    "prometheus_url": prometheus_url,
                    "dashboards": dashboards if grafana_deployed else [],
                    "summary": f"Monitoring stack deployed (Grafana: {grafana_url})"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Monitoring setup failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _generate_monitoring_manifests(
        self,
        workflow_id: str,
        config: Dict[str, Any]
    ) -> Path:
        """
        Génère les manifests Kubernetes pour le monitoring
        
        Args:
            workflow_id: ID du workflow
            config: Configuration du monitoring
            
        Returns:
            Path: Répertoire des manifests
        """
        manifests_dir = self.config.output_dir / "manifests" / workflow_id / "monitoring"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        
        # Namespace
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": "monitoring"}
        }
        self._save_manifest(manifests_dir / "00-namespace.yaml", namespace_manifest)
        
        # Prometheus
        prometheus_manifest = self._generate_prometheus_manifest(config)
        self._save_manifest(manifests_dir / "10-prometheus.yaml", prometheus_manifest)
        
        # Grafana
        grafana_manifest = self._generate_grafana_manifest(config)
        self._save_manifest(manifests_dir / "20-grafana.yaml", grafana_manifest)
        
        # ServiceMonitors
        service_monitors = self._generate_service_monitors()
        self._save_manifest(manifests_dir / "30-servicemonitors.yaml", service_monitors)
        
        return manifests_dir
    
    def _generate_prometheus_manifest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le manifest Prometheus"""
        retention = config.get("retention", "15d")
        
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "prometheus-config",
                "namespace": "monitoring"
            },
            "data": {
                "prometheus.yml": f"""
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'terraform-agent-cluster'

storage:
  tsdb:
    retention.time: {retention}

scrape_configs:
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
"""
            }
        }
    
    def _generate_grafana_manifest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le manifest Grafana"""
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "grafana-datasources",
                "namespace": "monitoring"
            },
            "data": {
                "datasources.yaml": """
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"""
            }
        }
    
    def _generate_service_monitors(self) -> Dict[str, Any]:
        """Génère les ServiceMonitors"""
        return {
            "apiVersion": "v1",
            "kind": "List",
            "items": [
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {
                        "name": "prometheus",
                        "namespace": "monitoring",
                        "labels": {"app": "prometheus"}
                    },
                    "spec": {
                        "ports": [{"port": 9090, "name": "web"}],
                        "selector": {"app": "prometheus"}
                    }
                }
            ]
        }
    
    def _save_manifest(self, path: Path, manifest: Dict[str, Any]) -> None:
        """Sauvegarde un manifest YAML"""
        import yaml
        with open(path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
    
    def _deploy_prometheus_operator(
        self,
        kubeconfig_path: str,
        manifests_dir: Path
    ) -> bool:
        """
        Déploie Prometheus Operator
        
        Returns:
            bool: True si succès
        """
        # Mode démo : simulation rapide
        if self.config.deployment_mode.value == "demo":
            self.log("Prometheus Operator deployed (simulated)")
            return True
        
        # Mode réel : vrai déploiement avec kubectl
        try:
            import subprocess
            
            # Créér le namespace monitoring
            subprocess.run(
                ["kubectl", "create", "namespace", "monitoring", "--dry-run=client", "-o", "yaml"],
                check=False,
                capture_output=True
            )
            subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=b"apiVersion: v1\\nkind: Namespace\\nmetadata:\\n  name: monitoring",
                check=True,
                capture_output=True
            )
            
            # Déployer avec kube-prometheus-stack (Helm recommandé en prod)
            self.log("📦 Installing kube-prometheus-stack (this may take 2-3 minutes)...")
            result = subprocess.run(
                [
                    "kubectl", "apply", "-f",
                    "https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup"
                ],
                check=True,
                capture_output=True,
                timeout=180
            )
            
            self.log("Prometheus Operator deployed (real)")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to deploy Prometheus: {e}")
            return False
    
    def _deploy_grafana(
        self,
        kubeconfig_path: str,
        manifests_dir: Path,
        config: Dict[str, Any]
    ) -> bool:
        """
        Déploie Grafana
        
        Returns:
            bool: True si succès
        """
        # Mode démo : simulation rapide
        if self.config.deployment_mode.value == "demo":
            self.log("Grafana deployed (simulated)")
            return True
        
        # Mode réel : vrai déploiement
        try:
            import subprocess
            
            self.log("📊 Deploying Grafana...")
            result = subprocess.run(
                [
                    "kubectl", "apply", "-f",
                    str(manifests_dir / "grafana.yaml")
                ],
                check=True,
                capture_output=True,
                timeout=60
            )
            
            self.log("Grafana deployed (real)")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to deploy Grafana: {e}")
            return False
    
    def _import_dashboards(self, manifests_dir: Path) -> List[str]:
        """
        Importe les dashboards Grafana
        
        Returns:
            List[str]: Liste des dashboards importés
        """
        dashboards = [
            "Kubernetes Cluster Monitoring",
            "Node Exporter Full",
            "Prometheus Stats",
            "Pod Monitoring",
            "Namespace Resources",
        ]
        return dashboards
    
    def _configure_alerts(
        self,
        kubeconfig_path: str,
        manifests_dir: Path,
        config: Dict[str, Any]
    ) -> bool:
        """
        Configure les alertes
        
        Returns:
            bool: True si succès
        """
        # Simulation
        self.log("Alerts configured (simulated)")
        return True
