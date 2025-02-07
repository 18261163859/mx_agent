from typing import Dict, Any
from .config.settings import Settings
from .models.model_factory import ModelFactory
from .graphs.workflow import create_workflow

class AgentApp:
    def __init__(self):
        self.settings = Settings()
        self.model_factory = ModelFactory()
        self.workflow = create_workflow()
    
    @property
    def llm(self):
        """获取语言模型"""
        return self.model_factory.chat_model
    
    @property
    def embeddings(self):
        """获取嵌入模型"""
        return self.model_factory.embedding_model
    
    async def run(self, input_data: dict):
        # 确保输入数据包含所需字段
        initial_state = {
            "input": input_data["input"],
            "context": input_data["context"],
            "output": None
        }
        
        # 运行工作流
        result = self.workflow.compile().invoke(initial_state)
        return result 