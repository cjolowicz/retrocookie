"""Compatibility shim for contextlib."""
import contextlib
from typing import Callable
from typing import ContextManager
from typing import Iterator
from typing import TypeVar


T = TypeVar("T")


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., ContextManager[T]]:
    """Fix annotations of functions decorated by contextlib.contextmanager."""
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": ContextManager[T]}
    return result
