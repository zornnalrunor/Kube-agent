# Agent Documentation

## 🤖 Overview

This document details the role and operation of each agent in the system.

## 📋 Orchestrator Agent

### Responsibilities

- **Coordination**: Orchestrates execution of all agents
- **Workflow**: Manages execution flow
- **State**: Maintains global state
- **Errors**: Decides actions on failure
- **Reporting**: Generates final report

### Execution Workflow

```python
def execute(self, agent_input: AgentInput) -> AgentOutput:
    # 1. Initialization
    display_banner()
    
    # 2. Sequential agent execution
    for agent_name, description in workflow_steps:
        # 2.1 Prepare input
        step_input = prepare_input(previous_outputs)
        
        # 2.2 Update status
        update_workflow_status(step_name)
        
        # 2.3 Execute agent
        result = agent.run(step_input)
        
        # 2.4 Check result
        if not result.success and is_critical:
            break  # Stop if critical agent fails
    
    # 3. Generate summary
    display_summary(outputs, errors)
    
    return final_output
```

### Critical Decisions

The orchestrator determines which agents are critical:

```python
def _is_critical_agent(self, agent_name: str) -> bool:
    critical_agents = {"planner", "infrastructure"}
    return agent_name in critical_agents
```

- **Critical**: Planner, Infrastructure → Failure = Stop
- **Non-critical**: Monitoring, Documentation → Failure = Warning

### User Interface

The orchestrator manages Rich console display:
- Startup banner
- Progress bars
- Summary table
- Final access (URLs)

---

## 📊 Planner Agent

### Responsibilities

- **Analysis**: Understand user requirements
- **Optimization**: Use AI to optimize configuration
- **Planning**: Generate detailed execution plan
- **Estimation**: Calculate required resources and time

### Artificial Intelligence

The Planner uses AI to optimize configuration:

```python
def _optimize_configuration(self, context: Dict) -> Dict:
    prompt = f"""
    You are a Kubernetes infrastructure expert. 
    Optimize this configuration for {platform} in {environment}:
    
    {json.dumps(context, indent=2)}
    
    Consider:
    1. Resource sizing (CPU, memory)
    2. High availability
    3. Security best practices
    4. Cost optimization
    5. Monitoring and observability
    
    Return ONLY a JSON object.
    """
    
    response = self.prompt_llm(prompt)
    return json.loads(response)
```

### Configuration by Environment

The Planner adapts config based on environment:

| Environment   | Min Nodes | Instance Type | Disk  | HA      |
|---------------|-----------|---------------|-------|---------|
| Development   | 1         | t3.medium     | 50GB  | No      |
| Staging       | 2         | t3.large      | 100GB | Partial |
| Production    | 3+        | t3.xlarge     | 200GB | Yes     |

### Execution Plan

Structure of generated plan:

```python
{
    "platform": "k3s",
    "environment": "development",
    "steps": [
        {
            "name": "infrastructure",
            "description": "Provisioning k3s cluster",
            "tasks": [
                "Initialize Terraform",
                "Create network resources",
                "Provision compute instances",
                "Configure Kubernetes"
            ],
            "estimated_time": 5  # minutes
        },
        # ... other steps
    ],
    "total_steps": 4
}
```

### Validation

The Planner validates the plan before execution:

- ✅ Plan has steps
- ✅ Each step has tasks
- ✅ Consistent estimations
- ⚠️ Warnings for sub-optimal configurations

---

## 🏗️ Infrastructure Agent

### Responsibilities

- **Generation**: Create Terraform code
- **Initialization**: `terraform init`
- **Planning**: `terraform plan`
- **Application**: `terraform apply`
- **Outputs**: Retrieve cluster information

### Terraform Generation

Terraform code is generated dynamically:

```python
def _generate_terraform_files(self, workspace, platform, config):
    # main.tf
    main_tf = self._generate_main_tf(platform, config)
    
    # variables.tf
    variables_tf = self._generate_variables_tf(config)
    
    # terraform.tfvars
    tfvars = self._generate_tfvars(config)
    
    # outputs.tf
    outputs_tf = self._generate_outputs_tf(platform)
```

### Platform Adaptation

#### K3s (Local/VMs)

