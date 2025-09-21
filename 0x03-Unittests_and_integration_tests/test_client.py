#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient.org using parameterized inputs and patching.

This test verifies that:
- GithubOrgClient.org (a memoized property) returns the value provided by get_json
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

    @patch("client.get_json")
    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    def test_org(self, mock_get_json: Mock, org_name: str) -> None:
        """
        Test that GithubOrgClient.org returns the expected payload and that
        get_json is called exactly once with the correct URL.

        Note:
        - `org` is a memoized property, so access it as `github_client.org`,
          not `github_client.org()`.
        - patch is applied above parameterized.expand so the mock is injected
          as the first argument.
        """
        expected_payload: Any = {"org": org_name}
        mock_get_json.return_value = expected_payload

        github_client = client.GithubOrgClient(org_name)
        result = github_client.org  # access property, not call

        mock_get_json.assert_called_once_with(
            client.GithubOrgClient.ORG_URL.format(org=org_name)
        )
        self.assertEqual(result, expected_payload)


if __name__ == "__main__":
    unittest.main()

