"""Compatibility shims for shlex."""
import sys

if sys.version_info >= (3, 8):
    from shlex import join
else:
    from shlex import quote
    from typing import Iterable

    def join(split_command: Iterable[str]) -> str:
        """Return a shell-escaped string from *split_command*."""
        return " ".join(quote(arg) for arg in split_command)


__all__ = ["join"]
