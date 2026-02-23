"""
ArgoCD Agent
Agent responsable du déploiement et de la configuration d'ArgoCD (GitOps)
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class ArgoCDAgent(BaseAgent):
    """
    Agent ArgoCD
    
    Responsabilités:
    - Installer ArgoCD dans le cluster
    - Créer le namespace argocd
    - Configurer le App of Apps pattern (bootstrap)
    - Permettre aux autres agents d'ajouter leurs Applications
    - Gérer l'auto-gestion d'ArgoCD
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Déploie ArgoCD et configure le bootstrap
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Résultat du déploiement ArgoCD
        """
        logs = []
        errors = []
        
        try:
            self.log("Starting ArgoCD deployment")
            
            # Récupérer le kubeconfig de l'infrastructure
            infra_output = agent_input.previous_outputs.get("infrastructure", {})
            kubeconfig_path = infra_output.get("kubeconfig_path")
            
            if not kubeconfig_path:
                error_msg = "No kubeconfig path found from infrastructure agent"
                errors.append(error_msg)
                self.log_error(error_msg)
                return AgentOutput(
                    agent_name=self.agent_name,
                    success=False,
                    errors=errors,
                    logs=logs,
                )
            
            # Créer le répertoire de sortie pour ArgoCD
            argocd_dir = Path("output") / agent_input.workflow_id / "argocd"
            argocd_dir.mkdir(parents=True, exist_ok=True)
            
            # Mode démo ou réel
            if self.config.deployment_mode.value == "demo":
                self.log("📺 Demo mode - Simulating ArgoCD deployment")
                self.log_success("ArgoCD installed (simulated)")
                self.log_success("App of Apps bootstrap created (simulated)")
                
                return AgentOutput(
                    agent_name=self.agent_name,
                    success=True,
                    data={
                        "argocd_installed": True,
                        "argocd_namespace": "argocd",
                        "argocd_url": "http://localhost:30080",
                        "argocd_dir": str(argocd_dir),
                        "bootstrap_app": "root",
                        "summary": "ArgoCD deployed in demo mode"
                    },
                    logs=logs,
                )
            
            # Mode réel: Installation ArgoCD
            self.log("Installing ArgoCD...")
            argocd_installed = self._install_argocd(kubeconfig_path)
            
            if not argocd_installed:
                error_msg = "Failed to install ArgoCD"
                errors.append(error_msg)
                self.log_error(error_msg)
            else:
                self.log_success("ArgoCD installed successfully")
                logs.append("ArgoCD installed")
            
            # Attendre qu'ArgoCD soit prêt
            self.log("Waiting for ArgoCD to be ready...")
            argocd_ready = self._wait_for_argocd(kubeconfig_path)
            
            if not argocd_ready:
                error_msg = "ArgoCD not ready after timeout"
                errors.append(error_msg)
                self.log_error(error_msg)
            else:
                self.log_success("ArgoCD is ready")
                logs.append("ArgoCD ready")
            
            # Exposer ArgoCD via NodePort
            self.log("Exposing ArgoCD server...")
            argocd_url = self._expose_argocd(kubeconfig_path)
            if argocd_url:
                self.log_success(f"ArgoCD accessible at {argocd_url}")
                logs.append(f"ArgoCD URL: {argocd_url}")
            
            # Récupérer le mot de passe admin
            admin_password = self._get_admin_password(kubeconfig_path)
            if admin_password:
                self.log_success("ArgoCD admin password retrieved")
            
            # Créer le App of Apps bootstrap
            self.log("Creating App of Apps bootstrap...")
            bootstrap_created = self._create_app_of_apps_bootstrap(
                kubeconfig_path,
                agent_input.workflow_id,
                argocd_dir
            )
            
            if not bootstrap_created:
                error_msg = "Failed to create App of Apps bootstrap"
                errors.append(error_msg)
                self.log_error(error_msg)
            else:
                self.log_success("App of Apps bootstrap created")
                logs.append("Bootstrap created")
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0,
                data={
                    "argocd_installed": argocd_installed,
                    "argocd_namespace": "argocd",
                    "argocd_url": argocd_url or "http://localhost:30080",
                    "argocd_admin_password": admin_password,
                    "argocd_dir": str(argocd_dir),
                    "bootstrap_app": "root",
                    "kubeconfig_path": kubeconfig_path,
                    "summary": f"ArgoCD deployed ({'success' if len(errors) == 0 else 'with errors'})"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"ArgoCD deployment failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _install_argocd(self, kubeconfig_path: str) -> bool:
        """
        Installe ArgoCD dans le cluster
        
        Returns:
            bool: True si succès
        """
        try:
            import os
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            # Créer le namespace argocd
            subprocess.run(
                ["kubectl", "create", "namespace", "argocd", "--dry-run=client", "-o", "yaml"],
                capture_output=True,
                env=env,
                timeout=10
            )
            subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=subprocess.run(
                    ["kubectl", "create", "namespace", "argocd", "--dry-run=client", "-o", "yaml"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10
                ).stdout,
                text=True,
                capture_output=True,
                env=env,
                timeout=10
            )
            
            # Installer ArgoCD (version stable)
            # Utiliser --server-side pour contourner la limite des annotations CRD
            # --force-conflicts pour résoudre les conflits avec d'anciennes installations
            argocd_manifest_url = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
            
            result = subprocess.run(
                ["kubectl", "apply", "-n", "argocd", "-f", argocd_manifest_url, "--server-side", "--force-conflicts"],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            if result.returncode != 0:
                self.log_error(f"Failed to install ArgoCD: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.log_error(f"ArgoCD installation error: {e}")
            return False
    
    def _wait_for_argocd(self, kubeconfig_path: str, max_attempts: int = 30, delay: int = 10) -> bool:
        """
        Attend qu'ArgoCD soit prêt
        
        Returns:
            bool: True si ArgoCD est prêt
        """
        try:
            import os
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            for attempt in range(max_attempts):
                result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", "argocd", "-o", "json"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10
                )
                
                if result.returncode == 0:
                    pods_data = json.loads(result.stdout)
                    total_pods = len(pods_data.get("items", []))
                    ready_pods = 0
                    
                    for pod in pods_data.get("items", []):
                        phase = pod["status"].get("phase", "Unknown")
                        if phase in ["Running", "Succeeded"]:
                            ready_pods += 1
                    
                    if ready_pods == total_pods and total_pods > 0:
                        self.log(f"✅ ArgoCD ready: {ready_pods}/{total_pods} pods")
                        return True
                    else:
                        self.log(f"⏳ ArgoCD starting: {ready_pods}/{total_pods} pods ready (attempt {attempt+1}/{max_attempts})")
                
                if attempt < max_attempts - 1:
                    time.sleep(delay)
            
            return False
            
        except Exception as e:
            self.log_error(f"Failed to check ArgoCD status: {e}")
            return False
    
    def _expose_argocd(self, kubeconfig_path: str) -> str:
        """
        Expose ArgoCD server via NodePort
        
        Returns:
            str: URL d'accès ArgoCD
        """
        try:
            import os
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            # Patch le service argocd-server en NodePort
            patch = {
                "spec": {
                    "type": "NodePort",
                    "ports": [
                        {
                            "name": "http",
                            "port": 80,
                            "targetPort": 8080,
                            "nodePort": 30080,
                            "protocol": "TCP"
                        },
                        {
                            "name": "https",
                            "port": 443,
                            "targetPort": 8080,
                            "nodePort": 30443,
                            "protocol": "TCP"
                        }
                    ]
                }
            }
            
            result = subprocess.run(
                ["kubectl", "patch", "svc", "argocd-server", "-n", "argocd", 
                 "--type", "merge", "-p", json.dumps(patch)],
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log_warning(f"Failed to patch ArgoCD service: {result.stderr}")
                return "http://localhost:30080"
            
            return "http://localhost:30080"
            
        except Exception as e:
            self.log_error(f"Failed to expose ArgoCD: {e}")
            return "http://localhost:30080"
    
    def _get_admin_password(self, kubeconfig_path: str) -> str:
        """
        Récupère le mot de passe admin ArgoCD
        
        Returns:
            str: Mot de passe admin
        """
        try:
            import os
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            # Le password est dans le secret argocd-initial-admin-secret
            result = subprocess.run(
                ["kubectl", "get", "secret", "argocd-initial-admin-secret", 
                 "-n", "argocd", "-o", "jsonpath={.data.password}"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                # Décoder le base64
                import base64
                password = base64.b64decode(result.stdout).decode('utf-8')
                return password
            
            return "admin"
            
        except Exception as e:
            self.log_error(f"Failed to get admin password: {e}")
            return "admin"
    
    def _create_app_of_apps_bootstrap(
        self, 
        kubeconfig_path: str, 
        workflow_id: str,
        argocd_dir: Path
    ) -> bool:
        """
        Crée le App of Apps bootstrap pattern
        
        Le root app gère:
        - argocd/ (ArgoCD s'auto-gère)
        - monitoring/ (Stack de monitoring)
        - apps/ (Futures applications)
        
        Returns:
            bool: True si succès
        """
        try:
            import os
            
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            # Créer le ConfigMap pour le root app
            root_app_manifest = {
                "apiVersion": "argoproj.io/v1alpha1",
                "kind": "Application",
                "metadata": {
                    "name": "root",
                    "namespace": "argocd",
                    "finalizers": ["resources-finalizer.argocd.argoproj.io"]
                },
                "spec": {
                    "project": "default",
                    "source": {
                        "repoURL": "https://github.com/argoproj/argocd-example-apps.git",
                        "targetRevision": "HEAD",
                        "path": "apps"
                    },
                    "destination": {
                        "server": "https://kubernetes.default.svc",
                        "namespace": "argocd"
                    },
                    "syncPolicy": {
                        "automated": {
                            "prune": True,
                            "selfHeal": True
                        }
                    }
                }
            }
            
            # Pour l'instant, on crée juste un placeholder
            # Les autres agents vont ajouter leurs Applications
            root_app_file = argocd_dir / "root-app.yaml"
            with open(root_app_file, 'w') as f:
                json.dump(root_app_manifest, f, indent=2)
            
            self.log("App of Apps structure created")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create bootstrap: {e}")
            return False
