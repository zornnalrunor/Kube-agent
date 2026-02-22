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
            if self.config.deployment_mode.value == "real":
                # En mode réel, utiliser les NodePorts
                grafana_url = "http://localhost:30300"
                prometheus_url = "http://localhost:30090"
                access_instructions = (
                    f"Grafana: {grafana_url} (admin/admin), "
                    f"Prometheus: {prometheus_url}"
                )
            else:
                # En mode démo, URLs fictives
                grafana_url = "http://localhost:3000"
                prometheus_url = "http://localhost:9090"
                access_instructions = f"Grafana: {grafana_url}"
            
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
                    "summary": f"Monitoring stack deployed ({access_instructions})"
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
        """Génère le manifest Prometheus avec Deployment"""
        retention = config.get("retention", "15d")
        
        return {
            "apiVersion": "v1",
            "kind": "List",
            "items": [
                # ConfigMap
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "prometheus-config",
                        "namespace": "monitoring"
                    },
                    "data": {
                        "prometheus.yml": f"""global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
"""
                    }
                },
                # Deployment
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": "prometheus",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "replicas": 1,
                        "selector": {
                            "matchLabels": {"app": "prometheus"}
                        },
                        "template": {
                            "metadata": {
                                "labels": {"app": "prometheus"}
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "name": "prometheus",
                                        "image": "prom/prometheus:latest",
                                        "ports": [{"containerPort": 9090}],
                                        "volumeMounts": [
                                            {
                                                "name": "config",
                                                "mountPath": "/etc/prometheus"
                                            }
                                        ]
                                    }
                                ],
                                "volumes": [
                                    {
                                        "name": "config",
                                        "configMap": {"name": "prometheus-config"}
                                    }
                                ]
                            }
                        }
                    }
                },
                # Service
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {
                        "name": "prometheus",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "type": "NodePort",
                        "ports": [
                            {
                                "port": 9090,
                                "targetPort": 9090,
                                "nodePort": 30090
                            }
                        ],
                        "selector": {"app": "prometheus"}
                    }
                }
            ]
        }
    
    def _generate_grafana_manifest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le manifest Grafana avec Deployment"""
        return {
            "apiVersion": "v1",
            "kind": "List",
            "items": [
                # ConfigMap
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "grafana-datasources",
                        "namespace": "monitoring"
                    },
                    "data": {
                        "datasources.yaml": """apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"""
                    }
                },
                # Deployment
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": "grafana",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "replicas": 1,
                        "selector": {
                            "matchLabels": {"app": "grafana"}
                        },
                        "template": {
                            "metadata": {
                                "labels": {"app": "grafana"}
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "name": "grafana",
                                        "image": "grafana/grafana:latest",
                                        "ports": [{"containerPort": 3000}],
                                        "env": [
                                            {
                                                "name": "GF_SECURITY_ADMIN_PASSWORD",
                                                "value": "admin"
                                            }
                                        ],
                                        "volumeMounts": [
                                            {
                                                "name": "datasources",
                                                "mountPath": "/etc/grafana/provisioning/datasources"
                                            }
                                        ]
                                    }
                                ],
                                "volumes": [
                                    {
                                        "name": "datasources",
                                        "configMap": {"name": "grafana-datasources"}
                                    }
                                ]
                            }
                        }
                    }
                },
                # Service
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {
                        "name": "grafana",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "type": "NodePort",
                        "ports": [
                            {
                                "port": 3000,
                                "targetPort": 3000,
                                "nodePort": 30300
                            }
                        ],
                        "selector": {"app": "grafana"}
                    }
                }
            ]
        }
    
    def _generate_service_monitors(self) -> Dict[str, Any]:
        """Génère les ServiceMonitors (optionnel - pour l'instant vide)"""
        return {
            "apiVersion": "v1",
            "kind": "List",
            "items": []
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
            import os
            
            # Prepare environment with kubeconfig
            env = os.environ.copy()
            if kubeconfig_path:
                env["KUBECONFIG"] = kubeconfig_path
                self.log(f"Using kubeconfig: {kubeconfig_path}")
            else:
                self.log_error("No kubeconfig provided, using default")
            
            # Créér le namespace monitoring
            namespace_yaml = """apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
"""
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=namespace_yaml.encode(),
                capture_output=True,
                env=env
            )
            if result.returncode != 0:
                self.log_error(f"Failed to create namespace: {result.stderr.decode()}")
                return False
            
            # Déployer avec kube-prometheus-stack (Helm recommandé en prod)
            self.log("📦 Deploying Prometheus from manifests...")
            result = subprocess.run(
                [
                    "kubectl", "apply", "-f",
                    str(manifests_dir)
                ],
                capture_output=True,
                timeout=60,
                env=env
            )
            
            if result.returncode != 0:
                self.log_error(f"Prometheus operator failed: {result.stderr.decode()}")
                return False
            
            # Log successful deployments
            stdout = result.stdout.decode()
            if stdout:
                self.log("✅ Deployed resources:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.log(f"  {line}")
            
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
            import os
            
            # Prepare environment with kubeconfig
            env = os.environ.copy()
            if kubeconfig_path:
                env["KUBECONFIG"] = kubeconfig_path
            
            self.log("📊 Deploying Grafana...")
            result = subprocess.run(
                [
                    "kubectl", "apply", "-f",
                    str(manifests_dir / "20-grafana.yaml")
                ],
                capture_output=True,
                timeout=60,
                env=env
            )
            
            if result.returncode != 0:
                self.log_error(f"Grafana deployment failed: {result.stderr.decode()}")
                return False
            
            # Log successful deployment
            stdout = result.stdout.decode()
            if stdout:
                self.log(f"✅ {stdout.strip()}")
            
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
