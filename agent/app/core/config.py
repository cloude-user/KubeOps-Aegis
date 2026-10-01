import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Config
    APP_NAME: str = "KubeOps-Aegis SRE Agent"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "prd")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "aegis-super-secret-jwt-key-2026-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Azure Infrastructure & Services Configuration
    AZURE_TENANT_ID: Optional[str] = os.getenv("AZURE_TENANT_ID")
    AZURE_SUBSCRIPTION_ID: Optional[str] = os.getenv("AZURE_SUBSCRIPTION_ID")
    AZURE_KEYVAULT_URL: Optional[str] = os.getenv("AZURE_KEYVAULT_URL", "https://kubeops-aegis-kv-prd.vault.azure.net/")
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "kubeopsaegisstprd")
    AZURE_STORAGE_CONTAINER: str = os.getenv("AZURE_STORAGE_CONTAINER", "incident-logs")

    # Database Configuration (PostgreSQL / Cosmos DB)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", "postgresql://aegisadmin:P%40ssw0rdAegis2026!@localhost:5432/aegisdb")

    # Kubernetes Cluster Integration
    KUBERNETES_IN_CLUSTER: bool = os.getenv("KUBERNETES_IN_CLUSTER", "false").lower() == "true"
    KUBECONFIG_PATH: Optional[str] = os.getenv("KUBECONFIG", "~/.kube/config")

    # AI Model & LLM Provider Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gpt-4o")

    # Azure OpenAI Service Integration
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT", "https://kubeops-aegis-openai.openai.azure.com/")
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    # Prometheus Monitoring Integration
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://prometheus-k8s.monitoring.svc:9090")


settings = Settings()
