#!/usr/bin/env python3
"""
Unit tests for utils.access_nested_map using parameterized inputs.
"""
from typing import Any, Mapping, Sequence
import unittest
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

