"""
Repository domain model.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Repository:
    """Repository domain model."""

    name: str
    owner: str
    full_name: str

    def __post_init__(self):
        """Validate repository data after initialization."""
        if not self.name or not self.owner:
            raise ValueError("Repository name and owner are required")

        if not self.full_name:
            self.full_name = f"{self.owner}/{self.name}"

    @classmethod
    def from_string(cls, repo_string: str) -> "Repository":
        """Create Repository from string format 'owner/repo'."""
        if "/" not in repo_string:
            raise ValueError(f"Invalid repository format: {repo_string}")

        owner, name = repo_string.split("/", 1)
        return cls(name=name, owner=owner, full_name=repo_string)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "owner": self.owner,
            "full_name": self.full_name,
        }
