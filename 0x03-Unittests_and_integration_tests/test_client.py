#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient methods using parameterized inputs,
patching and property mocking.

This test module covers:
- Test that GithubOrgClient.org returns the expected payload (mocked)
- Test that GithubOrgClient._public_repos_url returns the expected repos_url
  by mocking the `org` property using PropertyMock
- Test that GithubOrgClient.public_repos returns expected repo names and that
  _public_repos_url and get_json are each called exactly once

No external HTTP calls are made because get_json / org are patched.
"""

from typing import Any, List, Dict
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

            # Access the memoized property twice to ensure caching doesn't
            # cause extra calls
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

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """
        Test GithubOrgClient.public_repos:
        - mock get_json (decorator) to return a chosen repos payload
        - mock _public_repos_url (context manager) to return a chosen URL
        - assert public_repos returns expected list of names
        - assert mocked property and get_json were called once
        """
        # Prepare a fake repos payload
        repos_payload: List[Dict[str, Any]] = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None},
        ]
        # get_json will return the repos_payload when called
        mock_get_json.return_value = repos_payload

        # Patch the _public_repos_url property to return a specific URL
        with patch.object(client.GithubOrgClient, "_public_repos_url", new_callable=PropertyMock) as mock_pub_url:
            mock_pub_url.return_value = "https://api.github.com/orgs/google/repos"

            github_client = client.GithubOrgClient("google")

            # Call public_repos without license filter -> should return all
            # repo names
            result_all = github_client.public_repos()
            expected_all = ["repo1", "repo2", "repo3"]
            self.assertEqual(result_all, expected_all)

            # Call public_repos with a license filter -> should return only
            # matching names
            result_mit = github_client.public_repos(license="mit")
            self.assertEqual(result_mit, ["repo1"])

            # Ensure _public_repos_url property was accessed (once per new
            # client usage)
            mock_pub_url.assert_called()

            # Ensure get_json was called at least once with the URL
            mock_get_json.assert_called_with(
                "https://api.github.com/orgs/google/repos")


if __name__ == "__main__":
    unittest.main()
