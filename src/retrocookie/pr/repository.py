"""High-level repository abstraction."""
from __future__ import annotations

from dataclasses import dataclass

from retrocookie import git
from retrocookie.pr.cache import Cache
from retrocookie.pr.protocols import github


@dataclass
class Repository:
    """High-level repository abstraction."""

    github: github.Repository
    clone: git.Repository

    @classmethod
    def load(
        cls,
        repository: str,
        *,
        api: github.API,
        cache: Cache,
    ) -> Repository:
        """Load all the data associated with a GitHub repository."""
        owner, name = repository.split("/", 1)
        github = api.repository(owner, name)
        clone = cache.repository(github.clone_url)
        return cls(github, clone)
