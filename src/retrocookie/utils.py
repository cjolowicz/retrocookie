"""Utilities."""
import contextlib
import os
from pathlib import Path
from typing import Iterator


def removeprefix(string: str, prefix: str) -> str:
    """Remove prefix from string, if present."""
    return string[len(prefix) :] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    """Remove suffix from string, if present."""
    return string[: -len(suffix)] if suffix and string.endswith(suffix) else string


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Context manager for changing the directory."""
    cwd = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cwd)
