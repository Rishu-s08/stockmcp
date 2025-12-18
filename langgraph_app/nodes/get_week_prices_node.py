from state import AgentState
from langchain_mcp_adapters.tools import load_mcp_tools


llm = ChatGroq(model="llama-3.1-8b-instant")


async def get_week_prices_node(state: AgentState) -> AgentState:
    tool = load_mcp_tools()
