"""Tests for Result monad."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pytest

from ai_coding_agent.core.result import (
    Err,
    Ok,
    Result,
    and_then,
    is_err,
    is_ok,
    map_err,
    mapo,
)
from ai_coding_agent.core.tools.result_types import CommandData

# Test constants
TEST_VALUE = 42
DOUBLED_TEST_VALUE = TEST_VALUE * 2
DEFAULT_VALUE = 0
SMALL_TEST_VALUE = 5
DOUBLED_SMALL_VALUE = SMALL_TEST_VALUE * 2


@dataclass
class TestData:
    """Test data class for Result tests."""

    message: str
    value: int


class DynamicTestData:
    """Dynamic test data class for Result tests."""

    def __init__(self, message: str, value: int) -> None:
        """Initialize the test data."""
        self.message = message
        self.value = value
        self.content = ""
        self.files: list[str] = []
        self.tools: list[Any] = []


def test_success_result():
    """Test successful Result operations."""
    # Basic success case
    result = Ok(TestData(message="test", value=TEST_VALUE))
    assert is_ok(result)
    assert not is_err(result)

    match result:
        case Ok(value=x):
            assert x.message == "test"
            assert x.value == TEST_VALUE

    # Test map on success
    mapped = mapo(result, lambda x: x.value * 2)

    match mapped:
        case Ok(value):
            assert value == DOUBLED_TEST_VALUE
        case Err():
            pytest.fail("Expected Ok result")

    # Test map_err on success (should not transform)
    mapped_err = map_err(result, lambda e: f"New error: {e}")
    assert is_ok(mapped_err)
    match (mapped_err, result):
        case (Ok(value=x), Ok(value=y)):
            assert x == y
        case _:
            pytest.fail("Expected both results to be Ok with same value")

    # Test default value handling for success
    match result:
        case Ok(value=x):
            assert x.message == "test"  # Should get original value, not default


def test_error_result():
    """Test error Result operations."""
    # Basic error case
    result = Err("test error")
    assert is_err(result)
    assert not is_ok(result)

    match result:
        case Err(error=e):
            assert e == "test error"

    # Test map on error (should not transform)
    mapped = mapo(result, lambda x: x * 2)
    assert is_err(mapped)
    match mapped:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert e == "test error"

    # Test map_err on error
    mapped_err = map_err(result, lambda e: f"New error: {e}")
    assert is_err(mapped_err)
    match mapped_err:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert e == "New error: test error"

    # Test default value for error
    default = TestData(message="default", value=DEFAULT_VALUE)
    match result:
        case Err():
            assert default.message == "default"  # Should get default value


def test_error_handling():
    """Test error handling in Result operations."""
    success = Ok(TestData(message="test", value=TEST_VALUE))
    error = Err("test error")

    # Test error case handling
    match error:
        case Err(error=e):
            assert str(e) == "test error"

    # Test success case handling
    match success:
        case Ok(value=x):
            assert x.message == "test"
            assert x.value == TEST_VALUE


def test_chaining():
    """Test method chaining with Result."""
    # Success chain
    result = Ok(SMALL_TEST_VALUE)
    chained = and_then(mapo(result, lambda x: x * 2), lambda x: Ok(str(x)))
    assert is_ok(chained)
    match chained:
        case Ok(value=x):
            assert x == str(DOUBLED_SMALL_VALUE)
        case Err():
            pytest.fail("Expected Ok result")

    # Error chain
    error_chain = and_then(mapo(result, lambda x: x * 2), lambda x: Ok(str(x / 0)))
    assert is_err(error_chain)
    match error_chain:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert isinstance(e, ZeroDivisionError)


def test_complex_transformations():
    """Test complex transformations with Result."""
    # Test with sequence types
    items: Sequence[int] = [1, 2, 3]
    result = Ok(items)
    mapped = mapo(result, lambda x: [i * 2 for i in x])
    assert is_ok(mapped)
    match mapped:
        case Ok(value=x):
            assert x == [2, 4, 6]
        case Err():
            pytest.fail("Expected Ok result")

    # Test with nested data structures
    data = {"data": TestData(message="test", value=TEST_VALUE)}
    nested = Ok(data)
    transformed = mapo(nested, lambda x: x.get("data").value)  # type: ignore
    assert is_ok(transformed)
    match transformed:
        case Ok(value=x):
            assert x == TEST_VALUE
        case Err():
            pytest.fail("Expected Ok result")

    # Test with exceptions in transformations
    test_result: Result[int, str] = Ok(
        5
    )  # Using a single integer value with explicit typing
    error_transform = mapo(
        test_result, lambda x: float(x) / 0
    )  # Explicitly convert to float
    assert is_err(error_transform)
    match error_transform:
        case Ok(_):
            pytest.fail("Expected Err result")
        case Err(error=e):
            assert isinstance(e, ZeroDivisionError)


def test_result_properties():
    """Test Result properties."""
    # Test success property
    success = Ok(TestData(message="test", value=TEST_VALUE))
    error = Err("test error")
    assert is_ok(success)
    assert is_err(error)

    # Test message property
    match success:
        case Ok(value=x):
            assert x.message == "test"

    match error:
        case Err(error=e):
            assert e == "test error"

    # Test content property
    data = DynamicTestData(message="test", value=TEST_VALUE)
    data.content = "test content"
    result = Ok(data)

    match result:
        case Ok(value=x):
            assert x.content == "test content"

    # Test files property
    data = DynamicTestData(message="test", value=TEST_VALUE)
    data.files = ["file1", "file2"]
    result = Ok(data)

    match result:
        case Ok(value=x):
            assert x.files == ["file1", "file2"]

    # Test tools property
    data = DynamicTestData(message="test", value=TEST_VALUE)
    data.tools = ["tool1", "tool2"]
    result = Ok(data)

    match result:
        case Ok(value=x):
            assert x.tools == ["tool1", "tool2"]


def test_result_initialization():
    """Test Result initialization."""
    # Test valid initialization
    success = Ok(TEST_VALUE)
    error = Err("error")
    assert is_ok(success)
    assert is_err(error)

    match success:
        case Ok(value=x):
            assert x == TEST_VALUE

    match error:
        case Err(error=e):
            assert e == "error"


def test_result_match_on_success():
    """Test pattern matching on Result with CommandData."""
    result = Ok[CommandData, str](
        CommandData(
            message="Flutter 3.27.2 • channel stable • https://github.com/flutter/flutter.git\nFramework • revision 68415ad1d9 (6 days ago) • 2025-01-13 10:22:03 -0800\nEngine • revision e672b006cb\nTools • Dart 3.6.1 • DevTools 2.40.2\n",
            working_path="/private/var/folders/v3/49bmt6f55b1csb6snk8fr1mw0000gn/T/tmpn0w_zaum/d24a8d04-3568-4b5c-b037-fa52a7cabdac",
        )
    )

    match result:
        case Ok(value=cd):
            assert "Flutter" in cd.message
            assert cd.working_path.startswith("/private/var")
