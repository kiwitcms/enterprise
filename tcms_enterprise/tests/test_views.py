# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json
from http import HTTPStatus
from urllib.parse import parse_qs, urlsplit

from django.urls import reverse

from parameterized import parameterized

from tcms_tenants.tests import LoggedInTestCase

from tcms_enterprise.mcp_scopes import SCOPES


class TestOAuthProtectedResource(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    @parameterized.expand(
        [
            reverse("mcp-oauth-protected-resource"),
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-protected-resource/mcp/",
        ]
    )
    def test_describes_the_mcp_endpoint(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        payload = response.json()
        endpoint = reverse("mcp-endpoint")
        self.assertTrue(payload["resource"].endswith(endpoint))
        self.assertEqual(
            payload["authorization_servers"], [payload["resource"][: -len(endpoint)]]
        )
        self.assertEqual(payload["scopes_supported"], list(SCOPES.values()))


class TestOAuthServerMetadata(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_describes_the_authorization_server(self):
        response = self.client.get(reverse("oauth-server-metadata"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        payload = response.json()
        self.assertTrue(payload["issuer"].startswith("http://"))
        self.assertTrue(payload["authorization_endpoint"].endswith("/o/authorize/"))
        self.assertTrue(payload["token_endpoint"].endswith("/o/token/"))
        self.assertTrue(payload["registration_endpoint"].endswith("/o/register/"))
        self.assertEqual(payload["scopes_supported"], sorted(SCOPES.values()))


class TestDynamicClientRegistration(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_anonymous_registration(self):
        response = self.client.post(
            "/o/register/",
            data=json.dumps(
                {
                    "client_name": "MCP e2e",
                    "redirect_uris": ["http://127.0.0.1:8765/callback"],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "none",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertIn("client_id", response.json())


class TestLoginView(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_private_tenant_login_preserves_next_path_and_query(self):
        next_url = "/o/authorize/?response_type=code&client_id=abc&scope=kiwitcms:view"
        response = self.client.get(reverse("tcms-login"), {"next": next_url})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        location = urlsplit(response["Location"])
        self.assertEqual(location.path, "/accounts/login/")
        self.assertEqual(
            parse_qs(location.query)["next"][0],
            f"/kiwitcms_tenants/go/to/{self.tenant.schema_name}/o/authorize/"
            "?response_type=code&client_id=abc&scope=kiwitcms:view",
        )

    def test_private_tenant_login_ignores_absolute_next(self):
        response = self.client.get(
            reverse("tcms-login"), {"next": "https://evil.example/o/authorize/"}
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        location = urlsplit(response["Location"])
        self.assertEqual(
            parse_qs(location.query)["next"][0],
            f"/kiwitcms_tenants/go/to/{self.tenant.schema_name}/",
        )
