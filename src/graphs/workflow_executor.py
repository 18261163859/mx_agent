import asyncio
from typing import Dict, Any, Callable, TypedDict, Optional, AsyncGenerator
from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import StrOutputParser

from src.models.model_factory import ModelFactory
from .workflow import (
    Workflow, 
    NodeType, 
    InputValue,
)

class NodeOutput(TypedDict):
    """节点输出定义"""
    value: Any
    type: str

class WorkflowState(TypedDict):
    """工作流状态定义"""
    # 存储每个节点的输出，格式为 {node_id: {output_name: NodeOutput}}
    node_outputs: Dict[str, Dict[str, NodeOutput]]
    # 当前正在处理的节点ID
    current_node: str
    # 最终输出结果
    final_output: str

class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        # 定义状态模式
        self.graph = StateGraph(state_schema=WorkflowState)
        # 创建ModelFactory实例
        self.model_factory = ModelFactory()
        self.chat_model = self.model_factory.chat_model
        self.embedding_model = self.model_factory.embedding_model
        
    def create_node_handler(self, node_type: str) -> Callable:
        """根据节点类型创建处理函数"""
        if node_type == NodeType.START.value:
            return self._handle_start_node
        elif node_type == NodeType.LLM.value:
            return self._handle_llm_node
        elif node_type == NodeType.CONDITION.value:
            return self._handle_condition_node
        elif node_type == NodeType.END.value:
            return self._handle_end_node
        elif node_type == NodeType.KB.value:
            return self._handle_kb_node
        else:
            raise ValueError(f"不支持的节点类型: {node_type}")

    def _handle_start_node(self, state: WorkflowState) -> WorkflowState:
        """处理开始节点"""
        node = self.workflow.get_node_by_id(state["current_node"])
        node_data = node.data if isinstance(node.data, dict) else node.data.__dict__
        
        # 获取节点定义的输出参数
        outputs = node_data.get("outputs", [])
        
        # 将输入参数保存到节点输出中
        # state["node_outputs"][node.id] = {}
        # for output in outputs:
        #     output_name = output["name"]
        #     state["node_outputs"][node.id][output_name] = {
        #         "value": state["node_outputs"][node.id].get(output_name, {}).get("value", ""),
        #         "type": output["type"]
        #     }
        return state

    def _handle_llm_node(self, state: WorkflowState) -> WorkflowState:
        """处理LLM节点"""
        node = self.workflow.get_node_by_id(state["current_node"])
        
        # 获取输入参数配置
        node_data = node.data if isinstance(node.data, dict) else node.data.__dict__
        inputs_data = node_data.get("inputs", {})
        input_params = inputs_data.get("inputParameters", [])
        print(f"input_params: {input_params}")
        # 构建输入数据
        inputs = {}
        for param in input_params:
            if param["input"]["value"]["type"] == "ref":
                # 从其他节点获取输入
                source_node = param["input"]["value"]["content"]["blockID"]
                output_name = param["input"]["value"]["content"]["name"]
                inputs[param["name"]] = state["node_outputs"][source_node][output_name]["value"]
            else:
                # 使用字面量
                inputs[param["name"]] = param["input"]["value"]["content"]

        print(f"state: {state}")
        print(f"调用LLM节点，输入: {inputs}")
        # 将inputs里所有value组成一个字符串
        input_str = "".join(inputs.values())
        print(f"input_str: {input_str}")
        output = self.chat_model.invoke(input_str).content
        print(f"output: {output}")
        # output = "LLM节点的输出"  # 这里应该是实际调用LLM的地方
        
        # 保存输出
        state["node_outputs"][node.id] = {
            "output": {
                "value": output,
                "type": "string"
            }
        }
        
        return state

    def _handle_condition_node(self, state: WorkflowState) -> WorkflowState:
        """处理条件节点"""
        node = self.workflow.get_node_by_id(state["current_node"])
        
        # 获取条件配置
        node_data = node.data if isinstance(node.data, dict) else node.data.__dict__
        inputs_data = node_data.get("inputs", {})
        branches = inputs_data.get("branches", [])
        
        if not branches:
            state["condition_result"] = "true"
            return state
            
        branch = branches[0]  # 获取第一个分支的条件
        conditions = branch["condition"]["conditions"]
        
        # 评估条件
        for condition in conditions:
            # 获取左值
            left_value = self._get_condition_value(condition["left"], state)
            # 获取右值
            right_value = self._get_condition_value(condition["right"], state)

            print(f"left_value: {left_value}, right_value: {right_value}")
            
            # 根据操作符比较值的长度

            if self._compare_values(left_value, condition["operator"], right_value):
                print("compare true")
                state["condition_result"] = "true"
                return state
        
        print("compare false")
        state["condition_result"] = "false"
        return state

    def _get_condition_value(self, value_dict: Dict[str, Any], state: WorkflowState) -> Any:
        """从条件配置中获取实际值"""
        for _, input_value in value_dict.items():
            if input_value["value"]["type"] == "ref":
                # 从其他节点获取值
                source_node = input_value["value"]["content"]["blockID"]
                output_name = input_value["value"]["content"]["name"]
                return state["node_outputs"][source_node][output_name]["value"]
            else:
                # 返回字面量
                return input_value["value"]["content"]

    def _compare_values(self, left: Any, operator: int, right: Any) -> bool:
        """比较两个值"""
        if operator == 1:  # 等于
            return left == right
        elif operator == 2:  # 不等于
            return left != right
        elif operator == 3:  # 长度大于
            return len(left) > int(right)
        elif operator == 4:  # 长度小于
            return len(left) < int(right)
        return False

    def _handle_end_node(self, state: WorkflowState) -> WorkflowState:
        """处理结束节点"""
        print("处理结束节点")
        print(f"state: {state}")
        
        # 获取节点配置
        node = self.workflow.get_node_by_id(state["current_node"])
        node_data = node.data if isinstance(node.data, dict) else node.data.__dict__
        inputs_data = node_data.get("inputs", {})
        input_params = inputs_data.get("inputParameters", [])
        
        # 获取输出内容
        for param in input_params:
            if param["input"]["value"]["type"] == "ref":
                source_node = param["input"]["value"]["content"]["blockID"]
                output_name = param["input"]["value"]["content"]["name"]
                final_output = state["node_outputs"][source_node][output_name]["value"]
                # 将最终输出存储在状态中
                state = {**state, "final_output": final_output}
                break
        
        return state

    def should_continue(self, state: WorkflowState) -> str:
        """判断是否继续执行，返回字符串 'true' 或 'false'"""
        return state.get("condition_result", "false")

    def _handle_kb_node(self, state: WorkflowState) -> WorkflowState:
        """处理知识库检索节点"""
        node = self.workflow.get_node_by_id(state["current_node"])
        node_data = node.data if isinstance(node.data, dict) else node.data.__dict__
        
        # 获取查询参数
        inputs_data = node_data.get("inputs", {})
        input_params = inputs_data.get("inputParameters", [])
        
        # 构建查询
        query = ""
        for param in input_params:
            if param["input"]["value"]["type"] == "ref":
                source_node = param["input"]["value"]["content"]["blockID"]
                output_name = param["input"]["value"]["content"]["name"]
                query = state["node_outputs"][source_node][output_name]["value"]
        
        # 这里应该是实际的知识库检索逻辑
        # 示例：使用 embedding_model 进行检索
        print(f"知识库检索，查询: {query}")
        context = "这里是从知识库检索到的相关内容..."
        
        # 保存检索结果
        state["node_outputs"][node.id] = {
            "context": {
                "value": context,
                "type": "string"
            }
        }
        
        return state

    def build(self) -> StateGraph:
        """构建工作流图"""
        # 添加所有节点
        for node in self.workflow.nodes:
            # 创建一个闭包来捕获节点ID
            def create_handler(node_id: str, handler: Callable) -> Callable:
                def wrapped_handler(state: WorkflowState) -> WorkflowState:
                    # 更新当前节点ID
                    state["current_node"] = node_id
                    # 调用实际的处理函数
                    return handler(state)
                return wrapped_handler

            if node.type == NodeType.CONDITION.value:
                self.graph.add_node(
                    node.id, 
                    create_handler(node.id, self.create_node_handler(node.type))
                )
            else:
                self.graph.add_node(
                    node.id, 
                    create_handler(node.id, self.create_node_handler(node.type))
                )

        # 添加边
        condition_edges = {}  # 存储条件节点的边 {source_node: {condition: target_node}}
        
        # 先收集所有条件边
        for edge in self.workflow.edges:
            if edge.sourcePortID:
                if edge.sourceNodeID not in condition_edges:
                    condition_edges[edge.sourceNodeID] = {}
                condition_edges[edge.sourceNodeID][edge.sourcePortID] = edge.targetNodeID
        
        print(f"condition_edges: {condition_edges}")

        # 添加条件边
        for source_node, paths in condition_edges.items():
            self.graph.add_conditional_edges(
                source_node,
                self.should_continue,  # 使用类方法
                paths  # 直接使用收集到的路径映射
            )

        # 添加普通边
        for edge in self.workflow.edges:
            if not edge.sourcePortID:
                self.graph.add_edge(edge.sourceNodeID, edge.targetNodeID)

        # 设置开始和结束节点
        start_node = next(node for node in self.workflow.nodes if node.type == NodeType.START.value)
        end_node = next(node for node in self.workflow.nodes if node.type == NodeType.END.value)
        
        self.graph.set_entry_point(start_node.id)
        self.graph.set_finish_point(end_node.id)

        return self.graph

    async def run(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """运行工作流，返回流式结果"""
        # 找到开始节点
        start_node = next(node for node in self.workflow.nodes if node.type == NodeType.START.value)
        
        # 初始化状态
        initial_state = {
            "node_outputs": {
                start_node.id: {  # 初始化开始节点的输出
                    "question": {
                        "value": inputs["question"],
                        "type": "string"
                    }
                }
            },
            "current_node": start_node.id,  # 从开始节点开始
            "final_output": ""  # 初始化最终输出
        }
        
        graph = self.build()
        app = graph.compile()
        
        # 执行工作流
        final_state = await app.ainvoke(initial_state, {"recursion_limit": len(self.workflow.nodes) * 2})
        print(f"final_state: {final_state}")
        # 流式返回最终结果
        final_output = final_state.get("final_output", "")
        for char in final_output:
            yield char 