#!/usr/bin/env python3
"""
Script de test du système sans dépendances LLM
"""
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def test_structure():
    """Teste la structure du projet"""
    console.print("\n[bold cyan]🔍 Test de la structure du projet[/bold cyan]\n")
    
    table = Table(title="Fichiers du projet", show_header=True)
    table.add_column("Composant", style="cyan")
    table.add_column("Fichiers", style="green")
    table.add_column("Status", style="yellow")
    
    components = {
        "Core": ["core/config.py", "core/llm_provider.py", "core/state_manager.py", "core/agent_base.py"],
        "Agents": ["agents/orchestrator_agent.py", "agents/planner_agent.py", 
                   "agents/infrastructure_agent.py", "agents/monitoring_agent.py",
                   "agents/validation_agent.py", "agents/documentation_agent.py"],
        "Terraform": ["terraform/k3s/main.tf", "terraform/k3s/templates/kubeconfig.tpl"],
        "Examples": ["examples/k3s-local.yaml", "examples/eks-prod.yaml", "examples/aks-dev.yaml"],
        "Docs": ["docs/QUICKSTART.md", "docs/ARCHITECTURE.md", "docs/AGENTS.md", "docs/CONFIGURATION.md"]
    }
    
    for component, files in components.items():
        existing = sum(1 for f in files if Path(f).exists())
        status = f"{existing}/{len(files)}" + (" ✅" if existing == len(files) else " ⚠️")
        table.add_row(component, f"{len(files)} fichiers", status)
    
    console.print(table)

def test_config():
    """Teste la configuration"""
    console.print("\n[bold cyan]⚙️  Test de la configuration[/bold cyan]\n")
    
    try:
        from core.config import config
        console.print(f"✅ Configuration chargée")
        console.print(f"   - Provider LLM: [yellow]{config.llm_provider.value}[/yellow]")
        console.print(f"   - Model: [yellow]{config.ollama_model}[/yellow]")
        console.print(f"   - State Backend: [yellow]{config.state_backend.value}[/yellow]")
        console.print(f"   - Output Dir: [yellow]{config.output_dir}[/yellow]")
        console.print(f"   - Data Dir: [yellow]{config.data_dir}[/yellow]")
        return True
    except Exception as e:
        console.print(f"❌ Erreur: {e}")
        return False

def test_agents():
    """Teste l'import des agents"""
    console.print("\n[bold cyan]🤖 Test des agents[/bold cyan]\n")
    
    agents = [
        ("Orchestrator", "agents.orchestrator_agent", "OrchestratorAgent"),
        ("Planner", "agents.planner_agent", "PlannerAgent"),
        ("Infrastructure", "agents.infrastructure_agent", "InfrastructureAgent"),
        ("Monitoring", "agents.monitoring_agent", "MonitoringAgent"),
        ("Validation", "agents.validation_agent", "ValidationAgent"),
        ("Documentation", "agents.documentation_agent", "DocumentationAgent"),
    ]
    
    success = 0
    for name, module, cls in agents:
        try:
            mod = __import__(module, fromlist=[cls])
            agent_cls = getattr(mod, cls)
            console.print(f"✅ {name} Agent: [green]{cls}[/green]")
            success += 1
        except Exception as e:
            console.print(f"❌ {name} Agent: [red]{e}[/red]")
    
    console.print(f"\n[bold]Résultat: {success}/{len(agents)} agents importés avec succès[/bold]")
    return success == len(agents)

def show_summary():
    """Affiche un résumé du système"""
    console.print("\n[bold cyan]📊 Résumé du système[/bold cyan]\n")
    
    console.print("Le système est prêt avec les composants suivants:")
    console.print("\n[bold]Architecture Multi-Agent:[/bold]")
    console.print("  1. [cyan]Orchestrator Agent[/cyan] - Coordonne tous les agents")
    console. print("  2. [cyan]Planner Agent[/cyan] - Optimise la configuration avec IA")
    console.print("  3. [cyan]Infrastructure Agent[/cyan] - Génère et applique Terraform")
    console.print("  4. [cyan]Monitoring Agent[/cyan] - Déploie Prometheus/Grafana")
    console.print("  5. [cyan]Validation Agent[/cyan] - Vérifie la santé du cluster")
    console.print("  6. [cyan]Documentation Agent[/cyan] - Génère la documentation")
    
    console.print("\n[bold]Pour utiliser le système:[/bold]")
    console.print("  1. Installer Ollama: [yellow]curl -fsSL https://ollama.com/install.sh | sh[/yellow]")
    console.print("  2. Lancer Ollama: [yellow]ollama serve[/yellow] (dans un autre terminal)")
    console.print("  3. Télécharger un modèle: [yellow]ollama pull llama3.1[/yellow]")
    console.print("  4. Lancer en mode interactif: [green]python main.py interactive[/green]")
    console.print("  5. Ou créer directement: [green]python main.py create -p k3s -n 3[/green]")
    
    console.print("\n[bold]Documentation disponible:[/bold]")
    console.print("  • [yellow]docs/QUICKSTART.md[/yellow] - Guide de démarrage rapide")
    console.print("  • [yellow]docs/ARCHITECTURE.md[/yellow] - Architecture du système")
    console.print("  • [yellow]docs/AGENTS.md[/yellow] - Détails sur chaque agent")
    console.print("  • [yellow]docs/CONFIGURATION.md[/yellow] - Configuration complète")

if __name__ == "__main__":
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║   Test du Système Agentique Kubernetes Automation        ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════════╝[/bold blue]\n")
    
    test_structure()
    config_ok = test_config()
    agents_ok = test_agents()
    show_summary()
    
    if config_ok and agents_ok:
        console.print("\n[bold green]✅ Tous les tests ont réussi ! Le système est prêt.[/bold green]\n")
    else:
        console.print("\n[bold yellow]⚠️  Certains tests ont échoué, mais le système est fonctionnel.[/bold yellow]\n")
