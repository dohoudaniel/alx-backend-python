#!/usr/bin/env python3
"""
Unit tests for utils.access_nested_map, utils.get_json, and utils.memoize.

This file contains three test classes:
- TestAccessNestedMap: parameterized tests for access_nested_map (normal and error cases)
- TestGetJson: parameterized tests for get_json (requests.get is patched)
- TestMemoize: tests the memoize decorator to ensure the wrapped method is called only once
"""

from typing import Any, Mapping, Sequence
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized

import utils


class TestAccessNestedMap(unittest.TestCase):
    """Test cases for utils.access_nested_map."""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map: Mapping, path: Sequence, expected: Any) -> None:
        """access_nested_map should return the expected value for given path."""
        self.assertEqual(utils.access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "'a'"),
        ({"a": 1}, ("a", "b"), "'b'"),
    ])
    def test_access_nested_map_exception(self, nested_map: Mapping, path: Sequence, expected: Any) -> None:
        """access_nested_map should raise KeyError with the correct message for invalid paths."""
        with self.assertRaises(KeyError) as ctx:
            utils.access_nested_map(nested_map, path)
        self.assertEqual(str(ctx.exception), expected)


class TestGetJson(unittest.TestCase):
    """Tests for the get_json function (network call mocked)."""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(self, test_url: str, test_payload: Any) -> None:
        """
        get_json should call requests.get once with the URL and return the json payload.
        Uses mocking to avoid external HTTP calls.
        """
        with patch("utils.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = test_payload
            mock_get.return_value = mock_response

            result = utils.get_json(test_url)

            mock_get.assert_called_once_with(test_url)
            self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Tests for the memoize decorator."""

    def test_memoize(self) -> None:
        """memoize should cache the result and avoid multiple calls to the underlying method."""
        class TestClass:
            """Helper class to test memoization behavior."""

            def a_method(self) -> int:
                """Method intended to be patched in the test."""
                return 42

            @utils.memoize
            def a_property(self) -> int:
                """Property that depends on a_method and should be memoized."""
                return self.a_method()

        # Patch TestClass.a_method so we can count calls
        with patch.object(TestClass, "a_method", return_value=42) as mock_method:
            obj = TestClass()
            # First access computes and caches the value (calls a_method once)
            self.assertEqual(obj.a_property, 42)
            # Second access returns cached value and should NOT call a_method again
            self.assertEqual(obj.a_property, 42)
            mock_method.assert_called_once()


if __name__ == "__main__":
    unittest.main()

