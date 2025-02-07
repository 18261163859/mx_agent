from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """项目配置"""
    
    # Chat模型配置
    CHAT_API_KEY: str
    CHAT_BASE_URL: str
    CHAT_MODEL: str
    
    # Embedding模型配置
    EMBEDDING_API_KEY: str
    EMBEDDING_BASE_URL: str
    EMBEDDING_MODEL: str
    
    # 其他配置项
    DEBUG: bool = False
    
    class Config:
        env_file = ".env" 