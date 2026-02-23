#!/usr/bin/env python3
"""
Terraform K8s Agent - Main Entry Point
Système agentique IA pour l'automatisation de clusters Kubernetes
"""
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from agents.argocd_agent import ArgoCDAgent
from agents.documentation_agent import DocumentationAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.monitoring_agent import MonitoringAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.planner_agent import PlannerAgent
from agents.validation_agent import ValidationAgent
from core.config import Config, Environment, Platform, DeploymentMode
from core.state_manager import StateManager

app = typer.Typer(
    name="terraform-k8s-agent",
    help="Système agentique IA pour l'automatisation de clusters Kubernetes",
    add_completion=False,
)
console = Console()


def create_system(config: Optional[Config] = None) -> OrchestratorAgent:
    """
    Crée et configure le système d'agents
    
    Args:
        config: Configuration optionnelle
        
    Returns:
        OrchestratorAgent: Orchestrateur configuré
    """
    # Configuration
    cfg = config or Config()
    
    # State manager
    state_manager = StateManager(cfg)
    
    # Créer les agents
    planner = PlannerAgent(cfg, state_manager)
    infrastructure = InfrastructureAgent(cfg, state_manager)
    argocd = ArgoCDAgent(cfg, state_manager)
    monitoring = MonitoringAgent(cfg, state_manager)
    validation = ValidationAgent(cfg, state_manager)
    documentation = DocumentationAgent(cfg, state_manager)
    
    # Orchestrateur
    orchestrator = OrchestratorAgent(cfg, state_manager)
    
    # Enregistrer les agents
    orchestrator.register_agent("planner", planner)
    orchestrator.register_agent("infrastructure", infrastructure)
    orchestrator.register_agent("argocd", argocd)
    orchestrator.register_agent("monitoring", monitoring)
    orchestrator.register_agent("validation", validation)
    orchestrator.register_agent("documentation", documentation)
    
    return orchestrator


def display_banner() -> None:
    """Affiche le banner de l'application"""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        🤖 TERRAFORM K8S AGENT - AI-Powered Automation        ║
║                                                               ║
║     Automatisation complète de clusters Kubernetes avec      ║
║              monitoring intégré (Prometheus/Grafana)          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)


