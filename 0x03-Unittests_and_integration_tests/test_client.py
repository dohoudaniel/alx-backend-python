#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient methods using parameterized inputs,
patching and property mocking.

This test module covers:
- Test that GithubOrgClient.org returns the expected payload (mocked)
- Test that GithubOrgClient._public_repos_url returns the expected repos_url
  by mocking the `org` property using PropertyMock

No external HTTP calls are made because get_json / org are patched.
"""

from typing import Any
import unittest
from unittest.mock import patch, Mock, PropertyMock
from parameterized import parameterized

import client


class TestGithubOrgClient(unittest.TestCase):
    """Tests for GithubOrgClient."""

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

    def test_public_repos_url(self) -> None:
        """
        Test GithubOrgClient._public_repos_url by mocking the `org` property.
        Use PropertyMock to mock the property-style behavior.
        """
        payload = {"repos_url": "https://api.github.com/orgs/google/repos"}

        # Patch the `org` property on GithubOrgClient to return our payload
        with patch.object(client.GithubOrgClient, "org", new_callable=PropertyMock) as mock_org:
            mock_org.return_value = payload

            github_client = client.GithubOrgClient("google")
            # Access the protected property that depends on org property
            result = github_client._public_repos_url

            # Verify the returned URL matches the mocked payload
            self.assertEqual(result, payload["repos_url"])

            # Ensure the property was accessed exactly once
            mock_org.assert_called_once()


if __name__ == "__main__":
    unittest.main()

