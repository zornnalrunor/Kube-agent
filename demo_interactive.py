#!/usr/bin/env python3
"""
Démo interactive du système multi-agent
Simule le workflow complet sans infrastructure réelle
"""
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax

console = Console()

def show_banner():
    """Affiche la bannière de démarrage"""
    console.print("\n")
    console.print("╔═══════════════════════════════════════════════════════════════╗", style="bold cyan")
    console.print("║                                                               ║", style="bold cyan")
    console.print("║        🤖 TERRAFORM K8S AGENT - DÉMO INTERACTIVE            ║", style="bold cyan")
    console.print("║                                                               ║", style="bold cyan")
    console.print("║     Automatisation complète de clusters Kubernetes avec      ║", style="bold cyan")
    console.print("║              monitoring intégré (Prometheus/Grafana)          ║", style="bold cyan")
    console.print("║                                                               ║", style="bold cyan")
    console.print("╚═══════════════════════════════════════════════════════════════╝", style="bold cyan")
    console.print("\n")

def demo_planner_agent():
    """Démo du Planner Agent"""
    console.print("\n[bold cyan]📋 Étape 1: Planner Agent[/bold cyan]")
    console.print("\nRôle: Analyse les besoins et optimise la configuration avec IA\n")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Analyse de la configuration...", total=None)
        time.sleep(1)
        progress.update(task, description="[cyan]Consultation du LLM pour optimisation...")
        time.sleep(1)
        progress.update(task, description="[green]✓ Configuration optimisée")
    
    config = {
        "Platform": "K3s",
        "Environment": "Development",
        "Nodes": "3 (1 server + 2 agents)",
        "Memory": "4Gi par node",
        "CPU": "2 cores par node",
        "Monitoring": "Prometheus + Grafana",
        "Storage": "Local-path provisioner",
        "Networking": "Flannel CNI"
    }
    
    table = Table(title="Configuration Optimisée par IA", show_header=True)
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur", style="green")
    
    for key, value in config.items():
        table.add_row(key, value)
    
    console.print(table)
    
    console.print("\n[yellow]💡 Recommandations IA:[/yellow]")
    console.print("  • Utiliser local-path-provisioner pour le stockage en dev")
    console.print("  • Activer metrics-server pour l'autoscaling")
    console.print("  • Configurer la rétention Prometheus à 7j en dev")
    console.print("  • Réserver 20% de ressources pour le système")

