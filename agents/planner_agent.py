"""
Planner Agent
Agent de planification intelligente pour analyser les besoins et générer un plan d'exécution
"""
import json
from typing import Any, Dict, List

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class PlannerAgent(BaseAgent):
    """
    Agent de planification
    
    Responsabilités:
    - Analyser les requirements utilisateur
    - Déterminer les ressources nécessaires
    - Générer un plan d'exécution détaillé
    - Optimiser la configuration selon les best practices
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Génère un plan d'exécution basé sur les requirements
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Plan d'exécution détaillé
        """
        logs = []
        errors = []
        
        try:
            context = agent_input.context
            platform = context.get("platform", "k3s")
            environment = context.get("environment", "development")
            
            self.log(f"Analyzing requirements for {platform} ({environment})")
            
            # Utiliser l'IA pour optimiser la configuration
            optimized_config = self._optimize_configuration(context)
            logs.append(f"Configuration optimized for {platform}")
            
            # Générer le plan d'exécution
            execution_plan = self._generate_execution_plan(
                platform,
                environment,
                optimized_config
            )
            logs.append("Execution plan generated")
            
            # Estimer les ressources et le temps
            estimates = self._estimate_resources(execution_plan)
            logs.append(f"Estimated time: {estimates['time']} minutes")
            
            # Validation du plan
            validation = self._validate_plan(execution_plan)
            if not validation["valid"]:
                errors.extend(validation["errors"])
            
            self.log_success("Planning completed successfully")
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0,
                data={
                    "optimized_config": optimized_config,
                    "execution_plan": execution_plan,
                    "estimates": estimates,
                    "validation": validation,
                    "summary": f"Plan for {platform} cluster with {optimized_config.get('nodes', 1)} nodes"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Planning failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _optimize_configuration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utilise l'IA pour optimiser la configuration selon les best practices
        
        Args:
            context: Configuration de base
            
        Returns:
            Dict: Configuration optimisée
        """
        platform = context.get("platform", "k3s")
        environment = context.get("environment", "development")
        nodes = context.get("nodes", 1)
        
        # Prompt pour l'IA
        prompt = f"""
You are a Kubernetes infrastructure expert. Optimize the following configuration for a {platform} cluster in {environment} environment.

Current configuration:
{json.dumps(context, indent=2)}

Provide an optimized configuration considering:
1. Resource sizing (CPU, memory)
2. High availability requirements
3. Security best practices
4. Cost optimization
5. Monitoring and observability

Return ONLY a JSON object with the optimized configuration.
"""
        
        try:
            # Obtenir les recommendations de l'IA
            response = self.prompt_llm(prompt)
            
            # Parser la réponse JSON
            # En cas d'erreur, utiliser des valeurs par défaut intelligentes
            try:
                optimized = json.loads(response)
            except json.JSONDecodeError:
                # Fallback sur des valeurs optimisées par défaut
                optimized = self._get_default_optimized_config(platform, environment, nodes)
        except Exception as e:
            self.log_warning(f"AI optimization failed, using defaults: {str(e)}")
            optimized = self._get_default_optimized_config(platform, environment, nodes)
        
        # S'assurer que les valeurs de base sont présentes
        optimized.setdefault("platform", platform)
        optimized.setdefault("environment", environment)
        optimized.setdefault("nodes", nodes)
        
        return optimized
    
    def _get_default_optimized_config(
        self,
        platform: str,
        environment: str,
        nodes: int
    ) -> Dict[str, Any]:
        """
        Retourne une configuration optimisée par défaut
        
        Args:
            platform: Plateforme cible
            environment: Environnement
            nodes: Nombre de nœuds
            
        Returns:
            Dict: Configuration optimisée
        """
        # Configuration de base selon l'environnement
        env_configs = {
            "development": {
                "instance_type": "t3.medium" if platform == "eks" else "Standard_B2s",
                "disk_size": 50,
                "memory": "4Gi",
                "cpu": 2,
            },
            "staging": {
                "instance_type": "t3.large" if platform == "eks" else "Standard_B2ms",
                "disk_size": 100,
                "memory": "8Gi",
                "cpu": 2,
            },
            "production": {
                "instance_type": "t3.xlarge" if platform == "eks" else "Standard_D2s_v3",
                "disk_size": 200,
                "memory": "16Gi",
                "cpu": 4,
            },
        }
        
        base_config = env_configs.get(environment, env_configs["development"])
        
        config = {
            "platform": platform,
            "environment": environment,
            "nodes": max(3, nodes) if environment == "production" else nodes,
            "kubernetes_version": "1.28",
            "resources": base_config,
            "networking": {
                "pod_cidr": "10.244.0.0/16",
                "service_cidr": "10.96.0.0/16",
            },
            "monitoring": {
                "enabled": True,
                "retention": "15d" if environment == "production" else "7d",
                "alerting": environment == "production",
            },
            "security": {
                "rbac_enabled": True,
                "network_policies": environment in ["staging", "production"],
                "pod_security_policy": environment == "production",
            },
            "addons": {
                "metrics_server": True,
                "ingress_nginx": True,
                "cert_manager": environment in ["staging", "production"],
            }
        }
        
        # Ajustements spécifiques par plateforme
        if platform == "k3s":
            config["k3s_config"] = {
                "disable": ["traefik"],  # On utilisera nginx
                "write_kubeconfig_mode": "644",
            }
        elif platform == "eks":
            config["eks_config"] = {
                "region": "us-east-1",
                "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
            }
        elif platform == "aks":
            config["aks_config"] = {
                "location": "eastus",
                "sku_tier": "Standard" if environment == "production" else "Free",
            }
        
        return config
    
    def _generate_execution_plan(
        self,
        platform: str,
        environment: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Génère le plan d'exécution détaillé
        
        Args:
            platform: Plateforme
            environment: Environnement
            config: Configuration optimisée
            
        Returns:
            Dict: Plan d'exécution
        """
        steps = []
        
        # Étape 1: Infrastructure
        steps.append({
            "name": "infrastructure",
            "description": f"Provisioning {platform} cluster",
            "tasks": [
                "Initialize Terraform",
                "Create network resources",
                "Provision compute instances",
                "Configure Kubernetes",
                "Setup storage classes",
            ],
            "estimated_time": 5 if platform == "k3s" else 15,
        })
        
        # Étape 2: Monitoring
        if config.get("monitoring", {}).get("enabled"):
            steps.append({
                "name": "monitoring",
                "description": "Setup monitoring stack",
                "tasks": [
                    "Deploy Prometheus Operator",
                    "Configure Prometheus",
                    "Deploy Grafana",
                    "Import dashboards",
                    "Setup alerts" if config["monitoring"].get("alerting") else None,
                ],
                "estimated_time": 3,
            })
        
        # Étape 3: Addons
        addons = config.get("addons", {})
        addon_tasks = []
        for addon, enabled in addons.items():
            if enabled:
                addon_tasks.append(f"Install {addon}")
        
        if addon_tasks:
            steps.append({
                "name": "addons",
                "description": "Install cluster addons",
                "tasks": addon_tasks,
                "estimated_time": 2,
            })
        
        # Étape 4: Validation
        steps.append({
            "name": "validation",
            "description": "Validate cluster",
            "tasks": [
                "Check node status",
                "Verify pod health",
                "Test monitoring endpoints",
                "Validate networking",
            ],
            "estimated_time": 2,
        })
        
        return {
            "platform": platform,
            "environment": environment,
            "steps": steps,
            "total_steps": len(steps),
        }
    
    def _estimate_resources(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estime les ressources nécessaires et le temps d'exécution
        
        Args:
            execution_plan: Plan d'exécution
            
        Returns:
            Dict: Estimations
        """
        total_time = sum(step["estimated_time"] for step in execution_plan["steps"])
        
        return {
            "time": total_time,
            "time_unit": "minutes",
            "steps": execution_plan["total_steps"],
            "complexity": "low" if total_time < 10 else "medium" if total_time < 20 else "high",
        }
    
    def _validate_plan(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide le plan d'exécution
        
        Args:
            execution_plan: Plan à valider
            
        Returns:
            Dict: Résultat de validation
        """
        errors = []
        warnings = []
        
        # Vérifier que le plan a des étapes
        if not execution_plan.get("steps"):
            errors.append("Execution plan has no steps")
        
        # Vérifier que chaque étape a des tasks
        for step in execution_plan.get("steps", []):
            tasks = [t for t in step.get("tasks", []) if t is not None]
            if not tasks:
                warnings.append(f"Step '{step['name']}' has no tasks")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
