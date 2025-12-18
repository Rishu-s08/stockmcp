import asyncio
from email import message
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from typing import Annotated, List, Dict
import json

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")

class AgentState(TypedDict):
    messages : Annotated[list, add_messages]


async def main():
    client = MultiServerMCPClient(
        {
            "stock": {
                "command": "python",
                "args": ["D:\\AIML\\mcp learn2\\StockMcp\\mcp_server\\server.py"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()
    agent = create_agent(llm, tools, state_schema=AgentState)

    # async def chatbot(state: AgentState) -> AgentState:
    #     print(state["messages"])
    #     response = await agent.ainvoke(state["messages"])
    #     return {"messages" : [response]}

    
    graph = StateGraph(AgentState)
    graph.add_node("chatbot", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_conditional_edges("chatbot", tools_condition)
    graph.add_edge(START, "chatbot")
    graph.add_edge("tools", "chatbot")

    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    config = {"configurable":{"thread_id":"1"}}
    
    # for visulization
    # with open("graph.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())
    # print("Graph saved as graph.png")

    # response = await app.ainvoke({"messages" : ["hello, do you remember my name"]}, config=config)
    # for m in response["messages"]:
    #     m.pretty_print()

    user_input  = input("User: ")
    while user_input.lower() not in ["exit", "quit"]:
        response = await app.ainvoke({"messages" : [user_input]}, config=config)
        # for m in response["messages"]:
        #     m.pretty_print()
        print("AI:", response["messages"][-1].content)
        user_input  = input("User: ")

asyncio.run(main())
