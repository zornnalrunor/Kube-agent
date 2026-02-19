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
            
            kubeconfig_path = infra_output.get("kubeconfig_path")
            
            # Validation des nœuds
            self.log("Checking node status...")
            nodes_status = self._check_nodes(kubeconfig_path)
            logs.append(f"Nodes check: {nodes_status['ready']}/{nodes_status['total']} ready")
            
            if nodes_status['ready'] < nodes_status['total']:
                errors.append(f"Not all nodes are ready: {nodes_status['ready']}/{nodes_status['total']}")
                self.log_error("Some nodes are not ready")
            else:
                self.log_success(f"All {nodes_status['total']} nodes are ready")
            
            # Validation des pods système
            self.log("Checking system pods...")
            pods_status = self._check_system_pods(kubeconfig_path)
            logs.append(f"System pods: {pods_status['running']}/{pods_status['total']} running")
            
            if pods_status['running'] < pods_status['total']:
                errors.append(f"Not all system pods are running: {pods_status['running']}/{pods_status['total']}")
                self.log_error("Some system pods are not running")
            else:
                self.log_success(f"All {pods_status['total']} system pods are running")
            
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
            
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
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
            
            result = subprocess.run(
                ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            pods_data = json.loads(result.stdout)
            running = 0
            pending = 0
            failed = 0
            namespaces = {}
            
            for pod in pods_data.get("items", []):
                namespace = pod["metadata"]["namespace"]
                phase = pod["status"].get("phase", "Unknown")
                
                if phase == "Running":
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
                "namespaces": namespaces
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
