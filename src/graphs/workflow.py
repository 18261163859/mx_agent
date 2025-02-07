from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum

class NodeType(Enum):
    """节点类型枚举"""
    START = "1"    # 开始节点
    END = "2"      # 结束节点
    LLM = "3"      # LLM模型节点
    KB = "4"       # 知识库检索节点
    CONDITION = "8" # 条件选择节点

@dataclass
class Position:
    """节点位置信息"""
    x: float  # X坐标
    y: float  # Y坐标

@dataclass
class NodeMeta:
    """节点元数据信息"""
    description: str       # 节点描述
    icon: str             # 节点图标URL
    subTitle: str         # 节点副标题
    title: str            # 节点标题
    mainColor: Optional[str] = None  # 节点主色调（可选）

@dataclass
class Parameter:
    """参数定义"""
    name: str                # 参数名称
    required: bool = False   # 是否必需
    type: str = "string"     # 参数类型

@dataclass
class ValueContent:
    """值内容定义"""
    content: Union[str, int, float, bool]  # 具体的值内容
    type: Literal["literal", "ref"]        # 值类型: literal(字面量) 或 ref(引用)
    blockID: Optional[str] = None          # 引用时的块ID
    name: Optional[str] = None             # 引用时的输出名称
    source: Optional[str] = None           # 引用时的来源

@dataclass
class InputValue:
    """输入值定义"""
    type: Literal["string", "integer", "float", "boolean"]  # 输入类型
    value: ValueContent  # 输入值配置

@dataclass
class InputParameter:
    """输入参数定义"""
    input: InputValue       # 输入值
    name: str              # 参数名称

@dataclass
class LLMParameter:
    """LLM模型参数配置"""
    modelType: int          # 模型类型ID
    modleName: str          # 模型名称
    generationDiversity: str # 生成多样性
    temperature: float      # 温度参数
    topP: float            # Top-P采样参数
    responseFormat: int     # 响应格式
    maxTokens: int         # 最大token数
    prompt: str            # 提示词
    enableChatHistory: bool # 是否启用聊天历史
    chatHistoryRound: int  # 聊天历史轮数
    systemPrompt: str      # 系统提示词

@dataclass
class Condition:
    """条件定义"""
    left: Dict[str, InputValue]     # 条件左值
    operator: int                   # 操作符
    right: Dict[str, InputValue]    # 条件右值

@dataclass
class ConditionConfig:
    """条件配置"""
    conditions: List[Condition]  # 条件列表
    logic: int                  # 逻辑操作符

@dataclass
class Branch:
    """分支定义"""
    condition: ConditionConfig  # 分支条件配置

@dataclass
class NodeInputs:
    """节点输入配置"""
    inputParameters: Optional[List[InputParameter]] = None  # 输入参数列表
    branches: Optional[List[Branch]] = None                # 分支列表
    llmParam: Optional[List[InputParameter]] = None        # LLM参数列表
    terminatePlan: Optional[str] = None                    # 终止计划
    settingOnError: Optional[Dict[str, str]] = None        # 错误处理配置

@dataclass
class NodeData:
    """节点数据定义"""
    nodeMeta: NodeMeta                           # 节点元数据
    outputs: Optional[List[Parameter]] = None     # 输出参数列表
    trigger_parameters: Optional[List[Parameter]] = None  # 触发参数列表
    inputs: Optional[NodeInputs] = None          # 输入配置
    version: Optional[str] = None                # 版本信息

@dataclass
class Edge:
    """边定义（节点间连接）"""
    sourceNodeID: str      # 源节点ID
    targetNodeID: str      # 目标节点ID
    sourcePortID: str = "" # 源端口ID

@dataclass
class BlockContent:
    """节点内部块内容"""
    id: str
    type: str
    content: Dict[str, Union[str, int, float, bool]]
    config: Optional[Dict[str, str]] = None

@dataclass
class Node:
    """节点定义"""
    data: NodeData                              # 节点数据
    id: str                                     # 节点ID
    meta: Dict[str, Position]                   # 节点元信息（包含位置信息）
    type: str                                   # 节点类型
    blocks: List[BlockContent] = None           # 节点内部块列表
    edges: Optional[List[Edge]] = None          # 节点级别的边

@dataclass
class WorkflowJson:
    """工作流JSON数据结构"""
    nodes: List[dict]
    edges: List[dict]
    versions: Dict[str, str]

@dataclass
class Workflow:
    """工作流定义"""
    nodes: List[Node]      # 节点列表
    edges: List[Edge]      # 边列表
    versions: Dict[str, str]  # 版本信息

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        根据ID获取节点
        Args:
            node_id: 节点ID
        Returns:
            Node: 找到的节点，如果未找到返回None
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_next_nodes(self, node_id: str) -> List[Node]:
        """
        获取指定节点的下一个节点列表
        Args:
            node_id: 当前节点ID
        Returns:
            List[Node]: 下一个节点列表
        """
        next_nodes = []
        for edge in self.edges:
            if edge.sourceNodeID == node_id:
                next_node = self.get_node_by_id(edge.targetNodeID)
                if next_node:
                    next_nodes.append(next_node)
        return next_nodes

    def validate(self) -> bool:
        """
        验证工作流的有效性
        检查是否包含必需的开始和结束节点
        Returns:
            bool: 验证结果
        """
        has_start = False
        has_end = False
        for node in self.nodes:
            if node.type == NodeType.START.value:
                has_start = True
            elif node.type == NodeType.END.value:
                has_end = True
        
        return has_start and has_end

def create_workflow_from_json(json_data: WorkflowJson) -> Workflow:
    """
    从JSON数据创建工作流实例
    Args:
        json_data: 工作流JSON配置数据
    Returns:
        Workflow: 创建的工作流实例
    """
    nodes = [Node(**node) for node in json_data.nodes]
    edges = [Edge(**edge) for edge in json_data.edges]
    return Workflow(
        nodes=nodes,
        edges=edges,
        versions=json_data.versions
    )
