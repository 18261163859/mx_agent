from typing import Dict, Any, Union
from langchain_core.agents import AgentAction, AgentFinish

class BaseAgent:
    def __init__(self):
        self.name = "base_agent"
    
    async def handle(self, state: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
        """
        处理输入状态并返回下一个动作
        
        Args:
            state: 当前工作流状态
            
        Returns:
            AgentAction 或 AgentFinish
        """
        raise NotImplementedError 