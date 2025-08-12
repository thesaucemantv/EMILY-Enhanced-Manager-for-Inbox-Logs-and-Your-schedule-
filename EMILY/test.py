from langchain_arcade import ToolManager
from dotenv import load_dotenv
import os

load_dotenv()
arcade = os.getenv("ARCADE_API_KEY")

tool_list = ["Gmail"]

manager = ToolManager(api_key=arcade)
tools = manager.init_tools(toolkits=tool_list)

for s_tool in tools:
    a = s_tool.args
    print(s_tool, " ", a)