"""Exception handlers as first-class citizens.

The utilities in this module allow the creation of exception handlers as
first-class objects that can be passed around and combined.

Consider the following imaginary application:

>>> class ApplicationError(Exception):
...     pass
...
... def main():
...     pass

Conventionally, application errors would be handled using a ``try...except``
block:

>>> try:
...     main()
... except ApplicationError as error:
...     sys.exit(f"fatal: {error}")

Instead, this module lets you create an exception handler object:

>>> @exceptionhandler(ApplicationError)
... def fatal(error):
...     sys.exit(f"fatal: {error}")

The :func:`exceptionhandler` decorator creates an instance of
:class:`ExceptionHandler`, a context manager that invokes the wrapped function
when an exception of type ApplicationError is caught.

The exception handler can now be used anywhere in the code, like this:

>>> with fatal:
...     main()

Exception handlers can also be used as decorators to apply exception handling to
a function. So instead of wrapping every call to ``main`` in a ``with``
statement, you could apply the exception handler to ``main`` once:

>>> @fatal
... def main():
...     ...

If your code uses type annotations, you can omit the arguments to
``exceptionhandler``, and define the handler like this:

>>> @exceptionhandler
... def fatal(error: ApplicationError):
...     sys.exit(f"fatal: {error}")

An important difference between an ``except`` clause and an ``ExceptionHandler``
is that ``except`` clauses suppress exceptions by default, and require an
explicit ``raise`` statement to re-raise the exception. By contrast, exception
handlers re-raise exceptions by default, and require an explicit ``return True``
statement to suppress the exception:

>>> @exceptionhandler(Exception)
... def suppress(exception):
...     return True

Exception handlers can be combined using the ``<<`` and ``>>`` operators:

>>> with fatal >> suppress:
...     ...

The operator points in the direction of exception flow, so in this example
``fatal`` sees exceptions before ``suppress``; in other words, the code exits on
application errors, while any remaining exceptions are silently discarded.

In general, ``a >> b`` is equivalent to ``b << a``. For example, the code above
could also have been written like this:

>>> with suppress << fatal:
...     ...

This style is closer to how the code would look with multiple context managers:

>>> with suppress, fatal:
...     ...

While this form is shorter, composing exception handlers explicitly gives us an
``ExceptionHandler`` object. The combined exception handler can be stored in a
variable, passed around, or combined with further handlers:

>>> handler = fatal >> suppress

This module defines only one actual exception handler of its own:
``nullhandler`` is a noop that does not handle any exceptions. A practical use
of ``nullhandler`` is when exception handling should be optional, letting you
either pass the real handler or ``nullhandler``.

In algebraic terms, ``nullhandler`` is the identity element of composition
(``<<`` and ``>>``): Combining any handler with ``nullhandler`` gives you a
handler that behaves exactly like the original handler. As composition is also
associative, this makes exception handlers with composition a simple monoid_.

.. _monoid: https://en.wikipedia.org/wiki/Monoid
"""
from __future__ import annotations

import contextlib
from types import TracebackType
from typing import Callable
from typing import Generic
from typing import get_type_hints
from typing import List
from typing import Optional
from typing import overload
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union


__all__ = [
    "ExceptionHandler",
    "exceptionhandler",
    "nullhandler",
]


