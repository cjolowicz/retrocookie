"""Compatibility shims for typing."""
import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

__all__ = ["Protocol"]
