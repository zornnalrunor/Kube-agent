# Architecture du Système Agentique

## 🏗️ Vue d'Ensemble

Le système Terraform K8s Agent utilise une architecture multi-agents orchestrée par l'IA pour automatiser complètement le déploiement et la configuration de clusters Kubernetes.

## 📐 Principes de Conception

### 1. Séparation des Responsabilités

Chaque agent a une responsabilité unique et bien définie :

- **Orchestrator Agent** : Chef d'orchestre
- **Planner Agent** : Analyse et planification
- **Infrastructure Agent** : Provisioning Terraform
- **Monitoring Agent** : Stack d'observabilité
- **Validation Agent** : Vérifications et tests
- **Documentation Agent** : Documentation automatique

### 2. Communication Inter-Agents

```
┌──────────────────────────────────────────────────────────────┐
│                     STATE MANAGER                             │
│  (SQLite/PostgreSQL - État centralisé et persistant)         │
└──────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
         │              │              │              │
         │              │              │              │
    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │ Planner │    │  Infra  │   │Monitor  │   │Validate │
    │  Agent  │    │  Agent  │   │ Agent   │   │ Agent   │
    └─────────┘    └─────────┘   └─────────┘   └─────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                         │
                    ┌────▼─────┐
                    │   LLM    │
                    │ Provider │
                    └──────────┘
```

Les agents communiquent via un **State Manager** centralisé qui :
- Maintient l'état global du workflow
- Permet la traçabilité complète
- Gère la persistance
- Facilite les rollbacks

### 3. Intelligence Artificielle

Chaque agent utilise un LLM configurable pour :

#### Planner Agent
- Optimiser la configuration selon les best practices
- Suggérer des améliorations
- Calculer les ressources nécessaires

#### Infrastructure Agent  
- Générer du code Terraform idiomatique
- Adapter la config selon la plateforme
- Diagnostiquer les erreurs Terraform

#### Monitoring Agent
- Configurer les alertes pertinentes
- Suggérer des dashboards adaptés
- Optimiser les métriques collectées

#### Validation Agent
- Analyser les logs pour diagnostiquer
- Suggérer des corrections
- Prioriser les problèmes

#### Documentation Agent
- Générer une documentation contextuelle
- Créer des runbooks adaptés
- Documenter les décisions prises

## 🔄 Workflow d'Exécution

### Phases du Workflow

```
1. INITIALISATION
   ├─ Création du workflow dans le State Manager
   ├─ Validation des inputs
   └─ Enregistrement des agents

2. PLANNING (Planner Agent)
   ├─ Analyse des requirements
   ├─ Optimisation via LLM
   ├─ Génération du plan d'exécution
   └─ Estimation des ressources/temps

3. PROVISIONING (Infrastructure Agent)
   ├─ Génération du code Terraform
   ├─ Terraform init
   ├─ Terraform plan
   ├─ Terraform apply
   └─ Récupération des outputs

4. CONFIGURATION (Monitoring Agent)
   ├─ Génération des manifests K8s
   ├─ Déploiement Prometheus Operator
   ├─ Déploiement Grafana
   ├─ Import des dashboards
   └─ Configuration des alertes

5. VALIDATION (Validation Agent)
   ├─ Vérification des nœuds
   ├─ Vérification des pods
   ├─ Test des endpoints monitoring
   ├─ Validation networking
   └─ Génération du rapport de santé

6. DOCUMENTATION (Documentation Agent)
   ├─ Génération README
   ├─ Génération ARCHITECTURE.md
   ├─ Génération RUNBOOK.md
   ├─ Génération TROUBLESHOOTING.md
   └─ Export des configurations

7. FINALISATION
   ├─ Mise à jour du workflow (COMPLETED/FAILED)
   ├─ Sauvegarde de l'état final
   └─ Génération du rapport
```

### Gestion des Erreurs

```python
# Chaque agent implémente la gestion d'erreur
try:
    result = agent.execute(input)
except Exception as e:
    # Log l'erreur
    # Met à jour le state
    # Décide rollback ou continue
    handle_error(e)
```

Décisions selon la criticité :
- **Agent critique** (Planner, Infrastructure) : Arrêt du workflow
- **Agent non-critique** (Documentation) : Warning et continuation

### Rollback Automatique

