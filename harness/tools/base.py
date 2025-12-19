"""Base class for native Python tools."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Base class for agent tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool and return result as string."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """Return JSON schema for parameters."""
        pass

    def to_doc(self) -> str:
        """Return documentation string for system prompt."""
        params = self.parameters.get("properties", {})
        param_docs = ", ".join(
            f'{p}: {info.get("type", "any")}'
            for p, info in params.items()
        )
        return f"- {self.name}({param_docs}): {self.description}"
