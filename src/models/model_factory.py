from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from ..config.settings import Settings

class ModelFactory:
    def __init__(self):
        self.settings = Settings()
        self._chat_model: Optional[BaseChatModel] = None
        self._embedding_model: Optional[Embeddings] = None
    
    @property
    def chat_model(self) -> BaseChatModel:
        """获取chat模型实例（单例模式）"""
        if self._chat_model is None:
            self._chat_model = ChatOpenAI(
                api_key=self.settings.CHAT_API_KEY,
                base_url=self.settings.CHAT_BASE_URL,
                model=self.settings.CHAT_MODEL,
            )
        return self._chat_model
    
    @property
    def embedding_model(self) -> Embeddings:
        """获取embedding模型实例（单例模式）"""
        if self._embedding_model is None:
            self._embedding_model = OpenAIEmbeddings(
                api_key=self.settings.EMBEDDING_API_KEY,
                base_url=self.settings.EMBEDDING_BASE_URL,
                model=self.settings.EMBEDDING_MODEL,
            )
        return self._embedding_model 