En cas d'échec critique :
1. Détection de l'erreur
2. Sauvegarde de l'état actuel
3. Exécution de `terraform destroy`
4. Nettoyage des ressources
5. Notification à l'utilisateur

## 🗄️ Gestion de l'État

### Schéma de Base de Données

#### Table `workflows`
```sql
CREATE TABLE workflows (
    id INTEGER PRIMARY KEY,
    workflow_id TEXT UNIQUE,
    status TEXT,
    platform TEXT,
    environment TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    config JSON,
    outputs JSON,
    errors JSON
);
```

#### Table `agent_executions`
```sql
CREATE TABLE agent_executions (
    id INTEGER PRIMARY KEY,
    execution_id TEXT UNIQUE,
    workflow_id TEXT,
    agent_name TEXT,
    status TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    logs JSON
);
```

### Backends Supportés

1. **SQLite** (par défaut)
   - Parfait pour dev/test
   - Zero configuration
   - Fichier local

2. **PostgreSQL**
   - Production ready
   - Multi-instance
   - ACID compliant

3. **File**
   - Simple JSON
   - Portable
   - Debug facile

## 🤖 Provider LLM

Architecture modulaire permettant plusieurs providers :

```python
class LLMProviderInterface(ABC):
    @abstractmethod
    def get_llm(self) -> BaseLLM:
        pass

class OpenAIProvider(LLMProviderInterface):
    # Implémentation OpenAI
    ...

class AnthropicProvider(LLMProviderInterface):
    # Implémentation Anthropic
    ...

class OllamaProvider(LLMProviderInterface):
    # Implémentation Ollama (local)
    ...
```

### Configuration

```python
# .env
LLM_PROVIDER=openai  # ou anthropic, ollama
OPENAI_API_KEY=sk-...
```

## 📊 Monitoring de l'Agent System

Le système se monitore lui-même :

### Métriques Collectées

- Temps d'exécution par agent
- Taux de succès/échec
- Utilisation des ressources
- Appels LLM (count, latency, tokens)

### Logs Structurés

```python
{
    "timestamp": "2024-02-19T10:00:00Z",
    "workflow_id": "k3s-dev-abc123",
    "agent": "InfrastructureAgent",
    "level": "INFO",
    "message": "Terraform apply completed",
    "execution_time": 45.2
}
```

## 🔐 Sécurité

### Secrets Management

1. **Variables d'environnement**
   ```bash
   export OPENAI_API_KEY=sk-...
   export AWS_ACCESS_KEY_ID=...
   ```

2. **Terraform Sensitive Values**
   ```hcl
   output "kubeconfig" {
     value     = "..."
     sensitive = true
   }
   ```

3. **State Encryption**
   - SQLite: File permissions (600)
   - PostgreSQL: SSL + encryption at rest

### RBAC

Le système génère des RBAC Kubernetes par défaut :
- ServiceAccounts dédiés
- Roles avec least privilege
- RoleBindings explicites

## 🚀 Performance

### Optimisations

1. **Parallel Execution**
   - Agents indépendants exécutés en parallèle
   - Terraform parallelism configuré

2. **Caching**
   - State Terraform local
   - Images Docker pré-pullées
   - Plans Terraform cachés

3. **Incremental Updates**
   - Seules les ressources modifiées sont re-appliquées
   - Détection des drifts

## 🔄 Extensibilité

### Ajouter un Nouvel Agent

```python
# 1. Créer la classe
class MyNewAgent(BaseAgent):
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Implementation
        ...

# 2. Enregistrer dans l'orchestrateur
orchestrator.register_agent("mynew", MyNewAgent(config, state_manager))

# 3. Ajouter dans le workflow
workflow_steps.append(("mynew", "Description"))
```

### Ajouter un Nouveau Provider Cloud

```python
# 1. Créer le module Terraform
terraform/gke/main.tf

# 2. Adapter l'Infrastructure Agent
if platform == "gke":
    # Logic spécifique GKE
    ...
```

## 📈 Métriques de Succès

### KPIs du Système

- **Time to Cluster**: < 10 minutes pour K3s, < 20 min pour EKS/AKS
- **Success Rate**: > 95%
- **Monitoring Coverage**: 100% des composants critiques
- **Documentation Quality**: Automatiquement générée et à jour

---

**Next**: Voir [AGENTS.md](AGENTS.md) pour le détail de chaque agent
