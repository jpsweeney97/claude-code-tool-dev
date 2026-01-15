"""Session-log MCP server."""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tool_handlers import get_tool_definitions, handle_tool

server = Server("session-log")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [Tool(**defn) for defn in get_tool_definitions()]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    results = handle_tool(name, arguments)
    return [TextContent(type="text", text=r.text) for r in results]


async def run():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
