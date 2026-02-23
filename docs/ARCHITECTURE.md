# Agentic System Architecture

## 🏗️ Overview

The Terraform K8s Agent system uses an AI-orchestrated multi-agent architecture to fully automate the deployment and configuration of Kubernetes clusters.

## 📐 Design Principles

### 1. Separation of Responsibilities

Each agent has a single, well-defined responsibility:

- **Orchestrator Agent**: Conductor
- **Planner Agent**: Analysis and planning
- **Infrastructure Agent**: Terraform provisioning
- **Monitoring  Agent**: Observability stack
- **Validation Agent**: Checks and tests
- **Documentation Agent**: Automatic documentation

### 2. Inter-Agent Communication

```
┌──────────────────────────────────────────────────────────────┐
│                     STATE MANAGER                             │
│  (SQLite/PostgreSQL - Centralized and persistent state)      │
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

Agents communicate via a centralized **State Manager** that:
- Maintains global workflow state
- Enables complete traceability
- Manages persistence
- Facilitates rollbacks

### 3. Artificial Intelligence

Each agent uses a configurable LLM for:

#### Planner Agent
- Optimize configuration according to best practices
- Suggest improvements
- Calculate required resources

#### Infrastructure Agent  
- Generate idiomatic Terraform code
- Adapt config based on platform
- Diagnose Terraform errors

#### Monitoring Agent
- Configure relevant alerts
- Suggest appropriate dashboards
- Optimize collected metrics

#### Validation Agent
- Analyze logs for diagnosis
- Suggest corrections
- Prioritize issues

#### Documentation Agent
- Generate contextual documentation
- Create adapted runbooks
- Document decisions made

## 🔄 Execution Workflow

### Workflow Phases

```
1. INITIALIZATION
   ├─ Create workflow in State Manager
   ├─ Validate inputs
   └─ Register agents

2. PLANNING (Planner Agent)
   ├─ Requirements analysis
   ├─ Optimization via LLM
   ├─ Execution plan generation
   └─ Resource/time estimation

3. PROVISIONING (Infrastructure Agent)
   ├─ Terraform code generation
   ├─ Terraform init
   ├─ Terraform plan
   ├─ Terraform apply
   └─ Output retrieval

4. CONFIGURATION (Monitoring Agent)
   ├─ K8s manifest generation
   ├─ Prometheus Operator deployment
   ├─ Grafana deployment
   ├─ Dashboard import
   └─ Alert configuration

5. VALIDATION (Validation Agent)
   ├─ Node verification
   ├─ Pod verification
   ├─ Monitoring endpoints test
   ├─ Networking validation
   └─ Health report generation

6. DOCUMENTATION (Documentation Agent)
   ├─ README generation
   ├─ ARCHITECTURE.md generation
   ├─ RUNBOOK.md generation
   ├─ TROUBLESHOOTING.md generation
   └─ Configuration export

7. FINALIZATION
   ├─ Workflow update (COMPLETED/FAILED)
   ├─ Final state save
   └─ Report generation
```

### Error Handling

```python
# Each agent implements error handling
try:
    result = agent.execute(input)
except Exception as e:
    # Log error
    # Update state
    # Decide rollback or continue
    handle_error(e)
```

Decisions based on criticality:
- **Critical agent** (Planner, Infrastructure): Workflow stop
- **Non-critical agent** (Documentation): Warning and continue

### Automatic Rollback

On critical failure:
1. Error detection
2. Current state save
3. Execute `terraform destroy`
4. Resource cleanup
5. User notification

## 🗄️ State Management

### Database Schema

#### `workflows` Table
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

#### `agent_executions` Table
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

### Supported Backends

1. **SQLite** (default)
   - Perfect for dev/test
   - Zero configuration
   - Local file

2. **PostgreSQL**
   - Production ready
   - Multi-instance
   - ACID compliant

3. **File**
   - Simple JSON
   - Portable
   - Easy debug

## 🤖 LLM Provider

Modular architecture supporting multiple providers:

```python
class LLMProviderInterface(ABC):
    @abstractmethod
    def get_llm(self) -> BaseLLM:
        pass

class OpenAIProvider(LLMProviderInterface):
    # OpenAI implementation
    ...

class AnthropicProvider(LLMProviderInterface):
    # Anthropic implementation
    ...

class OllamaProvider(LLMProviderInterface):
    # Ollama implementation (local)
    ...
```

### Configuration

```python
# .env
LLM_PROVIDER=openai  # or anthropic, ollama
OPENAI_API_KEY=sk-...
```

## 📊 Agent System Monitoring

The system monitors itself:

### Collected Metrics

- Execution time per agent
- Success/failure rate
- Resource utilization
- LLM calls (count, latency, tokens)

### Structured Logs

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

## 🔐 Security

### Secrets Management

1. **Environment variables**
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

The system generates Kubernetes RBAC by default:
- Dedicated ServiceAccounts
- Least privilege Roles
- Explicit RoleBindings

## 🚀 Performance

### Optimizations

1. **Parallel Execution**
   - Independent agents executed in parallel
   - Terraform parallelism configured

2. **Caching**
   - Local Terraform state
   - Pre-pulled Docker images
   - Cached Terraform plans

3. **Incremental Updates**
   - Only modified resources are re-applied
   - Drift detection

## 🔄 Extensibility

### Adding a New Agent

```python
# 1. Create class
class MyNewAgent(BaseAgent):
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Implementation
        ...

# 2. Register in orchestrator
orchestrator.register_agent("mynew", MyNewAgent(config, state_manager))

# 3. Add to workflow
workflow_steps.append(("mynew", "Description"))
```

### Adding a New Cloud Provider

```python
# 1. Create Terraform module
terraform/gke/main.tf

# 2. Adapt Infrastructure Agent
if platform == "gke":
    # GKE specific logic
    ...
```

## 📈 Success Metrics

### System KPIs

- **Time to Cluster**: < 10 minutes for K3s, < 20 min for EKS/AKS
- **Success Rate**: > 95%
- **Monitoring Coverage**: 100% of critical components
- **Documentation Quality**: Automatically generated and up-to-date

---

**Next**: See [AGENTS.md](AGENTS.md) for details on each agent
