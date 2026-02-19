# K3s Terraform Module

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

variable "cluster_name" {
  description = "Name of the K3s cluster"
  type        = string
  default     = "k3s-cluster"
}

variable "nodes" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

# Simulated K3s installation
# In production, this would use actual provisioners or cloud-init
resource "null_resource" "k3s_server" {
  provisioner "local-exec" {
    command = <<-EOT
      echo "Installing K3s server..."
      echo "Cluster: ${var.cluster_name}"
      echo "Nodes: ${var.nodes}"
      echo "K8s Version: ${var.kubernetes_version}"
    EOT
  }
}

resource "null_resource" "k3s_agents" {
  count = var.nodes - 1
  
  depends_on = [null_resource.k3s_server]
  
  provisioner "local-exec" {
    command = "echo 'Installing K3s agent ${count.index + 1}...'"
  }
}

# Generate kubeconfig
resource "local_file" "kubeconfig" {
  content = templatefile("${path.module}/templates/kubeconfig.tpl", {
    cluster_name = var.cluster_name
    server_url   = "https://127.0.0.1:6443"
  })
  filename = "${path.module}/kubeconfig"
  
  depends_on = [null_resource.k3s_server]
}

output "cluster_endpoint" {
  description = "K3s cluster endpoint"
  value       = "https://127.0.0.1:6443"
}

output "kubeconfig" {
  description = "Kubeconfig content"
  value       = local_file.kubeconfig.content
  sensitive   = true
}

output "cluster_name" {
  description = "Cluster name"
  value       = var.cluster_name
}
