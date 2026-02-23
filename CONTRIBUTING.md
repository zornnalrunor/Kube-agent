# CONTRIBUTING.md

## 🤝 Contributing to the Project

Thank you for your interest in contributing to Terraform K8s Agent!

## 📋 How to Contribute

### 1. Fork & Clone

```bash
# Fork on GitHub then clone
git clone https://github.com/YOUR_USERNAME/terraform-k8s-agent.git
cd terraform-k8s-agent
```

### 2. Create a Branch

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/my-bug-fix
```

### 3. Develop

```bash
# Install dev dependencies
pip install -r requirements.txt

# Enable pre-commit
pre-commit install

# Make your changes
# ...
```

### 4. Tests

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Linting
ruff check .
black --check .
mypy .
```

### 5. Commit

```bash
git add .
git commit -m "feat: add feature X"
# or
git commit -m "fix: fix bug Y"
```

**Commit convention**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Refactoring
- `test:` Tests
- `chore:` Maintenance

### 6. Push & Pull Request

```bash
git push origin feature/my-new-feature
```

Then create a Pull Request on GitHub.

## 🎯 What to Contribute?

### New Agents

Create an agent for a new functionality:

```python
# agents/my_new_agent.py
from core.agent_base import AgentInput, AgentOutput, BaseAgent

class MyNewAgent(BaseAgent):
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Your logic
        return AgentOutput(
            agent_name=self.agent_name,
            success=True,
            data={"result": "..."}
        )
```

### New Cloud Providers

- GKE (Google Cloud)
- DigitalOcean Kubernetes
- Linode Kubernetes Engine

### New Terraform Modules

Improve existing modules or create new ones.

### Documentation

- Tutorials
- Integration guides
- Translations
- Examples

### Tests

- Unit tests
- Integration tests
- End-to-end tests

## 🏗️ Architecture

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand the system.

## 📝 Code Style

### Python

```python
# Follow PEP 8
# Use Black for formatting
# Use Ruff for linting
# Type hints mandatory

def my_function(param: str) -> Dict[str, Any]:
    """
    Function description
    
    Args:
        param: Parameter description
        
    Returns:
        Dict: Return description
    """
    return {"key": "value"}
```

### Terraform

```hcl
# Format with terraform fmt
# Document variables
# Expose outputs

variable "cluster_name" {
  description = "Name of the cluster"
  type        = string
  default     = "my-cluster"
}
```

## 🧪 Tests

### Unit Tests

```python
# tests/test_my_agent.py
import pytest
from agents.my_agent import MyAgent

def test_my_agent_execute():
    agent = MyAgent(config, state_manager)
    result = agent.execute(input)
    assert result.success
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_workflow():
    orchestrator = create_system()
    result = orchestrator.run_workflow("k3s", "dev", config)
    assert result.success
```

## 📖 Documentation

- Comment complex code
- Docstrings for all functions/classes
- Keep README up-to-date
- Maintain changelog

## 🐛 Report a Bug

Create an issue with:
- Detailed description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, etc.)
- Logs

## 💡 Propose a Feature

Create a "Feature Request" issue with:
- Feature description
- Use case
- Implementation proposal (optional)

## 📞 Questions?

- GitHub Discussions
- GitHub Issues (for bugs)
- Documentation in `docs/`

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for your contribution!** 🎉
