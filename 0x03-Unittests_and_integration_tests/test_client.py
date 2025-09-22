#!/usr/bin/env python3
"""
Unit and integration tests for client.GithubOrgClient.

Unit tests cover:
- org property behavior (memoized)
- _public_repos_url property (mocked org)
- public_repos (unit test using mocked get_json and _public_repos_url)
- has_license static method

Integration tests use fixtures and mock only requests.get to return fixture
payloads for org and repos endpoints.
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
        """Test that GithubOrgClient.org returns expected payload and that
        get_json is called once.
        """
        expected_payload: Any = {"org": org_name}
        url = client.GithubOrgClient.ORG_URL.format(org=org_name)

        with patch("client.get_json") as mock_get_json:
            mock_get_json.return_value = expected_payload

            github_client = client.GithubOrgClient(org_name)
            # Access the memoized property twice to ensure caching does not
            # cause extra calls.
            result1 = github_client.org
            result2 = github_client.org

            mock_get_json.assert_called_once_with(url)
            self.assertEqual(result1, expected_payload)
            self.assertEqual(result2, expected_payload)

    def test_public_repos_url(self) -> None:
        """Test GithubOrgClient._public_repos_url by mocking the org property."""
        payload = {"repos_url": "https://api.github.com/orgs/google/repos"}

        with patch.object(client.GithubOrgClient,
                          "org",
                          new_callable=PropertyMock) as mock_org:
            mock_org.return_value = payload

            github_client = client.GithubOrgClient("google")
            result = github_client._public_repos_url

            self.assertEqual(result, payload["repos_url"])
            mock_org.assert_called_once()

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """Unit test for public_repos using mocked get_json and _public_repos_url."""
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
        """Test GithubOrgClient.has_license with different repos and keys."""
        result = client.GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


# Integration test: mocks only external HTTP calls (requests.get)
@parameterized_class(("org_payload", "repos_payload", "expected_repos",
                      "apache2_repos"),
                     [(fixtures.org_payload, fixtures.repos_payload,
                       fixtures.expected_repos, fixtures.apache2_repos)])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """
    Integration tests for GithubOrgClient.public_repos using fixture payloads.

    setUpClass starts a patcher for requests.get and configures side_effect
    so requests.get(url).json() returns the right fixture based on url.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Start patcher for requests.get and set side_effect to return fixtures."""
        cls.get_patcher = patch("requests.get")
        cls.mock_get = cls.get_patcher.start()

        org_url = client.GithubOrgClient.ORG_URL.format(org="google")
        repos_url = cls.org_payload.get("repos_url")

        def _get_side_effect(url: str, *args, **kwargs):
            mock_resp = Mock()
            if url == org_url:
                mock_resp.json.return_value = cls.org_payload
            elif url == repos_url:
                mock_resp.json.return_value = cls.repos_payload
            else:
                mock_resp.json.return_value = {}
            return mock_resp

        cls.mock_get.side_effect = _get_side_effect

    @classmethod
    def tearDownClass(cls) -> None:
        """Stop the requests.get patcher."""
        cls.get_patcher.stop()

    def test_public_repos(self) -> None:
        """Integration test: public_repos returns expected repo names from fixtures."""
        github_client = client.GithubOrgClient("google")
        result = github_client.public_repos()
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self) -> None:
        """Integration test: public_repos filtered by apache-2.0 returns expected."""
        github_client = client.GithubOrgClient("google")
        result_apache = github_client.public_repos(license="apache-2.0")
        self.assertEqual(result_apache, self.apache2_repos)


if __name__ == "__main__":
    unittest.main()
