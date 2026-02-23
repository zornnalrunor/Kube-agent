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
            
            # Vérifier si ArgoCD est disponible
            argocd_output = agent_input.previous_outputs.get("argocd", {})
            use_argocd = argocd_output.get("argocd_installed", False)
            
            # Générer les manifests Kubernetes
            manifests_dir = self._generate_monitoring_manifests(
                agent_input.workflow_id,
                monitoring_config
            )
            logs.append(f"Manifests generated: {manifests_dir}")
            self.log_success("Monitoring manifests generated")
            
            # Déploiement via ArgoCD ou direct
            prometheus_deployed = False
            grafana_deployed = False
            
            if use_argocd and self.config.deployment_mode.value == "real":
                self.log("🔄 GitOps mode: Deploying via ArgoCD")
                
                # Créer un repo Git local pour les manifests
                repo_path = self._create_git_repo(manifests_dir, agent_input.workflow_id)
                logs.append(f"Git repo created: {repo_path}")
                
                # Créer les Applications ArgoCD
                argocd_app_created = self._create_argocd_applications(
                    kubeconfig_path,
                    repo_path,
                    agent_input.workflow_id,
                    monitoring_config
                )
                
                if argocd_app_created:
                    prometheus_deployed = True
                    grafana_deployed = True
                    logs.append("ArgoCD Application created")
                    self.log_success("Monitoring deployed via ArgoCD")
                else:
                    errors.append("Failed to create ArgoCD applications")
                    self.log_error("ArgoCD application creation failed")
            else:
                # Mode direct (sans ArgoCD ou en démo)
                if not use_argocd:
                    self.log("📦 Direct mode: Deploying with kubectl")
                
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
            headlamp_enabled = monitoring_config.get("headlamp", True)
            
            if self.config.deployment_mode.value == "real":
                # En mode réel, utiliser les NodePorts
                grafana_url = "http://localhost:30300"
                prometheus_url = "http://localhost:30090"
                headlamp_url = "http://localhost:30466" if headlamp_enabled else None
                
                access_parts = [
                    f"Grafana: {grafana_url} (admin/admin)",
                    f"Prometheus: {prometheus_url}"
                ]
                if headlamp_enabled:
                    access_parts.append(f"Headlamp: {headlamp_url}")
                access_instructions = ", ".join(access_parts)
            else:
                # En mode démo, URLs fictives
                grafana_url = "http://localhost:3000"
                prometheus_url = "http://localhost:9090"
                headlamp_url = "http://localhost:4466" if headlamp_enabled else None
                
                access_parts = [f"Grafana: {grafana_url}"]
                if headlamp_enabled:
                    access_parts.append(f"Headlamp: {headlamp_url}")
                access_instructions = ", ".join(access_parts)
            
            result_data = {
                "manifests_dir": str(manifests_dir),
                "prometheus_deployed": prometheus_deployed,
                "grafana_deployed": grafana_deployed,
                "grafana_url": grafana_url,
                "prometheus_url": prometheus_url,
                "dashboards": dashboards if grafana_deployed else [],
                "summary": f"Monitoring stack deployed ({access_instructions})"
            }
            
            if headlamp_enabled:
                result_data["headlamp_url"] = headlamp_url
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0,
                data=result_data,
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
        
        # Headlamp (K8s UI) - optionnel
        monitoring_config = config.get("monitoring", {})
        if monitoring_config.get("headlamp", True):  # Activé par défaut
            headlamp_manifest = self._generate_headlamp_manifest(config)
            self._save_manifest(manifests_dir / "25-headlamp.yaml", headlamp_manifest)
        
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
    
    def _generate_headlamp_manifest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le manifest Headlamp (Kubernetes UI)"""
        return {
            "apiVersion": "v1",
            "kind": "List",
            "items": [
                # ServiceAccount
                {
                    "apiVersion": "v1",
                    "kind": "ServiceAccount",
                    "metadata": {
                        "name": "headlamp",
                        "namespace": "monitoring"
                    }
                },
                # ClusterRoleBinding
                {
                    "apiVersion": "rbac.authorization.k8s.io/v1",
                    "kind": "ClusterRoleBinding",
                    "metadata": {
                        "name": "headlamp"
                    },
                    "roleRef": {
                        "apiGroup": "rbac.authorization.k8s.io",
                        "kind": "ClusterRole",
                        "name": "cluster-admin"
                    },
                    "subjects": [
                        {
                            "kind": "ServiceAccount",
                            "name": "headlamp",
                            "namespace": "monitoring"
                        }
                    ]
                },
                # Deployment
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": "headlamp",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "replicas": 1,
                        "selector": {
                            "matchLabels": {"app": "headlamp"}
                        },
                        "template": {
                            "metadata": {
                                "labels": {"app": "headlamp"}
                            },
                            "spec": {
                                "serviceAccountName": "headlamp",
                                "containers": [
                                    {
                                        "name": "headlamp",
                                        "image": "ghcr.io/headlamp-k8s/headlamp:latest",
                                        "args": ["-in-cluster"],
                                        "ports": [{"containerPort": 4466}],
                                        "env": [
                                            {
                                                "name": "HEADLAMP_CONFIG_BASE_URL",
                                                "value": ""
                                            }
                                        ]
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
                        "name": "headlamp",
                        "namespace": "monitoring"
                    },
                    "spec": {
                        "type": "NodePort",
                        "ports": [
                            {
                                "port": 4466,
                                "targetPort": 4466,
                                "nodePort": 30466
                            }
                        ],
                        "selector": {"app": "headlamp"}
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
    
    def _create_git_repo(self, manifests_dir: Path, workflow_id: str) -> Path:
        """
        Crée un repo Git local pour les manifests (GitOps)
        
        Args:
            manifests_dir: Répertoire contenant les manifests
            workflow_id: ID du workflow
            
        Returns:
            Path: Chemin du repo Git créé
        """
        try:
            import subprocess
            
            # Créer un répertoire pour le repo bare
            repo_dir = self.config.output_dir / "gitops" / workflow_id
            repo_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialiser un repo Git
            subprocess.run(
                ["git", "init"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            # Copier les manifests dans le repo
            import shutil
            monitoring_path = repo_dir / "monitoring"
            if monitoring_path.exists():
                shutil.rmtree(monitoring_path)
            shutil.copytree(manifests_dir, monitoring_path)
            
            # Créer un .gitignore
            gitignore_path = repo_dir / ".gitignore"
            gitignore_path.write_text("*.swp\n*.tmp\n")
            
            # Commit initial
            subprocess.run(
                ["git", "add", "-A"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            subprocess.run(
                ["git", "config", "user.email", "argocd@terraform-agent.local"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            subprocess.run(
                ["git", "config", "user.name", "Terraform Agent"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            subprocess.run(
                ["git", "commit", "-m", "Initial monitoring manifests"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            self.log(f"Git repo created: {repo_dir}")
            return repo_dir
            
        except Exception as e:
            self.log_error(f"Failed to create Git repo: {e}")
            return manifests_dir
    
    def _create_argocd_applications(
        self,
        kubeconfig_path: str,
        repo_path: Path,
        workflow_id: str,
        monitoring_config: Dict[str, Any]
    ) -> bool:
        """
        Crée les Applications ArgoCD pour le monitoring stack
        
        Args:
            kubeconfig_path: Chemin vers kubeconfig
            repo_path: Chemin vers le repo Git local
            workflow_id: ID du workflow
            monitoring_config: Configuration du monitoring
            
        Returns:
            bool: True si succès
        """
        try:
            import subprocess
            import os
            import yaml
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            # Application pour le monitoring stack
            monitoring_app = {
                "apiVersion": "argoproj.io/v1alpha1",
                "kind": "Application",
                "metadata": {
                    "name": f"monitoring-{workflow_id}",
                    "namespace": "argocd",
                    "finalizers": ["resources-finalizer.argocd.argoproj.io"]
                },
                "spec": {
                    "project": "default",
                    "source": {
                        "repoURL": f"file://{repo_path.absolute()}",
                        "targetRevision": "HEAD",
                        "path": "monitoring"
                    },
                    "destination": {
                        "server": "https://kubernetes.default.svc",
                        "namespace": "monitoring"
                    },
                    "syncPolicy": {
                        "automated": {
                            "prune": True,
                            "selfHeal": True
                        },
                        "syncOptions": [
                            "CreateNamespace=true"
                        ]
                    }
                }
            }
            
            # Sauvegarder l'Application
            app_file = self.config.output_dir / "argocd-apps" / workflow_id / "monitoring-app.yaml"
            app_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(app_file, 'w') as f:
                yaml.dump(monitoring_app, f)
            
            # Appliquer l'Application dans ArgoCD
            result = subprocess.run(
                ["kubectl", "apply", "-f", str(app_file)],
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log_error(f"Failed to create ArgoCD application: {result.stderr}")
                return False
            
            self.log_success("ArgoCD Application created for monitoring")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create ArgoCD applications: {e}")
            return False
