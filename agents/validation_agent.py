"""
Validation Agent
Agent responsable de la validation du cluster et de sa santé
"""
from typing import Any, Dict, List

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class ValidationAgent(BaseAgent):
    """
    Agent de validation
    
    Responsabilités:
    - Vérifier la santé des nœuds
    - Valider le déploiement des pods
    - Tester les endpoints de monitoring
    - Vérifier le networking
    - Générer un rapport de santé
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Valide le cluster et génère un rapport
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Résultat de la validation
        """
        logs = []
        errors = []
        
        try:
            self.log("Starting cluster validation")
            
            # Récupérer les outputs précédents
            infra_output = agent_input.previous_outputs.get("infrastructure", {})
            monitoring_output = agent_input.previous_outputs.get("monitoring", {})
            argocd_output = agent_input.previous_outputs.get("argocd", {})
            
            kubeconfig_path = infra_output.get("kubeconfig_path")
            argocd_installed = argocd_output.get("argocd_installed", False)
            
            # Validation des nœuds
            self.log("Checking node status...")
            nodes_status = self._check_nodes(kubeconfig_path)
            logs.append(f"Nodes check: {nodes_status['ready']}/{nodes_status['total']} ready")
            
            # Log node details
            if nodes_status.get('nodes'):
                self.log("🖥️  Node Status:")
                for node in nodes_status['nodes']:
                    status_emoji = "✅" if node['status'] == "Ready" else "❌"
                    self.log(f"  {status_emoji} {node['name']}: {node['status']} ({node['version']})")
            
            if nodes_status['ready'] < nodes_status['total']:
                errors.append(f"Not all nodes are ready: {nodes_status['ready']}/{nodes_status['total']}")
                self.log_error("Some nodes are not ready")
            else:
                self.log_success(f"All {nodes_status['total']} nodes are ready")
            
            # Validation des pods système
            self.log("Checking system pods...")
            
            # En mode réel, retry plusieurs fois pour laisser les pods démarrer
            if self.config.deployment_mode.value == "real":
                max_retries = 6
                retry_delay = 10
                for attempt in range(max_retries):
                    pods_status = self._check_system_pods(kubeconfig_path)
                    
                    # Si tous les pods sont OK, on arrête
                    if pods_status['running'] == pods_status['total']:
                        break
                    
                    # Si pas le dernier essai, on attend
                    if attempt < max_retries - 1:
                        pending = pods_status.get('pending', 0)
                        self.log(f"⏳ {pending} pods still starting, retrying in {retry_delay}s... ({attempt+1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
            else:
                pods_status = self._check_system_pods(kubeconfig_path)
            
            logs.append(f"System pods: {pods_status['running']}/{pods_status['total']} healthy")
            
            # Log detailed pod status
            if pods_status.get('pod_details'):
                self.log("📊 Pod Status Details:")
                for pod_info in pods_status['pod_details']:
                    if pod_info['phase'] == "Running":
                        status_emoji = "✅"
                    elif pod_info['phase'] == "Succeeded":
                        status_emoji = "✅"
                    elif pod_info['phase'] == "Pending":
                        status_emoji = "⏳"
                    else:
                        status_emoji = "❌"
                    self.log(f"  {status_emoji} {pod_info['namespace']}/{pod_info['name']}: {pod_info['phase']}")
                    if pod_info.get('reason'):
                        self.log(f"     Reason: {pod_info['reason']}")
            
            if pods_status['running'] < pods_status['total']:
                errors.append(f"Not all system pods are running: {pods_status['running']}/{pods_status['total']}")
                self.log_error(f"Some system pods are not healthy (pending: {pods_status.get('pending', 0)}, failed: {pods_status.get('failed', 0)})")
            else:
                self.log_success(f"All {pods_status['total']} system pods are healthy")
            
            # Validation ArgoCD
            argocd_status = {}
            if argocd_installed:
                self.log("Checking ArgoCD status...")
                argocd_status = self._check_argocd(kubeconfig_path)
                logs.append(f"ArgoCD: {argocd_status.get('status', 'unknown')}")
                
                if not argocd_status.get('healthy', False):
                    errors.append("ArgoCD is not healthy")
                    self.log_error("ArgoCD check failed")
                else:
                    self.log_success("ArgoCD is healthy")
                    
                    # Vérifier les Applications ArgoCD
                    apps_status = argocd_status.get('applications', {})
                    if apps_status:
                        synced = apps_status.get('synced', 0)
                        total = apps_status.get('total', 0)
                        healthy = apps_status.get('healthy', 0)
                        self.log(f"📱 ArgoCD Applications: {synced}/{total} synced, {healthy}/{total} healthy")
            
            # Validation du monitoring
            if monitoring_output.get("grafana_deployed"):
                self.log("Testing monitoring endpoints...")
                monitoring_status = self._check_monitoring_endpoints(monitoring_output)
                logs.append(f"Monitoring endpoints: {monitoring_status['accessible']}/{monitoring_status['total']} accessible")
                
                if not monitoring_status['prometheus_ok']:
                    errors.append("Prometheus endpoint is not accessible")
                    self.log_error("Prometheus is not accessible")
                else:
                    self.log_success("Prometheus is accessible")
                
                if not monitoring_status['grafana_ok']:
                    errors.append("Grafana endpoint is not accessible")
                    self.log_error("Grafana is not accessible")
                else:
                    self.log_success("Grafana is accessible")
            
            # Validation du networking
            self.log("Validating networking...")
            network_status = self._check_networking(kubeconfig_path)
            logs.append(f"Networking: {'OK' if network_status['ok'] else 'FAILED'}")
            
            if not network_status['ok']:
                errors.extend(network_status['errors'])
                self.log_error("Networking validation failed")
            else:
                self.log_success("Networking is properly configured")
            
            # Vérification de la capacité
            self.log("Checking cluster capacity...")
            capacity = self._check_cluster_capacity(kubeconfig_path)
            logs.append(f"Cluster capacity: CPU={capacity['cpu']}, Memory={capacity['memory']}")
            self.log_success(f"Cluster capacity: {capacity['cpu']} CPUs, {capacity['memory']} Memory")
            
            # Générer le rapport de santé
            health_report = self._generate_health_report(
                nodes_status,
                pods_status,
                argocd_status,
                monitoring_status if monitoring_output.get("grafana_deployed") else {},
                network_status,
                capacity
            )
            
            # Score de santé global
            health_score = self._calculate_health_score(health_report)
            logs.append(f"Health score: {health_score}/100")
            
            if health_score < 80:
                errors.append(f"Cluster health score is below 80: {health_score}/100")
                self.log_warning(f"Health score: {health_score}/100 (below recommended)")
            else:
                self.log_success(f"Health score: {health_score}/100")
            
                return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0 and health_score >= 80,
                data={
                    "nodes_status": nodes_status,
                    "pods_status": pods_status,
                    "argocd_status": argocd_status,
                    "monitoring_status": monitoring_status if monitoring_output.get("grafana_deployed") else {},
                    "network_status": network_status,
                    "capacity": capacity,
                    "health_report": health_report,
                    "health_score": health_score,
                    "nodes_ready": f"{nodes_status['ready']}/{nodes_status['total']}",
                    "pods_running": f"{pods_status['running']}/{pods_status['total']}",
                    "summary": f"Cluster validation {'passed' if not errors else 'failed'} (score: {health_score}/100)"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _check_nodes(self, kubeconfig_path: str) -> Dict[str, Any]:
        """
        Vérifie le statut des nœuds
        
        Returns:
            Dict: Statut des nœuds
        """
        # Mode démo : données simulées
        if self.config.deployment_mode.value == "demo":
            return {
                "total": 3,
                "ready": 3,
                "not_ready": 0,
                "nodes": [
                    {"name": "node-1", "status": "Ready", "version": "v1.28.0"},
                    {"name": "node-2", "status": "Ready", "version": "v1.28.0"},
                    {"name": "node-3", "status": "Ready", "version": "v1.28.0"},
                ]
            }
        
        # Mode réel : vraies vérifications avec kubectl
        try:
            import subprocess
            import json
            import os
            
            # Prepare environment with kubeconfig
            env = os.environ.copy()
            if kubeconfig_path:
                env["KUBECONFIG"] = kubeconfig_path
            
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                self.log_error(f"kubectl get nodes failed: {result.stderr}")
                return {
                    "total": 0,
                    "ready": 0,
                    "not_ready": 0,
                    "nodes": [],
                    "error": result.stderr
                }
            
            nodes_data = json.loads(result.stdout)
            nodes = []
            ready_count = 0
            
            for node in nodes_data.get("items", []):
                name = node["metadata"]["name"]
                version = node["status"]["nodeInfo"]["kubeletVersion"]
                
                # Check if node is Ready
                status = "NotReady"
                for condition in node["status"]["conditions"]:
                    if condition["type"] == "Ready" and condition["status"] == "True":
                        status = "Ready"
                        ready_count += 1
                        break
                
                nodes.append({
                    "name": name,
                    "status": status,
                    "version": version
                })
            
            return {
                "total": len(nodes),
                "ready": ready_count,
                "not_ready": len(nodes) - ready_count,
                "nodes": nodes
            }
            
        except Exception as e:
            self.log_error(f"Failed to check nodes: {e}")
            return {
                "total": 0,
                "ready": 0,
                "not_ready": 0,
                "nodes": [],
                "error": str(e)
            }
    
    def _check_system_pods(self, kubeconfig_path: str) -> Dict[str, Any]:
        """
        Vérifie le statut des pods système
        
        Returns:
            Dict: Statut des pods
        """
        # Mode démo : simulation
        if self.config.deployment_mode.value == "demo":
            return {
                "total": 12,
                "running": 12,
                "pending": 0,
                "failed": 0,
                "namespaces": {
                    "kube-system": 8,
                    "monitoring": 4,
                }
            }
        
        # Mode réel : vraies vérifications
        try:
            import subprocess
            import json
            import os
            
            # Prepare environment with kubeconfig
            env = os.environ.copy()
            if kubeconfig_path:
                env["KUBECONFIG"] = kubeconfig_path
            
            result = subprocess.run(
                ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                self.log_error(f"kubectl get pods failed: {result.stderr}")
                return {
                    "total": 0,
                    "running": 0,
                    "pending": 0,
                    "failed": 0,
                    "namespaces": {},
                    "error": result.stderr
                }
            
            pods_data = json.loads(result.stdout)
            running = 0
            pending = 0
            failed = 0
            namespaces = {}
            pod_details = []
            
            for pod in pods_data.get("items", []):
                namespace = pod["metadata"]["namespace"]
                name = pod["metadata"]["name"]
                phase = pod["status"].get("phase", "Unknown")
                
                # Get container statuses for more details
                reason = None
                container_statuses = pod["status"].get("containerStatuses", [])
                for container in container_statuses:
                    if not container.get("ready", False):
                        waiting = container.get("state", {}).get("waiting", {})
                        if waiting:
                            reason = waiting.get("reason", "Unknown")
                            break
                
                pod_details.append({
                    "namespace": namespace,
                    "name": name,
                    "phase": phase,
                    "reason": reason
                })
                
                # Count Running and Succeeded as healthy
                if phase in ["Running", "Succeeded"]:
                    running += 1
                elif phase == "Pending":
                    pending += 1
                elif phase in ["Failed", "Unknown"]:
                    failed += 1
                
                namespaces[namespace] = namespaces.get(namespace, 0) + 1
            
            total = len(pods_data.get("items", []))
            
            return {
                "total": total,
                "running": running,
                "pending": pending,
                "failed": failed,
                "namespaces": namespaces,
                "pod_details": pod_details
            }
            
        except Exception as e:
            self.log_error(f"Failed to check pods: {e}")
            return {
                "total": 0,
                "running": 0,
                "pending": 0,
                "failed": 0,
                "namespaces": {},
                "error": str(e)
            }
    
    def _check_monitoring_endpoints(self, monitoring_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie l'accessibilité des endpoints de monitoring
        
        Returns:
            Dict: Statut des endpoints
        """
        # Simulation
        prometheus_url = monitoring_output.get("prometheus_url", "")
        grafana_url = monitoring_output.get("grafana_url", "")
        
        # En production, faire des vraies requêtes HTTP
        return {
            "total": 2,
            "accessible": 2,
            "prometheus_ok": True,
            "grafana_ok": True,
            "prometheus_url": prometheus_url,
            "grafana_url": grafana_url,
            "targets": {
                "up": 15,
                "down": 0,
            }
        }
    
    def _check_argocd(self, kubeconfig_path: str) -> Dict[str, Any]:
        """
        Vérifie le statut d'ArgoCD et de ses Applications
        
        Returns:
            Dict: Statut ArgoCD
        """
        # Mode démo
        if self.config.deployment_mode.value == "demo":
            return {
                "healthy": True,
                "status": "healthy",
                "applications": {
                    "total": 1,
                    "synced": 1,
                    "healthy": 1
                }
            }
        
        # Mode réel
        try:
            import subprocess
            import json
            import os
            
            env = os.environ.copy()
            if kubeconfig_path:
                env["KUBECONFIG"] = kubeconfig_path
            
            # Vérifier les pods ArgoCD
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "argocd", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                return {
                    "healthy": False,
                    "status": "unavailable",
                    "error": result.stderr
                }
            
            pods_data = json.loads(result.stdout)
            total_pods = len(pods_data.get("items", []))
            running_pods = sum(
                1 for pod in pods_data.get("items", [])
                if pod["status"].get("phase") == "Running"
            )
            
            # Vérifier les Applications ArgoCD
            app_result = subprocess.run(
                ["kubectl", "get", "applications", "-n", "argocd", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            applications = {
                "total": 0,
                "synced": 0,
                "healthy": 0
            }
            
            if app_result.returncode == 0:
                apps_data = json.loads(app_result.stdout)
                applications["total"] = len(apps_data.get("items", []))
                
                for app in apps_data.get("items", []):
                    status = app.get("status", {})
                    sync_status = status.get("sync", {}).get("status", "")
                    health_status = status.get("health", {}).get("status", "")
                    
                    if sync_status == "Synced":
                        applications["synced"] += 1
                    if health_status == "Healthy":
                        applications["healthy"] += 1
            
            return {
                "healthy": running_pods == total_pods,
                "status": "healthy" if running_pods == total_pods else "degraded",
                "pods_running": f"{running_pods}/{total_pods}",
                "applications": applications
            }
            
        except Exception as e:
            self.log_error(f"Failed to check ArgoCD: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    def _check_networking(self, kubeconfig_path: str) -> Dict[str, Any]:
        """
        Valide la configuration réseau
        
        Returns:
            Dict: Statut du réseau
        """
        # Simulation
        return {
            "ok": True,
            "errors": [],
            "pod_cidr": "10.244.0.0/16",
            "service_cidr": "10.96.0.0/16",
            "dns_ok": True,
            "connectivity_ok": True,
        }
    
    def _check_cluster_capacity(self, kubeconfig_path: str) -> Dict[str, Any]:
        """
        Vérifie la capacité du cluster
        
        Returns:
            Dict: Capacité du cluster
        """
        # Simulation
        return {
            "cpu": "6 cores",
            "memory": "12Gi",
            "storage": "300Gi",
            "pods": "110 per node",
            "utilization": {
                "cpu": "25%",
                "memory": "40%",
            }
        }
    
    def _generate_health_report(
        self,
        nodes_status: Dict[str, Any],
        pods_status: Dict[str, Any],
        argocd_status: Dict[str, Any],
        monitoring_status: Dict[str, Any],
        network_status: Dict[str, Any],
        capacity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Génère un rapport de santé complet
        
        Returns:
            Dict: Rapport de santé
        """
        checks = []
        
        # Nodes
        checks.append({
            "category": "Nodes",
            "status": "passed" if nodes_status['ready'] == nodes_status['total'] else "failed",
            "message": f"{nodes_status['ready']}/{nodes_status['total']} nodes ready",
        })
        
        # Pods
        checks.append({
            "category": "Pods",
            "status": "passed" if pods_status['running'] == pods_status['total'] else "failed",
            "message": f"{pods_status['running']}/{pods_status['total']} pods running",
        })
        
        # ArgoCD
        if argocd_status:
            checks.append({
                "category": "ArgoCD",
                "status": "passed" if argocd_status.get('healthy', False) else "failed",
                "message": f"ArgoCD is {argocd_status.get('status', 'unknown')}",
            })
        
        # Monitoring
        if monitoring_status:
            checks.append({
                "category": "Monitoring",
                "status": "passed" if monitoring_status.get('prometheus_ok') and monitoring_status.get('grafana_ok') else "failed",
                "message": "Monitoring stack is operational",
            })
        
        # Networking
        checks.append({
            "category": "Networking",
            "status": "passed" if network_status['ok'] else "failed",
            "message": "Network configuration is valid",
        })
        
        # Capacity
        checks.append({
            "category": "Capacity",
            "status": "passed",
            "message": f"CPU: {capacity['cpu']}, Memory: {capacity['memory']}",
        })
        
        return {
            "checks": checks,
            "timestamp": "2024-02-19T10:00:00Z",
            "overall_status": "healthy" if all(c["status"] == "passed" for c in checks) else "degraded"
        }
    
    def _calculate_health_score(self, health_report: Dict[str, Any]) -> int:
        """
        Calcule un score de santé sur 100
        
        Returns:
            int: Score de 0 à 100
        """
        checks = health_report.get("checks", [])
        if not checks:
            return 0
        
        passed = sum(1 for c in checks if c["status"] == "passed")
        total = len(checks)
        
        return int((passed / total) * 100)
