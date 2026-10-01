import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Aegis E-Commerce API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    # Azure PostgreSQL Flexible Server Connection
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://aegisadmin:P%40ssw0rdAegis2026!@kubeops-aegis-psql-prd.postgres.database.azure.com:5432/orderdb"
    )
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "kubeopsaegisstprd")
    AZURE_STORAGE_CONTAINER_MEDIA: str = os.getenv("AZURE_STORAGE_CONTAINER_MEDIA", "user-media")
    AZURE_STORAGE_CONTAINER_RECEIPTS: str = os.getenv("AZURE_STORAGE_CONTAINER_RECEIPTS", "order-receipts")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "aegis-commerce-jwt-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"


settings = Settings()
