"""Entry point for Harness agent."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .agent import run_session_async, _build_system_prompt
from .config import Config
from .mcp_client import MCPClientManager, MCPServer, initialize as init_mcp
from .tools import NATIVE_TOOLS

# Load .env from project root (supports both local dev and installed package)
load_dotenv(Path(__file__).parent.parent / ".env")


def save_output(content: str) -> None:
    """Save output to file if HARNESS_OUTPUT_DIR is set."""
    output_dir = os.getenv("HARNESS_OUTPUT_DIR")
    job_id = os.getenv("HARNESS_JOB_ID", "unknown")

    if output_dir:
        output_path = Path(output_dir) / f"{job_id}.txt"
        output_path.write_text(content)
        print(f"Output saved to {output_path}")

async def main_async():
    """Async main function."""
    config = Config.load()

    # Initialize MCP servers
    print("Connecting to MCP servers...")
    servers = [
        MCPServer(name=s.name, command=s.command, args=s.args, env=s.env)
        for s in config.get_mcp_servers()
    ]

    try:
        mcp = await init_mcp(servers)
    except Exception as e:
        print(f"Error connecting to MCP servers: {e}")
        print("Make sure you have npx/node installed for MCP servers.")
        return

    if not mcp.tools:
        print("Warning: No tools available. Check MCP server configuration.")

    # If arguments provided, run as single command
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        messages = [{"role": "system", "content": ""}]
        try:
            result = await run_session_async(task, messages, mcp, config)
            save_output(result or "")
        finally:
            await mcp.close()
        return

    # Interactive REPL with persistent session
    print(f"\nHarness - Local Code Agent")
    print(f"Model: {config.chat_model}")
    print(f"Tools: {len(mcp.tools)} available")
    print("Type /help for commands\n")

    # Session state
    messages = [{"role": "system", "content": ""}]

    try:
        while True:
            try:
                task = input(">>> ").strip()

                if not task:
                    continue

                # Commands start with /
                if task.startswith("/"):
                    cmd = task[1:].lower().split()[0]

                    if cmd in ("quit", "exit", "q"):
                        print("Goodbye!")
                        break

                    elif cmd == "clear":
                        messages = [{"role": "system", "content": ""}]
                        print("Context cleared.\n")
                        continue

                    elif cmd == "context":
                        user_msgs = [m for m in messages if m["role"] == "user"]
                        tool_results = [m for m in messages if m["role"] == "user" and m.get("content", "").startswith("Tool result:")]
                        print(f"  Messages: {len(messages)}")
                        print(f"  Your inputs: {len(user_msgs) - len(tool_results)}")
                        print(f"  Tool calls: {len(tool_results)}")
                        chars = sum(len(m.get("content", "")) for m in messages)
                        print(f"  Est. tokens: ~{chars // 4}")
                        print()
                        continue

                    elif cmd == "tools":
                        print("\n--- MCP Tools ---")
                        for name, tool in mcp.tools.items():
                            print(f"  {name}: {tool.description[:60]}...")
                        print("\n--- Native Tools ---")
                        for name, tool in NATIVE_TOOLS.items():
                            print(f"  {name}: {tool.description[:60]}...")
                        print("---\n")
                        continue

                    elif cmd == "index":
                        parts = task.split(maxsplit=1)
                        directory = parts[1] if len(parts) > 1 else "."
                        print(f"Indexing {directory}...")
                        from .indexer import index_directory
                        try:
                            count = index_directory(directory)
                            print(f"Done! Indexed {count} chunks.\n")
                        except Exception as e:
                            print(f"Error indexing: {e}\n")
                        continue

                    elif cmd == "history":
                        print("\n--- Recent History ---")
                        for m in messages[-10:]:
                            role = m["role"]
                            content = m.get("content", "")[:100]
                            if role == "system":
                                continue
                            prefix = {"user": "You", "assistant": "Agent"}.get(role, role)
                            print(f"[{prefix}] {content}{'...' if len(m.get('content', '')) > 100 else ''}")
                        print("---\n")
                        continue

                    elif cmd == "config":
                        print(f"  chat_model: {config.chat_model}")
                        print(f"  max_steps: {config.max_steps}")
                        print(f"  mcp_servers: {[s['name'] for s in config.mcp_servers]}")
                        print()
                        continue

                    elif cmd == "help":
                        print("""
Commands:
  /clear      - Clear conversation context (start fresh)
  /context    - Show context stats (message count, tokens)
  /tools      - List available tools (MCP and native)
  /index [dir]- Index a directory for semantic search
  /history    - Show recent conversation history
  /config     - Show current config
  /quit       - Exit the REPL

Just type your request to interact with the agent.
The agent remembers previous turns until you /clear.
""")
                        continue

                    else:
                        print(f"Unknown command: /{cmd}. Type /help for commands.\n")
                        continue

                # Regular task - run with session
                print()
                await run_session_async(task, messages, mcp, config)
                print()

            except KeyboardInterrupt:
                print("\nInterrupted. Type /quit to exit.")
            except Exception as e:
                print(f"Error: {e}")

    finally:
        await mcp.close()


def main():
    """Entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