```hcl
resource "null_resource" "k3s_cluster" {
  provisioner "local-exec" {
    command = "k3s server --cluster-init"
  }
}
```

#### EKS (AWS)

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  # ...
}
```

#### AKS (Azure)

```hcl
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  # ...
}
```

### Kubeconfig Management

```python
def _save_kubeconfig(self, workflow_id: str, content: str) -> str:
    kubeconfig_path = output_dir / "kubeconfigs" / f"{workflow_id}.kubeconfig"
    kubeconfig_path.write_text(content)
    kubeconfig_path.chmod(0o600)  # Security
    return str(kubeconfig_path)
```

### Error Handling

The Infrastructure agent handles Terraform errors:

```python
return_code, stdout, stderr = tf.apply()

if return_code != 0:
    # Parse Terraform error
    error_msg = parse_terraform_error(stderr)
    
    # Log
    self.log_error(f"Terraform failed: {error_msg}")
    
    # Decide next action
    if should_rollback:
        terraform_destroy()
```

---

## 📈 Monitoring Agent

### Responsibilities

- **Prometheus**: Deploy and configure Prometheus Operator
- **Grafana**: Deploy Grafana with datasources
- **Dashboards**: Import pre-configured dashboards
- **Alerts**: Configure alert rules
- **ServiceMonitors**: Create ServiceMonitors

### Monitoring Stack

```
Grafana (Visualization)
    ↓ queries
Prometheus (Metrics DB)
    ↑ scrapes
ServiceMonitors (Targets)
    ↑ expose
Applications/Infrastructure
```

### Kubernetes Manifests

The agent generates K8s manifests:

```python
def _generate_monitoring_manifests(self, workflow_id, config):
    # Namespace
    namespace = {"apiVersion": "v1", "kind": "Namespace", ...}
    
    # Prometheus ConfigMap
    prometheus_cm = self._generate_prometheus_manifest(config)
    
    # Grafana ConfigMap (datasources)
    grafana_cm = self._generate_grafana_manifest(config)
    
    # ServiceMonitors
    service_monitors = self._generate_service_monitors()
