#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient.org using parameterized inputs and patching.

This test verifies that:
- GithubOrgClient.org() returns the value provided by get_json
- get_json is called exactly once with the expected URL
No external HTTP calls are made because get_json is patched.
"""

from typing import Any
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized

import client


class TestGithubOrgClient(unittest.TestCase):
    """Tests for GithubOrgClient.org method."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org_name: str, mock_get_json: Mock) -> None:
        """
        Test that GithubOrgClient.org returns the expected payload and that
        get_json is called exactly once with the correct URL.
        """
        expected_payload: Any = {"org": org_name}
        mock_get_json.return_value = expected_payload

        github_client = client.GithubOrgClient(org_name)
        result = github_client.org()

        mock_get_json.assert_called_once_with(client.GithubOrgClient.ORG_URL.format(org=org_name))
        self.assertEqual(result, expected_payload)


if __name__ == "__main__":
    unittest.main()

