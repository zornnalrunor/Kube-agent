# CONTRIBUTING.md

## 🤝 Contribution au Projet

Merci de votre intérêt pour contribuer à Terraform K8s Agent!

## 📋 Comment Contribuer

### 1. Fork & Clone

```bash
# Fork sur GitHub puis clone
git clone https://github.com/YOUR_USERNAME/terraform-k8s-agent.git
cd terraform-k8s-agent
```

### 2. Créer une Branche

```bash
git checkout -b feature/ma-nouvelle-feature
# ou
git checkout -b fix/mon-bug-fix
```

### 3. Développer

```bash
# Installer les dépendances de dev
pip install -r requirements.txt

# Activer pre-commit
pre-commit install

# Faire vos modifications
# ...
```

### 4. Tests

```bash
# Lancer les tests
pytest

# Avec coverage
pytest --cov=. --cov-report=html

# Linting
ruff check .
black --check .
mypy .
```

### 5. Commit

```bash
git add .
git commit -m "feat: ajout de la fonctionnalité X"
# ou
git commit -m "fix: correction du bug Y"
```

**Convention de commits** :
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `style:` Formatage
- `refactor:` Refactoring
- `test:` Tests
- `chore:` Maintenance

### 6. Push & Pull Request

```bash
git push origin feature/ma-nouvelle-feature
```

Puis créer une Pull Request sur GitHub.

## 🎯 Que Contribuer?

### Nouveaux Agents

Créer un agent pour une nouvelle fonctionnalité :

```python
# agents/my_new_agent.py
from core.agent_base import AgentInput, AgentOutput, BaseAgent

class MyNewAgent(BaseAgent):
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Votre logique
        return AgentOutput(
            agent_name=self.agent_name,
            success=True,
            data={"result": "..."}
        )
```

### Nouveaux Providers Cloud

- GKE (Google Cloud)
- DigitalOcean Kubernetes
- Linode Kubernetes Engine

### Nouveaux Modules Terraform

Améliorer les modules existants ou en créer de nouveaux.

### Documentation

- Tutoriels
- Guides d'intégration
- Traductions
- Exemples

### Tests

- Tests unitaires
- Tests d'intégration
- Tests end-to-end

## 🏗️ Architecture

Lire [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour comprendre le système.

## 📝 Style de Code

### Python

```python
# Suivre PEP 8
# Utiliser Black pour le formatage
# Utiliser Ruff pour le linting
# Type hints obligatoires

def my_function(param: str) -> Dict[str, Any]:
    """
    Description de la fonction
    
    Args:
        param: Description du paramètre
        
    Returns:
        Dict: Description du retour
    """
    return {"key": "value"}
```

### Terraform

```hcl
# Formatage avec terraform fmt
# Variables documentées
# Outputs exposés

variable "cluster_name" {
  description = "Name of the cluster"
  type        = string
  default     = "my-cluster"
}
```

## 🧪 Tests

### Tests Unitaires

```python
# tests/test_my_agent.py
import pytest
from agents.my_agent import MyAgent

def test_my_agent_execute():
    agent = MyAgent(config, state_manager)
    result = agent.execute(input)
    assert result.success
```

### Tests d'Intégration

```python
# tests/test_integration.py
def test_full_workflow():
    orchestrator = create_system()
    result = orchestrator.run_workflow("k3s", "dev", config)
    assert result.success
```

## 📖 Documentation

- Commenter le code complexe
- Docstrings pour toutes les fonctions/classes
- README à jour
- Changelog maintenu

## 🐛 Reporter un Bug

Créer une issue avec :
- Description détaillée
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, etc.)
- Logs

## 💡 Proposer une Feature

Créer une issue "Feature Request" avec :
- Description de la feature
- Use case
- Proposition d'implémentation (optionnel)

## 📞 Questions?

- GitHub Discussions
- GitHub Issues (pour les bugs)
- Documentation dans `docs/`

## 📜 License

En contribuant, vous acceptez que vos contributions soient sous license MIT.

---

**Merci pour votre contribution!** 🎉