```

### Pre-configured Dashboards

Automatically imported dashboards:

1. **Kubernetes Cluster Monitoring**
   - Cluster overview
   - CPU/Memory per node
   - Pods status

2. **Node Exporter Full**
   - Detailed system metrics
   - Disk I/O
   - Network traffic

3. **Prometheus Stats**
   - Prometheus metrics itself
   - Scrape duration
   - Rule evaluation

4. **Pod Monitoring**
   - Metrics per pod
   - Restart count
   - Resource usage

5. **Namespace Resources**
   - View per namespace
   - Quotas
   - Limits vs requests

### Alert Configuration

If `alerting: true` in config:

```yaml
groups:
  - name: kubernetes-alerts
    interval: 30s
    rules:
      - alert: NodeDown
        expr: up{job="kubernetes-nodes"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Node {{ $labels.node }} is down"
```

---

## ✅ Validation Agent

### Responsibilities

- **Nodes**: Verify all nodes are Ready
- **Pods**: Verify system pods are running
- **Monitoring**: Test Prometheus/Grafana endpoints
- **Networking**: Validate network configuration
- **Health Score**: Calculate global health score

### Performed Checks

#### 1. Node Status

```python
def _check_nodes(self, kubeconfig_path: str) -> Dict:
    # kubectl get nodes
    return {
        "total": 3,
        "ready": 3,
        "not_ready": 0,
        "nodes": [...]
    }
```

#### 2. Pod Status

```python
def _check_system_pods(self, kubeconfig_path: str) -> Dict:
    # kubectl get pods -n kube-system
    # kubectl get pods -n monitoring
    return {
        "total": 12,
        "running": 12,
        "pending": 0,
        "failed": 0
    }
```

#### 3. Monitoring Endpoints

```python
def _check_monitoring_endpoints(self, monitoring_output: Dict) -> Dict:
    prometheus_url = monitoring_output["prometheus_url"]
    grafana_url = monitoring_output["grafana_url"]
    
    # HTTP GET requests
    prometheus_ok = check_endpoint(prometheus_url)
    grafana_ok = check_endpoint(grafana_url)
    
    return {
        "prometheus_ok": prometheus_ok,
        "grafana_ok": grafana_ok,
        "targets": {...}
    }
```

#### 4. Networking

```python
def _check_networking(self, kubeconfig_path: str) -> Dict:
    return {
        "ok": True,
        "pod_cidr": "10.244.0.0/16",
        "service_cidr": "10.96.0.0/16",
        "dns_ok": True,
        "connectivity_ok": True
    }
```

### Health Score

Health score calculation (0-100):

```python
def _calculate_health_score(self, health_report: Dict) -> int:
    checks = health_report["checks"]
    passed = sum(1 for c in checks if c["status"] == "passed")
    total = len(checks)
    return int((passed / total) * 100)
```

Status by score:
- **90-100**: Excellent ✅
- **80-89**: Good ⚠️
- **< 80**: Issues ❌

### Health Report

```python
health_report = {
    "checks": [
        {"category": "Nodes", "status": "passed", "message": "3/3 ready"},
        {"category": "Pods", "status": "passed", "message": "12/12 running"},
        {"category": "Monitoring", "status": "passed", "message": "Operational"},
        {"category": "Networking", "status": "passed", "message": "Valid"},
    ],
    "timestamp": "2024-02-19T10:00:00Z",
    "overall_status": "healthy"
}
```

---

## 📚 Documentation Agent

### Responsibilities

- **README**: Main document with access info
- **Architecture**: Detailed architecture documentation
- **Runbook**: Operational procedures
- **Troubleshooting**: Troubleshooting guide
- **Configs**: Configuration export
- **Diagrams**: ASCII architecture diagrams

### Generated Documents

#### 1. README.md

Contains:
- General cluster information
- Deployed architecture
- Access (Kubeconfig, Grafana, Prometheus)
- Cluster state
- Useful commands
- Destroy procedure

#### 2. ARCHITECTURE.md

Documents:
- Infrastructure configuration
- Network configuration
- Monitoring stack
- Security (RBAC, Network Policies)
- Installed addons

#### 3. RUNBOOK.md

Procedures for:
- Daily monitoring
- Metrics to watch
- Emergency procedures (node down, pod crash, etc.)
- Maintenance operations
- Scaling
- Backups

#### 4. TROUBLESHOOTING.md

Troubleshooting guide:
- Common issues
- Diagnostic commands
- Step-by-step solutions
- Contacts and escalation

#### 5. Exported Configurations

```
configs/
├── cluster-config.json      # Complete config
├── terraform-info.json      # Terraform info
└── metadata.json            # Workflow metadata
```

### ASCII Diagram

The agent generates an architecture diagram:

```
╔════════════════════════════════════════╗
║        ARCHITECTURE - K3S CLUSTER       ║
╚════════════════════════════════════════╝

┌────────────────────────────────────────┐
│           CONTROL PLANE                 │
│  ┌──────────┐  ┌──────────┐           │
│  │API Server│  │Scheduler │           │
│  └──────────┘  └──────────┘           │
└────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│ Node 1 │      │ Node 2  │
└────────┘      └─────────┘
```

---

## 🔄 Agent Lifecycle

### 1. Initialization

```python
agent = MyAgent(config, state_manager, llm)
```

### 2. Registration

```python
orchestrator.register_agent("myagent", agent)
```

### 3. Execution

```python
# The orchestrator calls
result = agent.run(agent_input)

# Which wraps execute()
def run(self, input):
    # Log start
    # Create execution record
    # Call execute()
    # Handle errors
    # Log end
    # Update execution record
```

### 4. Implementing execute()

```python
def execute(self, agent_input: AgentInput) -> AgentOutput:
    logs = []
    errors = []
    
    try:
        # 1. Get context
        context = agent_input.context
        previous_outputs = agent_input.previous_outputs
        
        # 2. Business logic
        result = do_work(context)
        
        # 3. Logs
        self.log_success("Work completed")
        logs.append("Work done")
        
        # 4. Return
        return AgentOutput(
            agent_name=self.agent_name,
            success=True,
            data={"result": result},
            logs=logs
        )
    except Exception as e:
        errors.append(str(e))
        return AgentOutput(
            agent_name=self.agent_name,
            success=False,
            errors=errors,
            logs=logs
        )
```

---

**Next**: See [CONFIGURATION.md](CONFIGURATION.md) for configuration options
