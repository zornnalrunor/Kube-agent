"""
Core Configuration Module
Gère la configuration globale du système d'agents
"""
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """LLM Providers supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class Platform(str, Enum):
    """Plateformes Kubernetes supportées"""
    K3S = "k3s"
    EKS = "eks"
    AKS = "aks"
    GKE = "gke"


class Environment(str, Enum):
    """Environnements de déploiement"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class StateBackend(str, Enum):
    """Backends pour le state manager"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    FILE = "file"


class DeploymentMode(str, Enum):
    """Mode de déploiement"""
    DEMO = "demo"
    REAL = "real"


class Config(BaseSettings):
    """Configuration globale de l'application"""
    
    # Application
    app_name: str = "Terraform K8s Agent"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    deployment_mode: DeploymentMode = Field(default=DeploymentMode.DEMO, env="DEPLOYMENT_MODE")
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    terraform_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "terraform")
    kubernetes_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "kubernetes")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "output")
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    
    # LLM Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI, env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4-turbo-preview", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, env="LLM_MAX_TOKENS")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
    
    # State Management
    state_backend: StateBackend = Field(default=StateBackend.SQLITE, env="STATE_BACKEND")
    state_db_path: str = Field(default="./data/state.db", env="STATE_DB_PATH")
    state_db_url: Optional[str] = Field(default=None, env="STATE_DB_URL")
    
    # Terraform
    terraform_log_level: str = Field(default="INFO", env="TF_LOG")
    terraform_parallelism: int = Field(default=10, env="TF_PARALLELISM")
    
    # Kubernetes
    kubeconfig_path: Optional[str] = Field(default=None, env="KUBECONFIG")
    
    # Monitoring
    prometheus_retention: str = Field(default="15d", env="PROMETHEUS_RETENTION")
    grafana_admin_password: str = Field(default="admin", env="GRAFANA_ADMIN_PASSWORD")
    
    # Alerting
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    enable_alerts: bool = Field(default=False, env="ENABLE_ALERTS")
    
    # Agent Configuration
    agent_max_iterations: int = Field(default=10, env="AGENT_MAX_ITERATIONS")
    agent_timeout: int = Field(default=3600, env="AGENT_TIMEOUT")  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_llm_config(self) -> dict:
        """Retourne la configuration pour le LLM provider actif"""
        if self.llm_provider == LLMProvider.OPENAI:
            return {
                "api_key": self.openai_api_key,
                "model": self.llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            }
        elif self.llm_provider == LLMProvider.ANTHROPIC:
            return {
                "api_key": self.anthropic_api_key,
                "model": self.llm_model or "claude-3-sonnet-20240229",
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            }
        elif self.llm_provider == LLMProvider.OLLAMA:
            return {
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
                "temperature": self.llm_temperature,
            }
        return {}


# Instance globale de configuration
config = Config()
