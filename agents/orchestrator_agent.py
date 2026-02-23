"""
Orchestrator Agent
Agent principal qui coordonne tous les autres agents
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.panel import Panel
from rich.table import Table

from core.agent_base import AgentInput, AgentOutput, BaseAgent
from core.config import Config
from core.state_manager import StateManager, WorkflowState, WorkflowStatus


class OrchestratorAgent(BaseAgent):
    """
    Agent orchestrateur principal
    
    Responsabilités:
    - Coordonner l'exécution de tous les agents
    - Gérer le workflow global
    - Gérer les erreurs et les rollbacks
    - Fournir un rapport final
    """
    
    def __init__(self, config: Config, state_manager: StateManager):
        super().__init__(config, state_manager)
        self.agents_registry = {}
    
    def register_agent(self, agent_name: str, agent: BaseAgent) -> None:
        """
        Enregistre un agent dans l'orchestrateur
        
        Args:
            agent_name: Nom de l'agent
            agent: Instance de l'agent
        """
        self.agents_registry[agent_name] = agent
        self.log(f"Agent registered: {agent_name}")
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Exécute l'orchestration complète du workflow
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Résultat de l'orchestration
        """
        logs = []
        errors = []
        outputs = {}
        
        try:
            # Afficher le banner
            self._display_banner(agent_input.context)
            
            # Workflow steps
            workflow_steps = [
                ("planner", "Planification du déploiement"),
                ("infrastructure", "Provisioning de l'infrastructure"),
                ("argocd", "Déploiement d'ArgoCD (GitOps)"),
                ("monitoring", "Configuration du monitoring"),
                ("validation", "Validation du cluster"),
                ("documentation", "Génération de la documentation"),
            ]
            
            # Exécuter chaque étape
            for agent_name, description in workflow_steps:
                if agent_name not in self.agents_registry:
                    error_msg = f"Agent '{agent_name}' not registered"
                    errors.append(error_msg)
                    self.log_error(error_msg)
                    continue
                
                # Afficher l'étape
                self.console.print(f"\n[bold cyan]📋 Étape: {description}[/bold cyan]")
                
                # Préparer l'input pour l'agent
                step_input = AgentInput(
                    workflow_id=agent_input.workflow_id,
                    context=agent_input.context,
                    previous_outputs=outputs,
                )
                
                # Mettre à jour le statut du workflow
                self._update_workflow_status(
                    agent_input.workflow_id,
                    self._get_status_for_agent(agent_name)
                )
                
                # Exécuter l'agent
                agent = self.agents_registry[agent_name]
                result = agent.run(step_input)
                
                # Collecter les résultats
                logs.extend(result.logs)
                outputs[agent_name] = result.data
                
                if not result.success:
                    errors.extend(result.errors)
                    self.log_error(f"Agent '{agent_name}' failed")
                    
                    # Décider si on continue ou on arrête
                    if self._is_critical_agent(agent_name):
                        self.log_error("Critical agent failed, stopping workflow")
                        break
                    else:
                        self.log_warning("Non-critical agent failed, continuing...")
                else:
                    self.log_success(f"{description} terminée")
            
            # Afficher le résumé
            success = len(errors) == 0
            self._display_summary(success, outputs, errors)
            
            # Mettre à jour le workflow final
            final_status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
            self._update_workflow_status(agent_input.workflow_id, final_status)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=success,
                data=outputs,
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Orchestration failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            # Mettre à jour le workflow
            self._update_workflow_status(
                agent_input.workflow_id,
                WorkflowStatus.FAILED
            )
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                data=outputs,
                errors=errors,
                logs=logs,
            )
    
    def _display_banner(self, context: Dict[str, Any]) -> None:
        """Affiche le banner de démarrage"""
        platform = context.get("platform", "unknown")
        environment = context.get("environment", "unknown")
        
        banner = f"""
[bold cyan]🚀 Terraform K8s Agent - Orchestrator[/bold cyan]

[bold]Configuration:[/bold]
  • Platform: [green]{platform}[/green]
  • Environment: [yellow]{environment}[/yellow]
  • Monitoring: [blue]{context.get('monitoring', {}).get('enabled', False)}[/blue]
        """
        
        self.console.print(Panel(banner.strip(), border_style="cyan"))
    
    def _display_summary(
        self,
        success: bool,
        outputs: Dict[str, Any],
        errors: List[str]
    ) -> None:
        """Affiche le résumé du déploiement"""
        status_icon = "✅" if success else "❌"
        status_text = "SUCCÈS" if success else "ÉCHEC"
        status_color = "green" if success else "red"
        
        # Table des résultats
        table = Table(title=f"\n{status_icon} Résumé du Déploiement - {status_text}")
        table.add_column("Agent", style="cyan")
        table.add_column("Statut", style="dim")
        table.add_column("Détails", style="dim")
        
        for agent_name, data in outputs.items():
            status = "✓" if data.get("success", True) else "✗"
            details = data.get("summary", "N/A")
            table.add_row(agent_name, status, str(details))
        
        self.console.print(table)
        
        # Afficher les erreurs
        if errors:
            self.console.print(f"\n[bold red]Erreurs ({len(errors)}):[/bold red]")
            for error in errors:
                self.console.print(f"  [red]• {error}[/red]")
        
        # Afficher les accès
        if success:
            self.console.print(f"\n[bold green]🎉 Déploiement terminé![/bold green]")
            self.console.print(f"\n[bold]Accès:[/bold]")
            
            # ArgoCD
            if "argocd" in outputs:
                argocd_data = outputs["argocd"]
                if argocd_data.get("argocd_url"):
                    argocd_url = argocd_data['argocd_url']
                    argocd_pwd = argocd_data.get('argocd_admin_password', 'admin')
                    self.console.print(f"  🔄 ArgoCD: {argocd_url} (admin/{argocd_pwd})")
            
            # Monitoring
            if "monitoring" in outputs:
                monitoring_data = outputs["monitoring"]
                if monitoring_data.get("grafana_url"):
                    self.console.print(f"  📊 Grafana: {monitoring_data['grafana_url']} (admin/admin)")
                if monitoring_data.get("prometheus_url"):
                    self.console.print(f"  📈 Prometheus: {monitoring_data['prometheus_url']}")
                if monitoring_data.get("headlamp_url"):
                    self.console.print(f"  🎛️  Headlamp: {monitoring_data['headlamp_url']}")
            
            # Cluster info
            if "validation" in outputs:
                validation = outputs["validation"]
                self.console.print(f"\n[bold]Cluster:[/bold]")
                self.console.print(f"  Nodes: {validation.get('nodes_ready', 'N/A')}")
                self.console.print(f"  Pods: {validation.get('pods_running', 'N/A')}")
    
    def _get_status_for_agent(self, agent_name: str) -> WorkflowStatus:
        """Retourne le statut du workflow pour un agent donné"""
        status_map = {
            "planner": WorkflowStatus.PLANNING,
            "infrastructure": WorkflowStatus.PROVISIONING,
            "argocd": WorkflowStatus.CONFIGURING,
            "monitoring": WorkflowStatus.CONFIGURING,
            "validation": WorkflowStatus.VALIDATING,
            "documentation": WorkflowStatus.DOCUMENTING,
        }
        return status_map.get(agent_name, WorkflowStatus.PENDING)
    
    def _is_critical_agent(self, agent_name: str) -> bool:
        """Détermine si un agent est critique"""
        critical_agents = {"planner", "infrastructure"}
        return agent_name in critical_agents
    
    def _update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus
    ) -> None:
        """Met à jour le statut du workflow"""
        workflow = self.state_manager.get_workflow(workflow_id)
        if workflow:
            workflow.status = status
            self.state_manager.update_workflow(workflow)
    
    def create_workflow(
        self,
        platform: str,
        environment: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Crée un nouveau workflow
        
        Args:
            platform: Plateforme (k3s, eks, aks)
            environment: Environnement (dev, staging, prod)
            config: Configuration du cluster
            
        Returns:
            str: ID du workflow créé
        """
        workflow_id = f"{platform}-{environment}-{uuid.uuid4().hex[:8]}"
        
        workflow = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            platform=platform,
            environment=environment,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            config=config,
        )
        
        self.state_manager.create_workflow(workflow)
        self.log_success(f"Workflow created: {workflow_id}")
        
        return workflow_id
    
    def run_workflow(
        self,
        platform: str,
        environment: str,
        config: Dict[str, Any]
    ) -> AgentOutput:
        """
        Crée et exécute un workflow complet
        
        Args:
            platform: Plateforme cible
            environment: Environnement
            config: Configuration
            
        Returns:
            AgentOutput: Résultat du workflow
        """
        # Créer le workflow
        workflow_id = self.create_workflow(platform, environment, config)
        
        # Préparer l'input
        agent_input = AgentInput(
            workflow_id=workflow_id,
            context={
                "platform": platform,
                "environment": environment,
                **config
            }
        )
        
        # Exécuter le workflow
        return self.run(agent_input)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Récupère le statut d'un workflow
        
        Args:
            workflow_id: ID du workflow
            
        Returns:
            WorkflowState: État du workflow ou None
        """
        return self.state_manager.get_workflow(workflow_id)
