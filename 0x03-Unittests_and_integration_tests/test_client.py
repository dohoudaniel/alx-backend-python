#!/usr/bin/env python3
"""
Unit test for client.GithubOrgClient.org using parameterized inputs.

This test:
- parameterizes the org name (google, abc)
- patches client.get_json to avoid real HTTP calls (used as a context manager)
- asserts that get_json is called once with the expected URL
- asserts that the returned value matches the mocked payload
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
    def test_org(self, org_name: str) -> None:
        """Test that GithubOrgClient.org returns expected payload and calls get_json once."""
        expected_payload: Any = {"org": org_name}
        url = client.GithubOrgClient.ORG_URL.format(org=org_name)

        # Use patch as a context manager to avoid decorator-order issues
        with patch("client.get_json") as mock_get_json:
            mock_get_json.return_value = expected_payload

            github_client = client.GithubOrgClient(org_name)

            # Access the memoized property twice to ensure caching doesn't cause extra calls
            result1 = github_client.org
            result2 = github_client.org

            # Ensure get_json was called exactly once with the expected URL
            mock_get_json.assert_called_once_with(url)

            # Both accesses should return the expected payload
            self.assertEqual(result1, expected_payload)
            self.assertEqual(result2, expected_payload)


if __name__ == "__main__":
    unittest.main()

