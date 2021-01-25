"""Protocol for retrocookie.retrocookie."""
from pathlib import Path

from retrocookie.pr.compat.typing import Protocol


class Retrocookie(Protocol):
    """The retrocookie function."""

    def __call__(
        self, repository: Path, *, branch: str, upstream: str, path: Path
    ) -> None:
        """Import commits from instance repository into template repository."""
