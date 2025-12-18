from tools.price_fetch import fetch_price
from mcp.server.fastmcp import FastMCP
from tools.news_fetch_tool import fetch_news


mcp = FastMCP("stockmcp")

mcp.add_tool(fetch_price)
mcp.add_tool(fetch_news)


if __name__ == "__main__":
    mcp.run()