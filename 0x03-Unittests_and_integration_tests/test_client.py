#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient methods using parameterized inputs,
patching and property mocking.

Includes:
- unit tests for org, _public_repos_url, public_repos and has_license
- an integration test that mocks only external requests via utils.requests.get
  using parameterized_class and fixtures from fixtures.py
"""

from typing import Any, Dict, List
import unittest
from unittest.mock import PropertyMock, Mock, patch
from parameterized import parameterized, parameterized_class

import client
import fixtures


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for GithubOrgClient."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    def test_org(self, org_name: str) -> None:
        """
        Test that GithubOrgClient.org returns expected payload and that
        get_json is called once.
        """
        expected_payload: Any = {"org": org_name}
        url = client.GithubOrgClient.ORG_URL.format(org=org_name)

        # Patch get_json as a context manager to avoid decorator-order issues
        with patch("client.get_json") as mock_get_json:
            mock_get_json.return_value = expected_payload

            github_client = client.GithubOrgClient(org_name)

            # Access the memoized property twice to ensure caching does not
            # cause extra calls.
            result1 = github_client.org
            result2 = github_client.org

            # Ensure get_json was called exactly once with the expected URL.
            mock_get_json.assert_called_once_with(url)

            # Both accesses should return the expected payload.
            self.assertEqual(result1, expected_payload)
            self.assertEqual(result2, expected_payload)

    def test_public_repos_url(self) -> None:
        """
        Test GithubOrgClient._public_repos_url by mocking the `org` property.
        Use PropertyMock to mock the property-style behavior.
        """
        payload = {"repos_url": "https://api.github.com/orgs/google/repos"}

        # Patch the `org` property on GithubOrgClient to return our payload.
        with patch.object(client.GithubOrgClient,
                          "org",
                          new_callable=PropertyMock) as mock_org:
            mock_org.return_value = payload

            github_client = client.GithubOrgClient("google")
            # Access the protected property that depends on org property.
            result = github_client._public_repos_url

            # Verify the returned URL matches the mocked payload.
            self.assertEqual(result, payload["repos_url"])

            # Ensure the property was accessed exactly once.
            mock_org.assert_called_once()

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """
        Unit test for public_repos: mock get_json and patch _public_repos_url.

        The test asserts that:
        - public_repos returns the expected names (all repos)
        - filtering by license works
        - the mocked property and get_json are called once
        """
        gh_url = "https://api.github.com/orgs/google/repos"
        repos_payload: List[Dict[str, Any]] = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None},
        ]
        mock_get_json.return_value = repos_payload

        with patch.object(client.GithubOrgClient,
                          "_public_repos_url",
                          new_callable=PropertyMock) as mock_pub_url:
            mock_pub_url.return_value = gh_url

            github_client = client.GithubOrgClient("google")

            result_all = github_client.public_repos()
            expected_all = ["repo1", "repo2", "repo3"]
            self.assertEqual(result_all, expected_all)

            result_mit = github_client.public_repos(license="mit")
            self.assertEqual(result_mit, ["repo1"])

            mock_pub_url.assert_called_once()
            mock_get_json.assert_called_once_with(gh_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self,
                         repo: Dict[str, Any],
                         license_key: str,
                         expected: bool) -> None:
        """
        Test GithubOrgClient.has_license with different repos and keys.
        """
        result = client.GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


# Integration test: mocks only external HTTP calls (requests.get)
@parameterized_class(("org_payload", "repos_payload",
                      "expected_repos", "apache2_repos"), [
    # Pull fixture values from fixtures.py; ensure fixtures exposes these names
    (fixtures.org_payload,
     fixtures.repos_payload,
     fixtures.expected_repos,
     fixtures.apache2_repos),
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """
    Integration tests for GithubOrgClient.public_repos using real method flows
    but with network requests mocked to return fixture payloads.

    setUpClass starts a patcher for utils.requests.get and configures
    side_effect so that requests.get(url).json() returns the right fixture
    depending on the URL requested.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Start patcher for requests.get and
        set side_effect to return fixtures.
        """
        # Start patcher on utils.requests.get (get_json uses that)
        cls.get_patcher = patch("utils.requests.get")
        cls.mock_get = cls.get_patcher.start()

        # Build a mapping from expected urls to fixture payloads.
        # The org URL is the one used by
        # GithubOrgClient.ORG_URL.format(org=...)
        # The repos URL should be taken from the org_payload['repos_url']
        # value.
        org_url = client.GithubOrgClient.ORG_URL.format(org="google")
        repos_url = cls.org_payload.get("repos_url")

        def _get_side_effect(url: str, *args, **kwargs):
            """
            Side effect for requests.get: return a Mock whose json() returns
            the appropriate fixture based on the URL requested.
            """
            mock_resp = Mock()
            if url == org_url:
                mock_resp.json.return_value = cls.org_payload
            elif url == repos_url:
                mock_resp.json.return_value = cls.repos_payload
            else:
                # default: return an empty mapping
                mock_resp.json.return_value = {}
            return mock_resp

        # Attach the side effect to the started mock
        cls.mock_get.side_effect = _get_side_effect

    @classmethod
    def tearDownClass(cls) -> None:
        """Stop the requests.get patcher."""
        cls.get_patcher.stop()

    def test_public_repos_integration(self) -> None:
        """
        Integration test for public_repos using fixtures.

        Asserts:
        - public_repos returns expected repo names (from expected_repos)
        - public_repos(license='apache-2.0') returns apache2_repos
        """
        github_client = client.GithubOrgClient("google")

        # assert all repos match expected
        result = github_client.public_repos()
        self.assertEqual(result, self.expected_repos)

        # assert license filtering works
        result_apache = github_client.public_repos(license="apache-2.0")
        self.assertEqual(result_apache, self.apache2_repos)


if __name__ == "__main__":
    unittest.main()