@app.command()
def interactive() -> None:
    """
    Mode interactif guidé par l'IA
    """
    display_banner()
    
    console.print("\n[bold green]Bienvenue dans le mode interactif![/bold green]")
    console.print("Je vais vous guider pour créer votre cluster Kubernetes.\n")
    
    # Choix de la plateforme
    console.print("[bold]Quelle plateforme souhaitez-vous utiliser?[/bold]")
    console.print("  1. K3s (local/VMs) - Parfait pour dev/test")
    console.print("  2. AWS EKS - Production cloud AWS")
    console.print("  3. Azure AKS - Production cloud Azure")
    
    platform_choice = IntPrompt.ask(
        "\nVotre choix",
        choices=["1", "2", "3"],
        default="1"
    )
    
    platform_map = {
        1: "k3s",
        2: "eks",
        3: "aks",
    }
    platform = platform_map[platform_choice]
    
    # Environnement
    console.print("\n[bold]Quel environnement?[/bold]")
    console.print("  1. Development")
    console.print("  2. Staging")
    console.print("  3. Production")
    
    env_choice = IntPrompt.ask(
        "\nVotre choix",
        choices=["1", "2", "3"],
        default="1"
    )
    
    env_map = {
        1: "development",
        2: "staging",
        3: "production",
    }
    environment = env_map[env_choice]
    
    # Nombre de nœuds
    min_nodes = 3 if environment == "production" else 1
    nodes = IntPrompt.ask(
        f"\n[bold]Combien de nœuds?[/bold] (min: {min_nodes})",
        default=min_nodes
    )
    
    if nodes < min_nodes:
        nodes = min_nodes
        console.print(f"[yellow]Ajusté à {min_nodes} nœuds (minimum pour {environment})[/yellow]")
    
    # Monitoring
    monitoring_enabled = Confirm.ask(
        "\n[bold]Activer le monitoring (Prometheus/Grafana)?[/bold]",
        default=True
    )
    
    # Headlamp (UI Kubernetes)
    headlamp_enabled = Confirm.ask(
        "\n[bold]Activer Headlamp (interface web pour Kubernetes)?[/bold]",
        default=True
    )
    
    # Mode de déploiement
    console.print("\n[bold]Quel mode de déploiement?[/bold]")
    console.print("  1. 📺 Démo rapide (simulation)")
    console.print("  2. 🚀 Déploiement réel (installe vraiment K3s)")
    
    deployment_mode_choice = IntPrompt.ask(
        "\nVotre choix",
        choices=["1", "2"],
        default="1"
    )
    
    deployment_mode = "demo" if deployment_mode_choice == 1 else "real"
    
    if deployment_mode == "real":
        console.print("\n[yellow]⚠️  Mode réel activé - va requérir:[/yellow]")
        console.print("   • Accès sudo pour installer K3s")
        console.print("   • ~2-5 minutes de déploiement")
        console.print("   • Téléchargement de ~500MB")
        if not Confirm.ask("\n[bold]Continuer?[/bold]", default=True):
            console.print("[yellow]Retour au mode démo.[/yellow]")
            deployment_mode = "demo"
    
    # Récapitulatif
    console.print(Panel.fit(
        f"""[bold]Récapitulatif de votre configuration:[/bold]

• Plateforme: [cyan]{platform.upper()}[/cyan]
• Environnement: [yellow]{environment}[/yellow]
• Nœuds: [green]{nodes}[/green]
• Monitoring: [blue]{'Activé' if monitoring_enabled else 'Désactivé'}[/blue]
• Mode: [magenta]{'🚀 Déploiement réel' if deployment_mode == 'real' else '📺 Démo (simulation)'}[/magenta]
        """,
        title="Configuration",
        border_style="green"
    ))
    
    # Confirmation
    if not Confirm.ask("\n[bold]Lancer le déploiement?[/bold]", default=True):
        console.print("[yellow]Déploiement annulé.[/yellow]")
        return
    
    # Créer la configuration
    config_dict = {
        "platform": platform,
        "environment": environment,
        "nodes": nodes,
        "deployment_mode": deployment_mode,
        "monitoring": {
            "enabled": monitoring_enabled,
            "headlamp": headlamp_enabled,
            "retention": "15d" if environment == "production" else "7d",
        }
    }
    
    # Configurer le mode de déploiement
    os.environ["DEPLOYMENT_MODE"] = deployment_mode
    
    # Créer le système d'agents
    orchestrator = create_system()
    
    # Exécuter le workflow
    console.print("\n[bold cyan]🚀 Démarrage du workflow...[/bold cyan]\n")
    result = orchestrator.run_workflow(platform, environment, config_dict)
    
    # Résultat final
    if result.success:
        console.print("\n[bold green]✅ Déploiement terminé avec succès![/bold green]")
    else:
        console.print("\n[bold red]❌ Le déploiement a échoué.[/bold red]")
        if result.errors:
            console.print("\n[bold red]Erreurs:[/bold red]")
            for error in result.errors:
                console.print(f"  • {error}")


