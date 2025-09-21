#!/usr/bin/env python3
"""
Unit tests for utils.access_nested_map and utils.get_json using parameterized inputs
and mocking for HTTP calls.
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


if __name__ == "__main__":
    unittest.main()

