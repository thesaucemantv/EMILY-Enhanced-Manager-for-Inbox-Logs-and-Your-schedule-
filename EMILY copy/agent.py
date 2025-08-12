import os
from configuration import AgentConfigurable
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_arcade import ToolManager

# Scope Variables
flask_auth_url = None

# ---- LOAD ENVIRONMENT VARIABLES ---- #
load_dotenv()
arcade_api_key = os.getenv("ARCADE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not arcade_api_key:
    raise ValueError("ARCADE_API_KEY is not set")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set")

# ---- INIT ARCADE TOOL MANAGER AND GMAIL TOOLS ---- #
tool_list = ["Gmail", "GoogleCalendar", "Slack", "GitHub", "Spotify", "Reddit"]
manager = ToolManager(api_key=arcade_api_key)
tools = manager.init_tools(toolkits=tool_list)

class AgentState(MessagesState):
    auth_url: str | None = None

class AuthorizationRequired(Exception):
    """Raised when the user needs to click through an OAuth URL."""
    def __init__(self, auth_response):
        super().__init__("Authorization required")
        self.auth_response = auth_response 

###### ---- NODES ---- ######
def check_auth(state: AgentState):
    """Checks if the user is authenticated."""
    global flask_auth_url
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    auth_response = manager.authorize(tool_name, user_id="default_user")
    print(auth_response)
    flask_auth_url = auth_response.url
    if auth_response.status != "completed":
        return {"auth_url": auth_response.url}
    else:
        return {"auth_url": None}

def authorize(state: AgentState):
    """Authorizes the user."""
    global flask_auth_url
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    auth_response = manager.authorize(tool_name, user_id="default_user")
    flask_auth_url = auth_response.url
    if auth_response.status != "completed":
        auth_message = (
            f"Please authorize the application in your browser:\n\n {state.get('auth_url')}"
        )
        return auth_message

# Should Continue #
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "check_auth"
    return END

# ---- TOOLS LIST ---- #

# ---- LLM WITH TOOLS ---- #
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

# ---- SYSTEM MESSAGE ---- #
sys_msg = SystemMessage(content="You are a helpful assistant that can use tools to help users with tasks.")

# ---- ASSISTANT NODE ---- #
def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


# ---- BUILD GRAPH ---- #
builder = StateGraph(AgentState, AgentConfigurable)
builder.add_node("agent", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_node("check_auth", check_auth)
builder.add_node("authorize", authorize)
builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue,
    ["check_auth", END]
)

builder.add_edge("check_auth", "authorize")
builder.add_edge("authorize", "tools")
builder.add_edge("tools", "agent")

graph = builder.compile()