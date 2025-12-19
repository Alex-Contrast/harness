"""Agent loop for Harness using MCP and native tools."""

import asyncio
import json
import os
import re
from ollama import Client
from .config import Config
from .mcp_client import MCPClientManager, MCPServer, initialize as init_mcp, get_client_sync
from .tools import NATIVE_TOOLS

# Initialize Ollama client with host from environment
ollama_client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))


def _get_native_tool_docs() -> str:
    """Get documentation for native Python tools."""
    return "\n".join(tool.to_doc() for tool in NATIVE_TOOLS.values())


def _build_system_prompt(mcp_tool_docs: str) -> str:
    """Build system prompt with available tools."""
    filesystem_root = os.getenv("FILESYSTEM_ROOT", "/tmp")
    native_docs = _get_native_tool_docs()

    all_tools = mcp_tool_docs
    if native_docs:
        all_tools = f"{mcp_tool_docs}\n{native_docs}" if mcp_tool_docs else native_docs

    return f"""You are a coding assistant with access to tools.

Available tools:
{all_tools}

To use a tool, respond with a JSON block:
```json
{{"tool": "tool_name", "args": {{"param": "value"}}}}
```

Rules:
- For file operations, use paths under {filesystem_root}
- Use semantic_search to find relevant code before making changes
- Use ONE tool at a time, wait for results
- When done or answering directly, respond normally WITHOUT json blocks
- Be concise"""


def _extract_tool_call(text: str) -> tuple[str, dict] | None:
    """Extract tool call from response text."""
    # Method 1: Look for code blocks
    code_block = re.search(r'```(?:json)?\s*(\{.+\})\s*```', text, re.DOTALL)
    if code_block:
        try:
            data = json.loads(code_block.group(1))
            if "tool" in data:
                return data["tool"], data.get("args", {})
        except json.JSONDecodeError:
            pass

    # Method 2: Find any JSON object with "tool" key
    start = text.find('{')
    while start != -1:
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict) and "tool" in data:
                            return data["tool"], data.get("args", {})
                    except json.JSONDecodeError:
                        pass
                    break
        start = text.find('{', start + 1)

    return None


async def run_session_async(
    task: str,
    messages: list,
    mcp: MCPClientManager,
    config: Config
) -> str:
    """Run a task within an existing session (async, modifies messages in place)."""
    system_prompt = _build_system_prompt(mcp.get_tool_docs())

    # Update system prompt if this is the first message
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] = system_prompt

    # Add user message
    messages.append({"role": "user", "content": task})

    for step in range(config.max_steps):
        response = ollama_client.chat(
            model=config.chat_model,
            messages=messages,
            stream=False
        )

        content = response.message.content or ""

        # Try to extract tool call
        tool_call = _extract_tool_call(content)

        if tool_call:
            name, args = tool_call
            messages.append({"role": "assistant", "content": content})

            print(f"  -> {name}({', '.join(f'{k}={repr(v)[:50]}' for k, v in args.items())})")

            # Check native tools first, then fall back to MCP
            if name in NATIVE_TOOLS:
                result = NATIVE_TOOLS[name].execute(**args)
            else:
                result = await mcp.call_tool(name, args)

            messages.append({"role": "user", "content": f"Tool result:\n{result}"})
        else:
            # No tool call = final response
            messages.append({"role": "assistant", "content": content})
            print(content)
            return content

    return "Error: Max steps reached without completion"


def run_session(task: str, messages: list, mcp: MCPClientManager, config: Config) -> str:
    """Sync wrapper for run_session_async."""
    return asyncio.get_event_loop().run_until_complete(
        run_session_async(task, messages, mcp, config)
    )


async def run_async(task: str, config: Config | None = None) -> str:
    """Run a single task (no session persistence)."""
    if config is None:
        config = Config.load()

    # Initialize MCP
    servers = [
        MCPServer(name=s.name, command=s.command, args=s.args, env=s.env)
        for s in config.get_mcp_servers()
    ]
    mcp = await init_mcp(servers)

    messages = [{"role": "system", "content": ""}]  # Will be set by run_session_async

    try:
        return await run_session_async(task, messages, mcp, config)
    finally:
        await mcp.close()


def run(task: str, config: Config | None = None) -> str:
    """Sync wrapper for run_async."""
    return asyncio.run(run_async(task, config))
