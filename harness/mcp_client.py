"""MCP client for connecting to MCP servers and aggregating tools."""

import asyncio
from dataclasses import dataclass
from typing import Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class MCPServer:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str] | None = None


@dataclass
class MCPTool:
    """A tool from an MCP server."""
    name: str
    description: str
    input_schema: dict
    server_name: str  # Which server this tool belongs to


class MCPClientManager:
    """Manages connections to multiple MCP servers."""

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.tools: dict[str, MCPTool] = {}  # tool_name -> MCPTool
        self._exit_stack = AsyncExitStack()

    async def connect(self, servers: list[MCPServer]) -> None:
        """Connect to all configured MCP servers."""
        for server in servers:
            try:
                await self._connect_server(server)
            except Exception as e:
                print(f"  Warning: Failed to connect to {server.name}: {e}")

    async def _connect_server(self, server: MCPServer) -> None:
        """Connect to a single MCP server."""
        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=server.env
        )

        # Create transport and session
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        # Initialize the session
        await session.initialize()

        # Store session
        self.sessions[server.name] = session

        # Discover and register tools
        response = await session.list_tools()
        for tool in response.tools:
            self.tools[tool.name] = MCPTool(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                server_name=server.name
            )

        print(f"  Connected to {server.name}: {len(response.tools)} tools")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool by name with given arguments."""
        if name not in self.tools:
            return f"Error: Unknown tool '{name}'"

        tool = self.tools[name]
        session = self.sessions.get(tool.server_name)

        if not session:
            return f"Error: Server '{tool.server_name}' not connected"

        try:
            result = await session.call_tool(name, arguments)
            # Extract text content from result
            if hasattr(result, 'content'):
                texts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                return "\n".join(texts) if texts else str(result)
            return str(result)
        except Exception as e:
            return f"Error calling tool '{name}': {e}"

    def get_tool_definitions(self) -> list[dict]:
        """Get tool definitions in format suitable for LLM prompting."""
        definitions = []
        for tool in self.tools.values():
            definitions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            })
        return definitions

    def get_tool_docs(self) -> str:
        """Get human-readable tool documentation for system prompt."""
        docs = []
        for tool in self.tools.values():
            params = tool.input_schema.get("properties", {})
            param_docs = ", ".join(
                f'{p}: {info.get("type", "any")}'
                for p, info in params.items()
            )
            docs.append(f"- {tool.name}({param_docs}): {tool.description}")
        return "\n".join(docs)

    async def close(self) -> None:
        """Close all server connections."""
        await self._exit_stack.aclose()


# Global client instance
_client: MCPClientManager | None = None


async def get_client() -> MCPClientManager:
    """Get the global MCP client instance."""
    global _client
    if _client is None:
        _client = MCPClientManager()
    return _client


async def initialize(servers: list[MCPServer]) -> MCPClientManager:
    """Initialize the MCP client with given servers."""
    global _client
    _client = MCPClientManager()
    await _client.connect(servers)
    return _client


def get_client_sync() -> MCPClientManager | None:
    """Get the client synchronously (must be initialized first)."""
    return _client