class ExceptionHandler(contextlib.ContextDecorator):
    """Context manager for handling exceptions.

    Apply exception handlers to a block of code using a with block::

        with myhandler:
            ...

    Note that there are no parentheses, because there is no need to invoke the
    exception handler. Exception handlers are `reentrant context managers`_,
    which means that you do not need to create them afresh for each use, even
    when they are used multiple times in nested ``with`` statements.

    .. _reentrant context managers:
       https://docs.python.org/3/library/contextlib.html
       #single-use-reusable-and-reentrant-context-managers

    Exception handlers can also be used as decorators::

        @myhandler
        def f():
            ...

    This is equivalent to enclosing the body of the function in a ``with``
    block::

        def f():
            with myhandler:
                ...

    This class should not be instantiated directly. Use the
    :func:`exceptionhandler` decorator to create an exception handler.
    """

    def __enter__(self) -> None:
        """Enter the runtime context."""

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Exit the runtime context."""
        return None

    def __lshift__(self, other: ExceptionHandler) -> ExceptionHandler:
        """Compose this exception handler with another one.

        The expression ``a << b`` is equivalent to these nested ``with``
        blocks::

            with a:
                with b:
                    ...

        As a mnemonic, the operator points in the direction of exception flow.
        In ``a << b``, the right operand sees the exception first.
        """
        return _Compose(self, other)

    def __rshift__(self, other: ExceptionHandler) -> ExceptionHandler:
        """Compose this exception handler with another one.

        The expression ``a >> b`` is equivalent to these nested ``with``
        blocks::

            with b:
                with a:
                    ...

        As a mnemonic, the operator points in the direction of exception flow.
        In ``a >> b``, the left operand sees the exception first.
        """
        return other << self


nullhandler = ExceptionHandler()


class _Compose(ExceptionHandler):
    """Exception handler composed of other exception handlers."""

    def __init__(self, first: ExceptionHandler, second: ExceptionHandler) -> None:
        """Initialize."""
        # Reduce object count in expressions like ``a << b << c``.
        self.stacks: List[contextlib.ExitStack] = []
        self.handlers: List[ExceptionHandler] = [
            handler
            for arg in (first, second)
            for handler in (arg.handlers if isinstance(arg, _Compose) else [arg])
        ]

    def __enter__(self) -> None:
        """Enter the runtime context."""
        stack = contextlib.ExitStack()
        self.stacks.append(stack)

        for handler in self.handlers:
            stack.enter_context(handler)

        stack.__enter__()

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Exit the runtime context."""
        stack = self.stacks.pop()
        return stack.__exit__(exception_type, exception, traceback)


E = TypeVar("E", bound=BaseException, contravariant=True)


_Callback = Callable[[E], Optional[bool]]


class _Decorator(Generic[E], ExceptionHandler):
    """Exception handler wrapping a callback function.

    This class is a helper for the @exceptionhandler decorator.
    """

    def __init__(
        self,
        callback: _Callback[E],
        *exception_types: Type[BaseException],
    ) -> None:
        """Initialize."""
        self.callback = callback
        self.exception_types = exception_types

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Exit the context."""
        return (
            self.callback(exception)  # type: ignore[arg-type]
            if any(
                isinstance(exception, exception_type)
                for exception_type in self.exception_types
            )
            else None
        )


def _exceptionhandler(
    *exception_types: Type[BaseException],
) -> Callable[[_Callback[E]], ExceptionHandler]:
    """Decorator factory implementing @exceptionhandler."""

    def _decorator(callback: _Callback[E]) -> ExceptionHandler:
        if exception_types:
            return _Decorator(callback, *exception_types)

        try:
            exception_type = next(
                hint
                for key, hint in get_type_hints(callback).items()
                if key != "return"
            )
        except StopIteration:
            raise TypeError(f"missing type annotation on {callback}") from None

        return _Decorator(callback, exception_type)

    return _decorator


@overload
def exceptionhandler(__callback: _Callback[E]) -> ExceptionHandler:
    """Overload for the plain decorator."""


@overload
def exceptionhandler(
    *exception_types: Type[BaseException],
) -> Callable[[_Callback[E]], ExceptionHandler]:
    """Overload for the decorator factory."""


def exceptionhandler(
    *args: Union[_Callback[E], Type[BaseException]],
) -> Union[ExceptionHandler, Callable[[_Callback[E]], ExceptionHandler]]:
    """Decorator for creating exception handlers.

    This decorator creates an exception handler that invokes the wrapped
    function when an exception of the specified type is caught::

        @exceptionhandler(SomeError)
        def handler(error):
            return True

    Multiple exception types may be specified, or none. In the latter case, the
    exception type is derived from the type annotation for the function
    parameter. Parentheses for the decorator are optional in this case. The
    following example is equivalent to the first one::

        @exceptionhandler
        def handler(error: SomeError) -> bool:
            return True

    A return value of True suppresses the exception. If the function returns
    False or None, the exception is reraised when the handler returns::

        @exceptionhandler
        def print_handler(exception: SomeException) -> None:
            print(exception)  # the exception is printed but not swallowed

    Another option is to raise another exception::

        @exceptionhandler
        def exit_handler(exception: SomeException) -> NoReturn:
            raise SystemExit(str(exception))

    """
    if all(isinstance(arg, type) and issubclass(arg, BaseException) for arg in args):
        exception_types: Tuple[Type[BaseException]] = args  # type: ignore[assignment]
        return _exceptionhandler(*exception_types)

    callback: _Callback[E]
    [callback] = args  # type: ignore[assignment]
    return _exceptionhandler()(callback)