def demo_infrastructure_agent():
    """Démo de l'Infrastructure Agent"""
    console.print("\n[bold cyan]🏗️  Étape 2: Infrastructure Agent[/bold cyan]")
    console.print("\nRôle: Génère le code Terraform et provisionne l'infrastructure\n")
    
    # Montre un exemple de code Terraform généré
    terraform_code = '''resource "null_resource" "k3s_server" {
  provisioner "local-exec" {
    command = <<-EOT
      curl -sfL https://get.k3s.io | sh -s - \\
        --cluster-init \\
        --write-kubeconfig-mode 644
    EOT
  }
}

resource "null_resource" "k3s_agents" {
  count = 2
  
  provisioner "local-exec" {
    command = <<-EOT
      K3S_URL=https://${var.server_ip}:6443 \\
      K3S_TOKEN=${var.token} \\
      curl -sfL https://get.k3s.io | sh -
    EOT
  }
}'''
    
    console.print("[yellow]Code Terraform généré:[/yellow]")
    syntax = Syntax(terraform_code, "hcl", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task1 = progress.add_task("[cyan]terraform init...", total=None)
        time.sleep(1)
        progress.update(task1, description="[green]✓ Terraform initialisé")
        
        task2 = progress.add_task("[cyan]terraform plan...", total=None)
        time.sleep(1)
        progress.update(task2, description="[green]✓ Plan généré: +5 à créer")
        
        task3 = progress.add_task("[cyan]terraform apply...", total=None)
        time.sleep(2)
        progress.update(task3, description="[green]✓ Infrastructure provisionnée")
    
    console.print("\n[green]✓ Kubeconfig généré: ./output/kubeconfig[/green]")

def demo_monitoring_agent():
    """Démo du Monitoring Agent"""
    console.print("\n[bold cyan]📊 Étape 3: Monitoring Agent[/bold cyan]")
    console.print("\nRôle: Déploie Prometheus et Grafana avec dashboards pré-configurés\n")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task1 = progress.add_task("[cyan]Création du namespace monitoring...", total=None)
        time.sleep(0.5)
        progress.update(task1, description="[green]✓ Namespace créé")
        
        task2 = progress.add_task("[cyan]Déploiement de Prometheus Operator...", total=None)
        time.sleep(1)
        progress.update(task2, description="[green]✓ Prometheus déployé")
        
        task3 = progress.add_task("[cyan]Configuration de Grafana...", total=None)
        time.sleep(1)
        progress.update(task3, description="[green]✓ Grafana configuré")
        
        task4 = progress.add_task("[cyan]Import des dashboards...", total=None)
        time.sleep(1)
        progress.update(task4, description="[green]✓ 5 dashboards importés")
    
    dashboards = [
        ("Cluster Overview", "Vue d'ensemble du cluster"),
        ("Node Metrics", "Métriques des nœuds"),
        ("Pod Resources", "Ressources des pods"),
        ("Network Traffic", "Trafic réseau"),
        ("Storage Usage", "Utilisation du stockage")
    ]
    
    console.print("\n[yellow]📈 Dashboards Grafana:[/yellow]")
    for name, desc in dashboards:
        console.print(f"  • [cyan]{name}[/cyan]: {desc}")
    
    console.print("\n[green]✓ Accès:[/green]")
    console.print("  • Prometheus: http://localhost:9090")
    console.print("  • Grafana: http://localhost:3000 (admin/admin)")

def demo_validation_agent():
    """Démo du Validation Agent"""
    console.print("\n[bold cyan]🔍 Étape 4: Validation Agent[/bold cyan]")
    console.print("\nRôle: Vérifie la santé du cluster et génère un rapport\n")
    
    checks = [
        ("Nœuds Ready", "3/3", "success"),
        ("Pods système running", "12/12", "success"),
        ("Endpoints Prometheus", "✓", "success"),
        ("Endpoints Grafana", "✓", "success"),
        ("DNS résolution", "✓", "success"),
        ("API Server", "Healthy", "success"),
    ]
    
    table = Table(title="Checks de Santé", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Résultat", style="green")
    table.add_column("Status", style="yellow")
    
    for check, result, status in checks:
        icon = "✓" if status == "success" else "✗"
        style = "green" if status == "success" else "red"
        table.add_row(check, result, f"[{style}]{icon}[/{style}]")
    
    console.print(table)
    
    console.print("\n[bold green]✅ Score de santé: 100/100[/bold green]")
    console.print("\nTous les composants fonctionnent correctement !")

def demo_documentation_agent():
    """Démo du Documentation Agent"""
    console.print("\n[bold cyan]📚 Étape 5: Documentation Agent[/bold cyan]")
    console.print("\nRôle: Génère la documentation complète du déploiement\n")
    
    docs = [
        ("README.md", "Guide d'accès et informations du cluster"),
        ("ARCHITECTURE.md", "Diagramme et description de l'architecture"),
        ("RUNBOOK.md", "Procédures opérationnelles"),
        ("TROUBLESHOOTING.md", "Guide de dépannage"),
        ("configs/cluster-config.json", "Configuration exportée")
    ]
    
    console.print("[yellow]Documents générés:[/yellow]")
    for doc, desc in docs:
        console.print(f"  • [cyan]{doc}[/cyan]")
        console.print(f"    {desc}")
    
    # Exemple d'architecture ASCII
    architecture = """
╔════════════════════════════════════════════════╗
║           K3s Cluster Architecture             ║
╠════════════════════════════════════════════════╣
║                                                ║
║  ┌──────────────┐                              ║
║  │  K3s Server  │ (Control Plane)              ║
║  │  + etcd      │                              ║
║  └───────┬──────┘                              ║
║          │                                     ║
║    ┌─────┴─────┐                               ║
║    │           │                               ║
║  ┌─▼──┐      ┌─▼──┐                            ║
║  │Node│      │Node│  (Workers)                 ║
║  │ #1 │      │ #2 │                            ║
║  └────┘      └────┘                            ║
║                                                ║
║  Monitoring Stack:                             ║
║  ┌─────────────┐  ┌──────────┐                ║
║  │ Prometheus  │  │ Grafana  │                ║
║  └─────────────┘  └──────────┘                ║
║                                                ║
╚════════════════════════════════════════════════╝
"""
    console.print(Panel(architecture, title="Architecture", border_style="green"))

def show_final_summary():
    """Affiche le résumé final"""
    console.print("\n")
    console.print("╔════════════════════════════════════════════════════════════════╗", style="bold green")
    console.print("║                    ✅ DÉPLOIEMENT RÉUSSI                       ║", style="bold green")
    console.print("╚════════════════════════════════════════════════════════════════╝", style="bold green")
    
    summary = Table(title="Résumé du Déploiement", show_header=True)
    summary.add_column("Agent", style="cyan")
    summary.add_column("Status", style="green")
    summary.add_column("Durée", style="yellow")
    
    summary.add_row("Planner", "✓ Complété", "1.8s")
    summary.add_row("Infrastructure", "✓ Complété", "12.5s")
    summary.add_row("Monitoring", "✓ Complété", "8.3s")
    summary.add_row("Validation", "✓ Complété", "2.1s")
    summary.add_row("Documentation", "✓ Complété", "1.5s")
    summary.add_row("[bold]TOTAL[/bold]", "[bold]✓ Succès[/bold]", "[bold]26.2s[/bold]")
    
    console.print(summary)
    
    console.print("\n[bold]🎯 Prochaines étapes:[/bold]")
    console.print("  1. Vérifier les dashboards Grafana")
    console.print("  2. Déployer vos applications")
    console.print("  3. Configurer les alertes")
    console.print("  4. Consulter la documentation générée\n")

def main():
    """Lance la démo complète"""
    show_banner()
    
    console.print("[bold]Configuration du déploiement:[/bold]")
    console.print("  • Platform: K3s")
    console.print("  • Environment: Development")
    console.print("  • Nodes: 3")
    console.print("  • Monitoring: Activé\n")
    
    console.input("[cyan]Appuyez sur Entrée pour démarrer la démo...[/cyan]")
    
    # Workflow complet
    demo_planner_agent()
    console.input("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
    
    demo_infrastructure_agent()
    console.input("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
    
    demo_monitoring_agent()
    console.input("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
    
    demo_validation_agent()
    console.input("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
    
    demo_documentation_agent()
    console.input("\n[dim]Appuyez sur Entrée pour voir le résumé...[/dim]")
    
    show_final_summary()
    
    console.print("\n[bold cyan]Merci d'avoir essayé le système Terraform K8s Agent ![/bold cyan]")
    console.print("\nPour un déploiement réel:")
    console.print("  [yellow]python main.py create --platform k3s --nodes 3 --monitoring[/yellow]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Démo interrompue.[/yellow]\n")