@app.command()
def create(
    platform: str = typer.Option("k3s", "--platform", "-p", help="Platform (k3s, eks, aks)"),
    environment: str = typer.Option("development", "--environment", "-e", help="Environment"),
    nodes: int = typer.Option(3, "--nodes", "-n", help="Number of nodes"),
    monitoring: bool = typer.Option(True, "--monitoring/--no-monitoring", help="Enable monitoring"),
    headlamp: bool = typer.Option(True, "--headlamp/--no-headlamp", help="Enable Headlamp (Kubernetes UI)"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Cloud region (for EKS/AKS)"),
    real_deployment: bool = typer.Option(False, "--real-deployment", "--real", help="🚀 Mode déploiement réel (sinon démo rapide)"),
) -> None:
    """
    Créer un cluster Kubernetes (mode CLI direct)
    """
    display_banner()
    
    deployment_mode = "real" if real_deployment else "demo"
    mode_label = "🚀 Déploiement réel" if real_deployment else "📺 Démo (simulation)"
    
    console.print(f"\n[bold]Création d'un cluster {platform.upper()}[/bold]")
    console.print(f"  • Environnement: {environment}")
    console.print(f"  • Nœuds: {nodes}")
    console.print(f"  • Monitoring: {'Activé' if monitoring else 'Désactivé'}")
    console.print(f"  • Headlamp UI: {'Activé' if headlamp else 'Désactivé'}")
    console.print(f"  • Mode: [magenta]{mode_label}[/magenta]")
    
    # Configuration
    config_dict = {
        "platform": platform,
        "environment": environment,
        "nodes": nodes,
        "deployment_mode": deployment_mode,
        "monitoring": {
            "enabled": monitoring,
            "headlamp": headlamp,
        }
    }
    
    if region:
        if platform == "eks":
            config_dict["eks_config"] = {"region": region}
        elif platform == "aks":
            config_dict["aks_config"] = {"location": region}
    
    # Configurer le mode de déploiement
    os.environ["DEPLOYMENT_MODE"] = deployment_mode
    
    # Créer et exécuter
    orchestrator = create_system()
    result = orchestrator.run_workflow(platform, environment, config_dict)
    
    if not result.success:
        console.print("\n[bold red]❌ Échec du déploiement[/bold red]")
        sys.exit(1)


@app.command()
def status(
    workflow_id: str = typer.Argument(..., help="Workflow ID")
) -> None:
    """
    Afficher le statut d'un workflow
    """
    config = Config()
    state_manager = StateManager(config)
    
    workflow = state_manager.get_workflow(workflow_id)
    
    if not workflow:
        console.print(f"[red]Workflow '{workflow_id}' not found[/red]")
        sys.exit(1)
    
    console.print(Panel.fit(
        f"""[bold]Workflow Status[/bold]

• ID: {workflow.workflow_id}
• Status: {workflow.status}
• Platform: {workflow.platform}
• Environment: {workflow.environment}
• Created: {workflow.created_at}
• Updated: {workflow.updated_at}
        """,
        title="Workflow Info",
        border_style="cyan"
    ))
    
    # Afficher les exécutions
    executions = state_manager.get_workflow_executions(workflow_id)
    
    if executions:
        console.print("\n[bold]Agent Executions:[/bold]")
        for execution in executions:
            status_icon = "✓" if execution.status == "success" else "✗"
            console.print(f"  {status_icon} {execution.agent_name}: {execution.status}")


@app.command()
def list_workflows() -> None:
    """
    Lister tous les workflows
    """
    console.print("[yellow]List command not yet implemented[/yellow]")


@app.command()
def destroy(
    workflow_id: str = typer.Argument(..., help="Workflow ID to destroy")
) -> None:
    """
    Détruire un cluster
    """
    config = Config()
    state_manager = StateManager(config)
    
    workflow = state_manager.get_workflow(workflow_id)
    
    if not workflow:
        console.print(f"[red]Workflow '{workflow_id}' not found[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold red]⚠️  Destruction du cluster {workflow_id}[/bold red]")
    console.print(f"  • Platform: {workflow.platform}")
    console.print(f"  • Environment: {workflow.environment}")
    
    if not Confirm.ask("\n[bold]Confirmer la destruction?[/bold]", default=False):
        console.print("[yellow]Annulé.[/yellow]")
        return
    
    console.print("\n[red]Destruction en cours...[/red]")
    console.print("[yellow]Feature not yet fully implemented[/yellow]")


@app.command()
def version() -> None:
    """
    Afficher la version
    """
    config = Config()
    console.print(f"[bold]{config.app_name}[/bold] version [cyan]{config.app_version}[/cyan]")


def main() -> None:
    """Point d'entrée principal"""
    # Si aucun argument, lancer le mode interactif
    if len(sys.argv) == 1:
        interactive()
    else:
        app()


if __name__ == "__main__":
    main()
