"""
Agent Base Module
Classe de base abstraite pour tous les agents
"""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from rich.console import Console

from core.config import Config
from core.llm_provider import LLMProviderFactory
from core.state_manager import (
    AgentExecution,
    AgentStatus,
    StateManager,
    WorkflowState,
)

console = Console()


class AgentInput(BaseModel):
    """Input standardisé pour un agent"""
    workflow_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    previous_outputs: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Output standardisé d'un agent"""
    agent_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    execution_time: float = 0.0


class BaseAgent(ABC):
    """
    Classe de base abstraite pour tous les agents du système
    
    Chaque agent doit implémenter la méthode `execute()` qui contient
    la logique principale de l'agent.
    """
    
    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        llm: Optional[BaseLLM] = None,
    ):
        self.config = config
        self.state_manager = state_manager
        self.llm = llm or LLMProviderFactory.get_llm(config)
        self.agent_name = self.__class__.__name__
        self.console = console
    
    @abstractmethod
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Méthode principale à implémenter par chaque agent
        
        Args:
            agent_input: Input standardisé contenant le context et les outputs précédents
            
        Returns:
            AgentOutput: Output standardisé de l'agent
        """
        pass
    
    def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Wrapper autour de execute() qui gère le logging et le state management
        
        Args:
            agent_input: Input pour l'agent
            
        Returns:
            AgentOutput: Output de l'agent
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Log début
        self._log_start(execution_id, agent_input.workflow_id)
        
        # Créer l'enregistrement d'exécution
        execution = AgentExecution(
            execution_id=execution_id,
            workflow_id=agent_input.workflow_id,
            agent_name=self.agent_name,
            status=AgentStatus.RUNNING,
            started_at=start_time,
            input_data=agent_input.model_dump(),
            output_data={},
            logs=[],
        )
        self.state_manager.create_execution(execution)
        
        try:
            # Exécuter l'agent
            output = self.execute(agent_input)
            
            # Calculer le temps d'exécution
            end_time = datetime.utcnow()
            output.execution_time = (end_time - start_time).total_seconds()
            
            # Mettre à jour l'exécution
            execution.status = AgentStatus.SUCCESS if output.success else AgentStatus.FAILED
            execution.completed_at = end_time
            execution.output_data = output.model_dump()
            execution.logs = output.logs
            execution.error_message = "\n".join(output.errors) if output.errors else None
            
            self.state_manager.update_execution(execution)
            
            # Log fin
            self._log_end(execution_id, output)
            
            return output
            
        except Exception as e:
            # Gérer les erreurs
            end_time = datetime.utcnow()
            error_msg = f"Agent {self.agent_name} failed: {str(e)}"
            
            execution.status = AgentStatus.FAILED
            execution.completed_at = end_time
            execution.error_message = error_msg
            self.state_manager.update_execution(execution)
            
            self._log_error(execution_id, str(e))
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=[error_msg],
                execution_time=(end_time - start_time).total_seconds(),
            )
    
    def _log_start(self, execution_id: str, workflow_id: str) -> None:
        """Log le démarrage de l'agent"""
        self.console.print(
            f"\n[bold cyan]🤖 {self.agent_name}[/bold cyan] "
            f"[dim](Execution: {execution_id[:8]}...)[/dim]"
        )
    
    def _log_end(self, execution_id: str, output: AgentOutput) -> None:
        """Log la fin de l'agent"""
        status_icon = "✅" if output.success else "❌"
        status_color = "green" if output.success else "red"
        
        self.console.print(
            f"{status_icon} [bold {status_color}]{self.agent_name}[/bold {status_color}] "
            f"completed in {output.execution_time:.2f}s"
        )
        
        # Log des erreurs
        if output.errors:
            for error in output.errors:
                self.console.print(f"  [red]Error: {error}[/red]")
    
    def _log_error(self, execution_id: str, error: str) -> None:
        """Log une erreur"""
        self.console.print(
            f"[bold red]❌ {self.agent_name} failed[/bold red]\n"
            f"  [red]{error}[/red]"
        )
    
    def log(self, message: str, style: str = "dim") -> None:
        """
        Log un message avec style
        
        Args:
            message: Message à logger
            style: Style Rich (ex: 'bold', 'dim', 'red', etc.)
        """
        self.console.print(f"  [{style}]{message}[/{style}]")
    
    def log_success(self, message: str) -> None:
        """Log un message de succès"""
        self.console.print(f"  [green]✓ {message}[/green]")
    
    def log_error(self, message: str) -> None:
        """Log un message d'erreur"""
        self.console.print(f"  [red]✗ {message}[/red]")
    
    def log_warning(self, message: str) -> None:
        """Log un avertissement"""
        self.console.print(f"  [yellow]⚠ {message}[/yellow]")
    
    def log_info(self, message: str) -> None:
        """Log une information"""
        self.console.print(f"  [blue]ℹ {message}[/blue]")
    
    def prompt_llm(self, prompt: str) -> str:
        """
        Envoie un prompt au LLM et retourne la réponse
        
        Args:
            prompt: Le prompt à envoyer
            
        Returns:
            str: La réponse du LLM
        """
        try:
            response = self.llm.invoke(prompt)
            # Gérer différents types de retour selon le provider
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            self.log_error(f"LLM error: {str(e)}")
            raise
    
    def update_workflow_state(
        self,
        workflow_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
    ) -> None:
        """
        Met à jour l'état du workflow
        
        Args:
            workflow_id: ID du workflow
            outputs: Nouveaux outputs à ajouter
            errors: Nouvelles erreurs à ajouter
        """
        workflow = self.state_manager.get_workflow(workflow_id)
        if workflow:
            if outputs:
                workflow.outputs.update(outputs)
            if errors:
                workflow.errors.extend(errors)
            self.state_manager.update_workflow(workflow)
