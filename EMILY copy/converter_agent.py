import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph, END
from configuration import AgentConfigurable
from langchain_arcade import ToolManager
from agent import AgentState, tool_list

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
arcade_api_key = os.getenv("ARCADE_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set")
if not arcade_api_key:
    raise ValueError("ARCADE_API_KEY is not set")

model = ChatOpenAI(model="gpt-4o")
manager = ToolManager(api_key=arcade_api_key)
tools = manager.init_tools(toolkits=tool_list)
model.bind_tools(tools)

sys_msg = SystemMessage("""
    You are an information-extraction agent. Your only objective is to read the user’s message and return a JSON dictionary with the following keys:
        •	tools_required (List[str]): The list of tools that must be used to fulfill the user’s request, or an empty list if none are needed.
        •	time_to_run_at (str, ISO 8601 format): The time at which the task should be executed. Use "immediate" if the user’s request should run right away and no time is specified.
        •	inputs_for_tools (List[Any]): The specific inputs or parameters needed for the identified tools to operate, in order corresponding to tools_required.
    
    You are given a list of tools the user has access to, use this to identify which tools and parameters are required
    You must only output the dictionary and nothing else — no explanations, no extra text.
    If any field’s value cannot be determined from the user’s message, return it as an empty list ([]) or "immediate" for time_to_run_at.
""")

HANDOFF_PROMPT = None | str
names = []
for tool in tools:
    names.append(tool.name)

def identify_tool(state: MessagesState):
    node_msg = "Identify the tool required to perform the action the user wants, return a list"
    ret = []
    

def converter(state: MessagesState):
    return {"messages": [model.invoke([sys_msg] + state["messages"] + names)]}

build = StateGraph(AgentState, AgentConfigurable)
build.add_node("converter", converter)

build.add_edge(START, "converter")
build.add_edge("converter", END)

second_graph = build.compile()