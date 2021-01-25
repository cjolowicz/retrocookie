"""Event bus.

This module defines a :class:`Bus` class for publishing events and subscribing
handlers to them.

Events must derive from :class:`Event`. Handlers are functions that take the
event as an argument. The function must have type annotations, to allow the bus
to determine which handlers to invoke when an event is published.

>>> class Timber(Event):
...     pass
...
... def shout(event: Timber):
...     print("Timber!")
...
... bus = Bus()
... bus.events.subscribe(shout)
>>> bus.events.publish(Timber())
Timber!

Events can be raised on the bus. A raised event is wrapped in an :class:Error
exception, causing the stack to unwind until an error handler is encounted.

>>> try:
...     with bus.events.errorhandler():
...         bus.events.raise_(Timber())
... except Error:
...     pass
Timber!

The error handler places the event on the bus, but it does not suppress the
exception.

Contexts are a special kind of event that has a duration. Handlers for contexts
must return a context manager, which is invoked on entering and exiting the
context.

>>> class Copy(Context):
...     pass
...
... import contextlib
...
... @contextlib.contextmanager
... def handle_copy(context: Copy):
...     print("starting copy...")
...     try:
...         yield
...     except Exception:
...         print("copy failed!")
...         raise
...     else:
...         print("copy complete.")
...
... bus.contexts.subscribe(handle_copy)
>>> with bus.contexts.publish(Copy()):
...     print("copy: file a")
...     print("copy: file b")
starting copy...
copy: file a
copy: file b
copy complete.
"""
from collections import defaultdict
from contextlib import ExitStack
from typing import Any
from typing import ContextManager
from typing import Dict
from typing import get_type_hints
from typing import Iterator
from typing import List
from typing import NoReturn
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.base.exceptionhandlers import exceptionhandler
from retrocookie.pr.compat.contextlib import contextmanager
from retrocookie.pr.compat.typing import Protocol


__all__ = [
    "Bus",
    "Context",
    "Error",
    "Event",
]


class Event:
    """An event can be published on the bus, and subscribed to."""


class Context:
    """A context is an event with a duration."""


class Error(Exception):
    """An exception for transporting an event."""

    def __init__(self, event: Event) -> None:
        """Initialize."""
        self.event = event


E = TypeVar("E", bound=Event, contravariant=True)
C = TypeVar("C", bound=Context, contravariant=True)


class _EventHandler(Protocol[E]):
    """Handler for an event."""

    def __call__(self, event: E) -> None:
        """Invoke the handler."""


class _ContextHandler(Protocol[C]):
    """Handler for a context."""

    def __call__(self, context: C) -> ContextManager[None]:
        """Invoke the handler."""


class _Events:
    """Publish and subscribe to events."""

    def __init__(self) -> None:
        """Initialize."""
        self.handlers: Dict[
            Type[Event],
            List[_EventHandler[Any]],
        ] = defaultdict(list)

    def publish(self, event: Event) -> None:
        """Publish an event on the bus."""
        handlers = self.handlers[type(event)]
        for handler in handlers:
            handler(event)

    def subscribe(self, handler: _EventHandler[E]) -> _EventHandler[E]:
        """Subscribe to an event."""
        event_type = next(hint for hint in get_type_hints(handler).values())
        self.handlers[event_type].append(handler)
        return handler

    def raise_(self, event: Event) -> NoReturn:
        """Raise an event."""
        raise Error(event)

    def reraise(
        self,
        event: Event,
        *,
        when: Union[Type[BaseException], Tuple[Type[BaseException], ...]] = (),
    ) -> ExceptionHandler:
        """Raise an event when an exception is caught."""
        if not isinstance(when, tuple):
            when = (when,)
        elif not when:
            when = (Exception,)

        @exceptionhandler(*when)
        def _(exception: BaseException) -> NoReturn:
            raise Error(event)

        return _

    def errorhandler(self) -> ExceptionHandler:
        """Publish error events on the bus."""

        @exceptionhandler
        def _(error: Error) -> None:
            self.publish(error.event)

        return _


class _Contexts:
    """Publish and subscribe to contexts."""

    def __init__(self) -> None:
        """Initialize."""
        self.handlers: Dict[
            Type[Context],
            List[_ContextHandler[Any]],
        ] = defaultdict(list)

    @contextmanager
    def publish(self, event: Context) -> Iterator[None]:
        """Publish a context."""
        handlers = self.handlers[type(event)]
        with ExitStack() as stack:
            for handler in handlers:
                stack.enter_context(handler(event))
            yield

    def subscribe(self, handler: _ContextHandler[C]) -> _ContextHandler[C]:
        """Subscribe to a context."""
        event_type = next(hint for hint in get_type_hints(handler).values())
        self.handlers[event_type].append(handler)
        return handler


class Bus:
    """Event bus."""

    def __init__(self) -> None:
        """Initialize."""
        self.events = _Events()
        self.contexts = _Contexts()
