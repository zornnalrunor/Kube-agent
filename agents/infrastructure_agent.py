"""
Infrastructure Agent
Agent responsable du provisioning de l'infrastructure via Terraform
"""
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from python_terraform import IsFlagged, Terraform

from core.agent_base import AgentInput, AgentOutput, BaseAgent


class InfrastructureAgent(BaseAgent):
    """
    Agent d'infrastructure
    
    Responsabilités:
    - Générer le code Terraform
    - Initialiser Terraform
    - Appliquer le plan d'infrastructure
    - Gérer le state Terraform
    - Récupérer les outputs
    """
    
    def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Provisionne l'infrastructure via Terraform
        
        Args:
            agent_input: Input contenant la configuration
            
        Returns:
            AgentOutput: Résultat du provisioning
        """
        logs = []
        errors = []
        
        try:
            # Récupérer la configuration du planner
            planner_output = agent_input.previous_outputs.get("planner", {})
            config = planner_output.get("optimized_config", agent_input.context)
            
            platform = config.get("platform", "k3s")
            self.log(f"Provisioning {platform} infrastructure")
            
            # Préparer le workspace Terraform
            tf_workspace = self._prepare_terraform_workspace(
                agent_input.workflow_id,
                platform,
                config
            )
            logs.append(f"Terraform workspace created: {tf_workspace}")
            
            # Générer les fichiers Terraform
            self._generate_terraform_files(tf_workspace, platform, config)
            logs.append("Terraform files generated")
            self.log_success("Terraform configuration generated")
            
            # Initialiser Terraform
            tf = Terraform(working_dir=str(tf_workspace))
            self.log("Initializing Terraform...")
            return_code, stdout, stderr = tf.init()
            
            if return_code != 0:
                error_msg = stderr if stderr else stdout
                errors.append(f"Terraform init failed: {error_msg}")
                self.log_error(f"Terraform initialization failed: {error_msg}")
                logs.append(f"Init error: {error_msg}")
            else:
                logs.append("Terraform initialized")
                self.log_success("Terraform initialized")
            
            # Plan Terraform
            if not errors:
                self.log("Creating Terraform plan...")
                return_code, stdout, stderr = tf.plan()
                
                # Terraform plan return codes:
                # 0 = no changes, 1 = error, 2 = changes planned (success!)
                if return_code == 1:
                    error_msg = stderr if stderr else stdout
                    errors.append(f"Terraform plan failed: {error_msg}")
                    self.log_error(f"Terraform plan failed: {error_msg}")
                    logs.append(f"Plan error: {error_msg}")
                else:
                    logs.append("Terraform plan created")
                    if return_code == 2:
                        self.log_success("Terraform plan created (changes detected)")
                    else:
                        self.log_success("Terraform plan created (no changes)")
            
            # Apply Terraform
            if not errors and not self.config.debug:  # Skip apply in debug mode
                self.log("Applying Terraform configuration...")
                return_code, stdout, stderr = tf.apply(skip_plan=True, auto_approve=IsFlagged)
                
                if return_code != 0:
                    errors.append(f"Terraform apply failed: {stderr}")
                    self.log_error("Terraform apply failed")
                else:
                    logs.append("Infrastructure provisioned")
                    self.log_success("Infrastructure provisioned successfully")
            
            # Récupérer les outputs
            outputs = {}
            if not errors:
                tf_outputs = tf.output()
                if isinstance(tf_outputs, dict):
                    outputs = tf_outputs
                logs.append(f"Retrieved {len(outputs)} Terraform outputs")
            
            # Générer le kubeconfig si disponible
            kubeconfig_path = None
            if "kubeconfig" in outputs:
                # Les outputs Terraform retournent {'value': '...', 'sensitive': True}
                kubeconfig_content = outputs["kubeconfig"]
                if isinstance(kubeconfig_content, dict):
                    kubeconfig_content = kubeconfig_content.get("value", "")
                
                if kubeconfig_content:
                    kubeconfig_path = self._save_kubeconfig(
                        agent_input.workflow_id,
                        kubeconfig_content
                    )
                    logs.append(f"Kubeconfig saved: {kubeconfig_path}")
            
            # Extraire le cluster endpoint
            cluster_endpoint = outputs.get("cluster_endpoint")
            if isinstance(cluster_endpoint, dict):
                cluster_endpoint = cluster_endpoint.get("value")
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=len(errors) == 0,
                data={
                    "platform": platform,
                    "workspace": str(tf_workspace),
                    "outputs": outputs,
                    "kubeconfig_path": kubeconfig_path,
                    "cluster_endpoint": cluster_endpoint,
                    "summary": f"{platform} cluster provisioned" if not errors else "Provisioning failed"
                },
                errors=errors,
                logs=logs,
            )
            
        except Exception as e:
            error_msg = f"Infrastructure provisioning failed: {str(e)}"
            errors.append(error_msg)
            self.log_error(error_msg)
            
            return AgentOutput(
                agent_name=self.agent_name,
                success=False,
                errors=errors,
                logs=logs,
            )
    
    def _prepare_terraform_workspace(
        self,
        workflow_id: str,
        platform: str,
        config: Dict[str, Any]
    ) -> Path:
        """
        Prépare le workspace Terraform
        
        Args:
            workflow_id: ID du workflow
            platform: Plateforme
            config: Configuration
            
        Returns:
            Path: Chemin du workspace
        """
        workspace_dir = self.config.output_dir / "terraform" / workflow_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir
    
    def _generate_terraform_files(
        self,
        workspace: Path,
        platform: str,
        config: Dict[str, Any]
    ) -> None:
        """
        Génère les fichiers Terraform
        
        Args:
            workspace: Workspace directory
            platform: Plateforme
            config: Configuration
        """
        # Copier le module de base
        module_source = self.config.terraform_dir / platform
        
        # Générer le main.tf
        main_tf = self._generate_main_tf(platform, config)
        (workspace / "main.tf").write_text(main_tf)
        
        # Générer le variables.tf
        variables_tf = self._generate_variables_tf(config)
        (workspace / "variables.tf").write_text(variables_tf)
        
        # Générer le terraform.tfvars
        tfvars = self._generate_tfvars(config)
        (workspace / "terraform.tfvars").write_text(tfvars)
        
        # Générer outputs.tf
        outputs_tf = self._generate_outputs_tf(platform, config)
        (workspace / "outputs.tf").write_text(outputs_tf)
    
    def _generate_main_tf(self, platform: str, config: Dict[str, Any]) -> str:
        """Génère le fichier main.tf"""
        nodes = config.get("nodes", 3)
        k8s_version = config.get("kubernetes_version", "1.28")
        deployment_mode = config.get("deployment_mode", self.config.deployment_mode.value)
        
        if platform == "k3s":
            # Mode RÉEL : Installation K3s véritable
            if deployment_mode == "real":
                return f'''
terraform {{
  required_providers {{
    local = {{
      source  = "hashicorp/local"
      version = "~> 2.4"
    }}
    null = {{
      source  = "hashicorp/null"
      version = "~> 3.2"
    }}
  }}
}}

# K3s Server Node (Control Plane)
resource "null_resource" "k3s_server" {{
  provisioner "local-exec" {{
    command = <<-EOT
      echo "🚀 Installing K3s server..."
      curl -sfL https://get.k3s.io | sh -s - \\
        --write-kubeconfig-mode 644 \\
        --node-name k3s-server
      
      # Wait for K3s to be ready
      echo "⏳ Waiting for K3s to be ready..."
      timeout 60 bash -c 'until kubectl get nodes 2>/dev/null; do sleep 2; done'
      echo "✅ K3s server is ready!"
      
      # Copy kubeconfig to output directory
      sudo cp /etc/rancher/k3s/k3s.yaml ${{path.module}}/kubeconfig
      sudo chmod 644 ${{path.module}}/kubeconfig
      echo "📋 Kubeconfig saved to ${{path.module}}/kubeconfig"
    EOT
  }}
}}

# Read the kubeconfig file after it's created
data "local_file" "kubeconfig" {{
  depends_on = [null_resource.k3s_server]
  filename   = "${{path.module}}/kubeconfig"
}}
'''
            
            # Mode DÉMO : Simulation rapide
            else:
                return f'''
terraform {{
  required_providers {{
    local = {{
      source  = "hashicorp/local"
      version = "~> 2.4"
    }}
    null = {{
      source  = "hashicorp/null"
      version = "~> 3.2"
    }}
  }}
}}

# K3s cluster - pour demo/dev
resource "null_resource" "k3s_cluster" {{
  provisioner "local-exec" {{
    command = "echo '📺 K3s cluster simulation - would deploy {nodes} nodes here'"
  }}
}}

# Simulated kubeconfig for demo
resource "local_file" "kubeconfig" {{
  content  = <<-EOT
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://localhost:6443
  name: k3s-cluster
contexts:
- context:
    cluster: k3s-cluster
    user: k3s-admin
  name: k3s
current-context: k3s
users:
- name: k3s-admin
  user: {{}}
EOT
  filename = "${{path.module}}/kubeconfig"
}}
'''
        elif platform == "eks":
            region = config.get("eks_config", {}).get("region", "us-east-1")
            return f'''
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

# EKS Cluster configuration
# Note: This is a simplified version for demonstration
resource "null_resource" "eks_cluster" {{
  provisioner "local-exec" {{
    command = "echo 'EKS cluster simulation - would deploy in {region}'"
  }}
}}
'''
        else:  # aks
            location = config.get("aks_config", {}).get("location", "eastus")
            return f'''
terraform {{
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
}}

# AKS Cluster configuration
resource "null_resource" "aks_cluster" {{
  provisioner "local-exec" {{
    command = "echo 'AKS cluster simulation - would deploy in {location}'"
  }}
}}
'''
    
    def _generate_variables_tf(self, config: Dict[str, Any]) -> str:
        """Génère le fichier variables.tf"""
        return '''
variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "nodes" {
  description = "Number of nodes"
  type        = number
  default     = 3
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}
'''
    
    def _generate_tfvars(self, config: Dict[str, Any]) -> str:
        """Génère le fichier terraform.tfvars"""
        nodes = config.get("nodes", 3)
        environment = config.get("environment", "development")
        k8s_version = config.get("kubernetes_version", "1.28")
        
        return f'''
cluster_name       = "terraform-agent-cluster"
environment        = "{environment}"
nodes              = {nodes}
kubernetes_version = "{k8s_version}"
'''
    
    def _generate_outputs_tf(self, platform: str, config: Dict[str, Any]) -> str:
        """Génère le fichier outputs.tf"""
        deployment_mode = config.get("deployment_mode", self.config.deployment_mode.value)
        
        # Use different resource reference based on mode
        if deployment_mode == "real":
            kubeconfig_ref = "data.local_file.kubeconfig.content"
        else:
            kubeconfig_ref = "local_file.kubeconfig.content"
        
        return f'''
output "cluster_endpoint" {{
  description = "Kubernetes cluster endpoint"
  value       = "https://localhost:6443"
}}

output "kubeconfig" {{
  description = "Kubeconfig content"
  value       = {kubeconfig_ref}
  sensitive   = true
}}
'''
    
    def _save_kubeconfig(self, workflow_id: str, kubeconfig_content: str) -> str:
        """
        Sauvegarde le kubeconfig
        
        Args:
            workflow_id: ID du workflow
            kubeconfig_content: Contenu du kubeconfig
            
        Returns:
            str: Chemin du fichier kubeconfig
        """
        kubeconfig_dir = self.config.output_dir / "kubeconfigs"
        kubeconfig_dir.mkdir(parents=True, exist_ok=True)
        
        kubeconfig_path = kubeconfig_dir / f"{workflow_id}.kubeconfig"
        kubeconfig_path.write_text(kubeconfig_content)
        kubeconfig_path.chmod(0o600)
        
        return str(kubeconfig_path)
