"""
LLM Provider Module
Interface unifiée pour différents providers LLM
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.config import Config, LLMProvider


class LLMProviderInterface(ABC):
    """Interface abstraite pour les providers LLM"""
    
    @abstractmethod
    def get_llm(self) -> Any:
        """Retourne une instance du LLM"""
        pass


class OpenAIProvider(LLMProviderInterface):
    """Provider pour OpenAI"""
    
    def __init__(self, config: Config):
        self.config = config
        llm_config = config.get_llm_config()
        if not llm_config.get("api_key"):
            raise ValueError("OpenAI API key is required")
        self.api_key = llm_config["api_key"]
        self.model = llm_config.get("model", "gpt-4-turbo-preview")
        self.temperature = llm_config.get("temperature", 0.7)
        self.max_tokens = llm_config.get("max_tokens", 4096)
    
    def get_llm(self) -> Any:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except ImportError:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")


class AnthropicProvider(LLMProviderInterface):
    """Provider pour Anthropic Claude"""
    
    def __init__(self, config: Config):
        self.config = config
        llm_config = config.get_llm_config()
        if not llm_config.get("api_key"):
            raise ValueError("Anthropic API key is required")
        self.api_key = llm_config["api_key"]
        self.model = llm_config.get("model", "claude-3-sonnet-20240229")
        self.temperature = llm_config.get("temperature", 0.7)
        self.max_tokens = llm_config.get("max_tokens", 4096)
    
    def get_llm(self) -> Any:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except ImportError:
            raise ImportError("langchain-anthropic not installed. Run: pip install langchain-anthropic")


class OllamaProvider(LLMProviderInterface):
    """Provider pour Ollama (local)"""
    
    def __init__(self, config: Config):
        self.config = config
        llm_config = config.get_llm_config()
        self.base_url = llm_config.get("base_url", "http://localhost:11434")
        self.model = llm_config.get("model", "llama2")
        self.temperature = llm_config.get("temperature", 0.7)
    
    def get_llm(self) -> Any:
        try:
            from langchain_community.llms import Ollama
            return Ollama(
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
            )
        except ImportError:
            raise ImportError("langchain-community not installed. Run: pip install langchain-community")


class LLMProviderFactory:
    """Factory pour créer le provider LLM approprié"""
    
    @staticmethod
    def create(config: Config) -> LLMProviderInterface:
        """Crée et retourne le provider LLM basé sur la configuration"""
        provider_map = {
            LLMProvider.OPENAI: OpenAIProvider,
            LLMProvider.ANTHROPIC: AnthropicProvider,
            LLMProvider.OLLAMA: OllamaProvider,
        }
        
        provider_class = provider_map.get(config.llm_provider)
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")
        
        return provider_class(config)
    
    @staticmethod
    def get_llm(config: Optional[Config] = None) -> BaseLLM:
        """Méthode de convenance pour obtenir directement une instance LLM"""
        from core.config import config as default_config
        cfg = config or default_config
        provider = LLMProviderFactory.create(cfg)
        return provider.get_llm()
