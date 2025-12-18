"""Configuration for Harness agent."""

from dataclasses import dataclass, field
from pathlib import Path
import json
import os


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MCPServerConfig":
        return cls(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env")
        )


# Default MCP servers - filesystem is essential for a coding agent
# Using npx to run the official Anthropic MCP filesystem server
# Use /tmp for K8s jobs (writable), or home directory for local dev
FILESYSTEM_ROOT = os.getenv("FILESYSTEM_ROOT", "/tmp")
DEFAULT_MCP_SERVERS = [
    {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", FILESYSTEM_ROOT]
    }
]

# Add Contrast MCP if credentials are configured
if os.getenv("CONTRAST_API_KEY"):
    DEFAULT_MCP_SERVERS.append({
        "name": "contrast",
        "command": "java",
        "args": ["-jar", "/opt/mcp-contrast.jar", "-t", "stdio"],
        "env": {
            "CONTRAST_HOST_NAME": os.getenv("CONTRAST_HOST_NAME", ""),
            "CONTRAST_API_KEY": os.getenv("CONTRAST_API_KEY", ""),
            "CONTRAST_ORG_ID": os.getenv("CONTRAST_ORG_ID", ""),
            "CONTRAST_SERVICE_KEY": os.getenv("CONTRAST_SERVICE_KEY", ""),
            "CONTRAST_USERNAME": os.getenv("CONTRAST_USERNAME", ""),
        }
    })


@dataclass
class Config:
    chat_model: str = "codestral:22b-v0.1-q8_0"
    max_steps: int = 20
    max_context_tokens: int = 28000  # Leave headroom in 32k window
    mcp_servers: list[dict] = field(default_factory=lambda: DEFAULT_MCP_SERVERS.copy())

    @classmethod
    def load(cls) -> "Config":
        """Load config from environment, then ~/.harness/config.json, then defaults.

        Environment variables take precedence over config file.
        """
        # Start with defaults
        chat_model = "codestral:22b-v0.1-q8_0"
        max_steps = 20
        max_context_tokens = 28000
        mcp_servers = DEFAULT_MCP_SERVERS.copy()

        # Load from config file if exists
        config_path = Path.home() / ".harness" / "config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                chat_model = data.get("chat_model", chat_model)
                max_steps = data.get("max_steps", max_steps)
                max_context_tokens = data.get("max_context_tokens", max_context_tokens)
                mcp_servers = data.get("mcp_servers", mcp_servers)
            except (json.JSONDecodeError, TypeError):
                pass

        # Environment variables override (for K8s ConfigMaps)
        chat_model = os.getenv("CHAT_MODEL", chat_model)
        max_steps = int(os.getenv("MAX_STEPS", max_steps))
        max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", max_context_tokens))

        return cls(
            chat_model=chat_model,
            max_steps=max_steps,
            max_context_tokens=max_context_tokens,
            mcp_servers=mcp_servers
        )

    def get_mcp_servers(self) -> list[MCPServerConfig]:
        """Get MCP server configs."""
        return [MCPServerConfig.from_dict(s) for s in self.mcp_servers]

    def save(self) -> None:
        """Save config to ~/.harness/config.json."""
        config_dir = Path.home() / ".harness"
        config_dir.mkdir(exist_ok=True)
        config_path = config_dir / "config.json"
        data = {
            "chat_model": self.chat_model,
            "max_steps": self.max_steps,
            "max_context_tokens": self.max_context_tokens,
            "mcp_servers": self.mcp_servers
        }
        config_path.write_text(json.dumps(data, indent=2))
