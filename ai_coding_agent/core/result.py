"""Result monad for handling success/error cases.

This module provides a Result monad that encapsulates success and error values,
allowing for safe error handling and chaining of operations.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar, cast, final

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # New success type for map operations


@final
@dataclass
class Ok(Generic[T, E]):
    """Success variant of Result."""

    value: T

    def __str__(self) -> str:
        """Return a string representation of the success value."""
        return f"Ok({self.value})"


@final
@dataclass
class Err(Generic[T, E]):
    """Error variant of Result."""

    error: E

    def __str__(self) -> str:
        """Return a string representation of the error value."""
        return f"Err({self.error})"


# Define Result as a proper type alias using the 'type' keyword
type Result[T, E] = Ok[T, E] | Err[T, E]


def is_ok(result: Result[T, E]) -> bool:
    """Check if the Result is successful."""
    return isinstance(result, Ok)


def is_err(result: Result[T, E]) -> bool:
    """Check if the Result is an error."""
    return isinstance(result, Err)


def on_error(result: Result[T, E], f: Callable[[E], None]) -> None:
    """Call a function if the result is an error."""
    match result:
        case Ok():
            pass
        case Err(error=e):
            f(e)


def mapo(result: Result[T, E], f: Callable[[T], U]) -> Result[U, E]:
    """Apply a function to the success value if present."""
    match result:
        case Ok(value=x):
            try:
                return Ok(f(x))
            except Exception as e:
                return Err(cast(E, e))
        case Err(error=e):
            return Err[U, E](e)


def map_err(result: Result[T, E], f: Callable[[E], E]) -> Result[T, E]:
    """Apply a function to the error value if present."""
    match result:
        case Ok():
            return result
        case Err(error=e):
            return Err(f(e))


def and_then(result: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
    """Chain operations that might fail."""
    match result:
        case Ok(value=x):
            try:
                return f(x)
            except Exception as e:
                return Err(cast(E, e))
        case Err(error=e):
            return Err[U, E](e)


def either(result: Result[T, T]) -> T:
    """Use this for cases where the error type is the same as the success type."""
    match result:
        case Ok(value=x):
            return x
        case Err(error=e):
            return e


def unwrap(result: Result[T, E]) -> T:
    """Don't use this! It can cause exceptions. Use pattern matching. Get the success value or raise an exception if it's an error."""
    match result:
        case Ok(value=x):
            return x
        case Err(error=e):
            raise ValueError(f"Cannot unwrap error result: {e}")


@dataclass
class TaskOutput:
    """Data class for task output results."""

    correlation_id: str | None
    output_message: str
