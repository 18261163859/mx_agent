import asyncio
import json
from src.graphs.workflow import create_workflow_from_json, WorkflowJson
from src.graphs.workflow_executor import WorkflowExecutor

async def main():
    # 读取模板文件
    with open("template.json", "r", encoding="utf-8") as f:
        template = json.load(f)
    
    # 创建工作流
    workflow_json = WorkflowJson(**template)
    workflow = create_workflow_from_json(workflow_json)
    
    # 创建执行器
    executor = WorkflowExecutor(workflow)
    
    # 示例输入数据
    input_data = {
        "question": "你好帮我写一首赞美春节的诗"
    }
    
    # 运行工作流并处理流式输出
    result = ""
    async for chunk in executor.run(input_data):
        await asyncio.sleep(0.05)
        print(chunk, end="", flush=True)
        # result += chunk
    # print(result)

if __name__ == "__main__":
    asyncio.run(main()) 