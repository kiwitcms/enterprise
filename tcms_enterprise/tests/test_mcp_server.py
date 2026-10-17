# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from django_tenants.utils import schema_context, tenant_context

from oauth2_provider.models import get_access_token_model, get_application_model

from tcms.tests import user_should_have_perm
from tcms.tests.factories import ProductFactory
from tcms_tenants.tests import LoggedInTestCase, UserFactory

from tcms_enterprise.mcp_server import MCPHandler

AccessToken = get_access_token_model()
Application = get_application_model()


class TestMCPServer(LoggedInTestCase):
    bearer_token = "mcp-test-bearer-0001"
    unauthorized_bearer_token = "mcp-test-bearer-unauthorized-0001"
    stale_bearer_token = "mcp-test-bearer-stale-0001"
    expired_bearer_token = "mcp-test-bearer-expired-0001"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with tenant_context(cls.tenant):
            cls.product = ProductFactory(name="MCP product")

            application = Application.objects.create(
                name=f"MCP {timezone.now().timestamp()}",
                user=cls.tester,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            AccessToken.objects.create(
                user=cls.tester,
                application=application,
                token=cls.bearer_token,
                expires=timezone.now() + timedelta(hours=1),
                scope="kiwitcms:view",
            )

            AccessToken.objects.create(
                user=cls.tester,
                application=application,
                token=cls.expired_bearer_token,
                expires=timezone.now() - timedelta(hours=1),
                scope="kiwitcms:view",
            )

        # the unauthorized user and its tokens live in the public schema,
        # i.e. they are not authorized for this tenant
        with schema_context("public"):
            cls.unauthorized_user = UserFactory()
            user_should_have_perm(cls.unauthorized_user, "management.view_product")
            application = Application.objects.create(
                name=f"MCP unauthorized {timezone.now().timestamp()}",
                user=cls.unauthorized_user,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            AccessToken.objects.create(
                user=cls.unauthorized_user,
                application=application,
                token=cls.unauthorized_bearer_token,
                expires=timezone.now() + timedelta(hours=1),
                scope="kiwitcms:view",
            )

        # an older token left behind on the tenant schema (the user was
        # previously authorized) is still found, but the user no longer is
        with tenant_context(cls.tenant):
            application = Application.objects.create(
                name=f"MCP stale {timezone.now().timestamp()}",
                user=cls.unauthorized_user,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            AccessToken.objects.create(
                user=cls.unauthorized_user,
                application=application,
                token=cls.stale_bearer_token,
                expires=timezone.now() + timedelta(hours=1),
                scope="kiwitcms:view",
            )

    def setUp(self):
        super().setUp()
        # simulate an external MCP client: never send the Django session cookie
        self.client.logout()

    def call(
        self,
        method,
        params=None,
        version=MCPHandler.PROTOCOL_VERSION,
        bearer_token=None,
        raw=False,
    ):
        meta = {}
        if version is not None:
            meta["io.modelcontextprotocol/protocolVersion"] = version

        if params is None:
            params = {}
        params["_meta"] = meta

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        headers = {}
        if bearer_token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {bearer_token}"

        response = self.client.post(
            "/mcp/",
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )
        if raw:
            return response
        return json.loads(response.content)

    def test_server_discover_should_succeed(self):
        response = self.call("server/discover")
        result = response["result"]
        self.assertEqual(result["supportedVersions"], [MCPHandler.PROTOCOL_VERSION])
        self.assertEqual(result["resultType"], "complete")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(
            result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "kiwitcms"
        )

    def test_unsupported_protocol_version_should_error(self):
        response = self.call("tools/list", version="2025-06-18")
        error = response["error"]
        self.assertEqual(error["code"], -32022)
        self.assertEqual(error["data"]["supported"], [MCPHandler.PROTOCOL_VERSION])
        self.assertEqual(error["data"]["requested"], "2025-06-18")

    def test_tools_list_should_return_a_list(self):
        response = self.call("tools/list")
        result = response["result"]
        self.assertEqual(result["resultType"], "complete")
        names = []
        for tool in result["tools"]:
            names.append(tool["name"])
        self.assertIn("Product.filter", names)

    def test_tools_call_with_unknown_tool_should_error(self):
        response = self.call(
            "tools/call",
            {"name": "Nope.nope", "arguments": {}},
            bearer_token=self.bearer_token,
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn(
            "Unknown tool: Nope.nope",
            response["result"]["content"][0]["text"],
        )

    def test_tools_call_should_401_when_token_missing(self):
        response = self.call(
            "tools/call", {"name": "Product.filter", "arguments": {}}, raw=True
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn(
            reverse("mcp-oauth-protected-resource"),
            response["WWW-Authenticate"],
        )
        self.assertIn('scope="kiwitcms:view"', response["WWW-Authenticate"])

    def test_tools_call_should_401_with_the_scope_of_the_requested_tool(self):
        response = self.call(
            "tools/call",
            {"name": "Product.create", "arguments": {"values": {"name": "New"}}},
            raw=True,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('scope="kiwitcms:add"', response["WWW-Authenticate"])

    def test_tools_call_should_error_when_without_permissions(self):
        self.assertFalse(self.tester.has_perm("management.view_product"))
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.bearer_token,
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn(
            "Authentication failed for Product.filter",
            response["result"]["content"][0]["text"],
        )

    def test_tools_call_returns_success_when_with_permissions_and_correct_token_scope(
        self,
    ):
        user_should_have_perm(self.tester, "management.view_product")
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.bearer_token,
        )
        self.assertFalse(response["result"]["isError"])

        products = json.loads(response["result"]["content"][0]["text"])
        names = []
        for product in products:
            names.append(product["name"])
        self.assertIn(self.product.name, names)

    def test_tools_call_should_error_when_user_is_disabled(self):
        user_should_have_perm(self.tester, "management.view_product")
        self.tester.is_active = False
        self.tester.save()
        self.addCleanup(setattr, self.tester, "is_active", True)

        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.bearer_token,
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn(
            "Authentication failed for Product.filter",
            response["result"]["content"][0]["text"],
        )

    def test_tools_call_should_401_when_token_is_expired(self):
        user_should_have_perm(self.tester, "management.view_product")
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.expired_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, 401)

    def test_tools_call_should_error_when_with_permissions_but_token_scope_insufficient(
        self,
    ):
        user_should_have_perm(self.tester, "management.add_product")
        response = self.call(
            "tools/call",
            {"name": "Product.create", "arguments": {"values": {"name": "New"}}},
            bearer_token=self.bearer_token,
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn(
            "Insufficient scope for Product.create",
            response["result"]["content"][0]["text"],
        )

    def test_tools_call_should_401_when_token_user_not_authorized_for_tenant(
        self,
    ):
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.unauthorized_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, 401)

    def test_tools_call_should_403_when_stale_token_exists_but_user_not_authorized_for_tenant(
        self,
    ):
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.stale_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_unknown_method_should_error(self):
        response = self.call("nope", bearer_token=self.bearer_token)
        self.assertEqual(response["error"]["message"], 'Method not found: "nope"')
