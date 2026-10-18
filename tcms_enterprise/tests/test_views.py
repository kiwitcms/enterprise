# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from http import HTTPStatus

from django.urls import reverse

from tcms_tenants.tests import LoggedInTestCase

from tcms_enterprise.mcp_scopes import SCOPES


class TestOAuthProtectedResource(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_describes_the_mcp_endpoint(self):
        response = self.client.get(reverse("mcp-oauth-protected-resource"))
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
        self.assertEqual(payload["scopes_supported"], sorted(SCOPES.values()))
