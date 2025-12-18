import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from state import AgentState
from pydantic import BaseModel, Field
from typing import List, Dict
import json


load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")  # Better model for structured output


async def main():
    """Example using MultiServerMCPClient with LangChain agents."""
    # Initialize MCP client with your stock server
    client = MultiServerMCPClient(
        {
            "stock": {
                "command": "python",
                "args": ["D:\\AIML\\mcp learn2\\StockMcp\\mcp_server\\server.py"],
                "transport": "stdio",
            }
        }
    )
    
    # Get tools from MCP servers
    tools = await client.get_tools()
    print(f"[setup] Loaded {len(tools)} tools: {[t.name for t in tools]}")
    
    # Create agent with tools
    agent = create_agent(
        llm, 
        tools
    )
    
    class PriceData(BaseModel):
        prices: List[Dict[str, str]] = Field(description="List of price dicts with 'date' and 'price' keys")
        summary: str = Field(description="Brief summary of the data")
    
    async def fetch_stock_price(state: AgentState) -> AgentState:
        """Fetch stock price using MCP prices tool that is fetch_prices only you cant use any other tool and return the state with the prices in it, returning the tool message"""
        system_message = SystemMessage(
            content="You are a stock assistant. Use the prices tool that is fetch_stock_price only you cant use any other tool to get current stock prices. and return the exact tool message what tool is provided with"
        )
        messages = [system_message, state.user_inp]
        
        tool_response = await agent.ainvoke({"messages": messages})
        
        raw_content = tool_response['messages']
        print(f"raw_content h yeeeeee", raw_content)
        for msg in reversed(raw_content):
            if isinstance(msg, ToolMessage):
                print(f"tool msg h ye ... {msg.content}")
                
                # msg.content is a list: [{'type': 'text', 'text': '{"symbol": "GOOG", ...}', 'id': '...'}]
                json_str = msg.content[0]['text']
                
                data = json.loads(json_str)
                
                print(f"Parsed data: {data}")
                print(f"Week prices: {data['week_prices']}")
                
                state.prices = [{"price": str(p), "day": i+1} for i, p in enumerate(data['week_prices'])]
                print(f"satte prices{state.prices}")
                state.result = f"Got {len(data['week_prices'])} prices for {data['symbol']}"
                break
        return state
    
    async def fetch_stock_news(state: AgentState) -> AgentState:
        """Fetch stock news - LLM returns data directly in AgentState format."""
    
        
        system_message = SystemMessage(
            content="You are a stock news giver. Use the fetch_news mcp tool no other tool to get current top news related to the stock, You provide the tool with query for that company so we can analyse the news later. and return the exact tool message what tool is provided with"
        )
        messages = [system_message, state.user_inp]
        tool_response = await agent.ainvoke({"messages": messages})
        
        raw_content = tool_response['messages']
        print(f"raw_content h yeeeeee newss ka", raw_content)

        for msg in reversed(raw_content):
            if isinstance(msg, ToolMessage):
                print(f"tool msg h ye ... {msg.content}")

                news_list = []
                for news_item in msg.content:
                    json_str = news_item['text']
                    data = json.loads(json_str)
                    news_list.append({
                        "title": data.get("title", ""),
                        "description": data.get("description", "")
                    })
                
                print(f"Parsed news: {news_list}")
                
                state.news = news_list
                state.result = f"Got {len(news_list)} news articles"
                break

        return state

    async def sentiment_analysis_node(state: AgentState) -> AgentState:
        """Perform sentiment analysis on the news articles."""
        if not state.news:
            state.sentiment = "No news to analyze."
            return state
        print(f"raw news {state.news}")
        news_summaries = " ".join([news['description'] for news in state.news])
        print(f"news summaries: {news_summaries}")
        prompt = (
            "Analyze the sentiment of the following news articles about the stock market. "
            "Provide a brief summary of the overall sentiment (positive, negative, neutral): and also tell if user should buy the stock of the company or not with the past closing week prices are \n\n "

            f"Prices: {state.prices}\n\n"
            f"News: {news_summaries}"
        )
        
        response = await llm.ainvoke({
            "messages": [HumanMessage(content=prompt)]
        })
        
        sentiment_summary = response['messages'][-1].content
        state.sentiment = sentiment_summary
        state.result = "Sentiment analysis completed."
        return state

    graph = StateGraph(AgentState)
    graph.add_node("fetch_stock_price", fetch_stock_price)
    graph.add_node("fetch_news_stock", fetch_stock_news)
    graph.add_node("sentiment_analysis", sentiment_analysis_node)
    graph.add_edge("fetch_news_stock", "sentiment_analysis")
    graph.add_edge("fetch_stock_price", "fetch_news_stock")
    graph.add_edge(START, "fetch_stock_price")
    graph.add_edge("sentiment_analysis", END)
    app = graph.compile()
    user_input = input("Enter your stock query: ")
    while user_input != "exit":
        result_state = await app.ainvoke({
            'user_inp': HumanMessage(content=user_input)
        })
        user_input = input("Enter your stock query: ")

if __name__ == "__main__":
    asyncio.run(main())

