"""Application cache."""
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from retrocookie import git
from retrocookie.pr.compat import contextlib


# Windows does not properly support files and directories longer than
# 260 characters. Use a smaller digest size on this platform.
DIGEST_SIZE: int = 64 if sys.platform != "win32" else 32


@dataclass
class Cache:
    """Application cache."""

    path: Path

    def save_token(self, token: str) -> None:
        """Save a token."""
        data = {"token": token}
        text = json.dumps(data)
        path = self.path / "token.json"
        path.parent.mkdir(exist_ok=True, parents=True)
        path.touch(mode=0o600)
        path.write_text(text)

    def load_token(self) -> str:
        """Load a token."""
        path = self.path / "token.json"
        text = path.read_text()
        data = json.loads(text)
        token = data["token"]
        if not isinstance(token, str):
            raise TypeError("invalid token")
        return token

    def _repository_path(self, url: str) -> Path:
        h = hashlib.blake2b(url.encode(), digest_size=DIGEST_SIZE).hexdigest()
        return self.path / "repositories" / h[:2] / h[2:] / "repo.git"

    def repository(self, url: str) -> git.Repository:
        """Clone or update repository."""
        path = self._repository_path(url)

        if not path.exists():
            return git.Repository.clone(url, path, mirror=True)

        repository = git.Repository(path)
        repository.update_remote()
        return repository

    @contextlib.contextmanager
    def worktree(
        self,
        repository: git.Repository,
        branch: str,
        *,
        base: str = "HEAD",
        force: bool = False,
    ) -> Iterator[git.Repository]:
        """Context manager to add and remove a worktree."""
        assert self.path in repository.path.parents  # noqa: S101
        path = repository.path.parent / "worktrees" / branch

        with repository.worktree(
            branch, path, base=base, force=force, force_remove=True
        ) as worktree:
            yield worktree
