# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json
from datetime import timedelta
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from django_tenants.utils import schema_context, tenant_context

from oauth2_provider.models import get_access_token_model, get_application_model

from tcms.tests import user_should_have_perm
from tcms.tests.factories import ProductFactory
from tcms_tenants.tests import LoggedInTestCase, UserFactory

from tcms_enterprise.mcp_server import MCPHandler, UNTRUSTED_DATA_NOTICE

AccessToken = get_access_token_model()
Application = get_application_model()


class TestMCPServer(LoggedInTestCase):  # pylint: disable=too-many-public-methods
    bearer_token = "mcp-test-bearer-0001"
    unauthorized_bearer_token = "mcp-test-bearer-unauthorized-0001"
    stale_bearer_token = "mcp-test-bearer-stale-0001"
    expired_bearer_token = "mcp-test-bearer-expired-0001"
    cross_tenant_bearer_token = "mcp-test-bearer-cross-tenant-0001"

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
        if params is None:
            params = {}

        meta = {}
        if version is not None:
            meta["io.modelcontextprotocol/protocolVersion"] = version

        if meta:
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
        response = self.call("tools/list", version="1999-01-01")
        error = response["error"]
        self.assertEqual(error["code"], -32022)
        self.assertEqual(
            error["data"]["supported"], list(MCPHandler.SUPPORTED_VERSIONS)
        )
        self.assertEqual(error["data"]["requested"], "1999-01-01")

    def test_tools_list_should_return_a_list(self):
        response = self.call("tools/list")
        result = response["result"]
        self.assertEqual(result["resultType"], "complete")
        names = []
        for tool in result["tools"]:
            names.append(tool["name"])
        self.assertIn("Product.filter", names)

    def test_tools_call_should_reject_restricted_lookup_path(self):
        user_should_have_perm(self.tester, "testcases.view_testcase")
        response = self.call(
            "tools/call",
            {
                "name": "TestCase.filter",
                "arguments": {
                    "query": {"author__password__startswith": "pbkdf2_sha256$"}
                },
            },
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertTrue(result["isError"])
        self.assertIn("Unsupported field", result["content"][0]["text"])

    def test_tools_call_should_reject_restricted_email_lookup_path(self):
        user_should_have_perm(self.tester, "testcases.view_testcase")
        response = self.call(
            "tools/call",
            {
                "name": "TestCase.filter",
                "arguments": {"query": {"author__email__icontains": "x"}},
            },
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertTrue(result["isError"])
        self.assertIn("Unsupported field", result["content"][0]["text"])

    def test_tools_call_should_allow_safe_lookup_path(self):
        user_should_have_perm(self.tester, "management.view_product")
        response = self.call(
            "tools/call",
            {
                "name": "Product.filter",
                "arguments": {"query": {"name__icontains": "MCP"}},
            },
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertFalse(result["isError"])

        products = json.loads(result["content"][0]["text"])
        names = []
        for product in products:
            names.append(product["name"])
        self.assertIn(self.product.name, names)

    def test_tools_call_should_normalize_and_escape_output(self):
        with tenant_context(self.tenant):
            self.product.name = "<script>alert(1)</script> ＜b＞\u200bﬁ"
            self.product.save()

        user_should_have_perm(self.tester, "management.view_product")
        response = self.call(
            "tools/call",
            {
                "name": "Product.filter",
                "arguments": {"query": {"pk": self.product.pk}},
            },
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertFalse(result["isError"])

        text = result["content"][0]["text"]
        self.assertNotIn("<script>", text)
        self.assertNotIn("\u200b", text)
        self.assertIn("&lt;script&gt;", text)

        products = json.loads(text)
        self.assertEqual(
            products[0]["name"],
            "&lt;script&gt;alert(1)&lt;/script&gt; &lt;b&gt;fi",
        )

    def test_error_result_should_normalize_and_escape(self):
        response = self.call(
            "tools/call",
            {"name": "<script>\u200b", "arguments": {}},
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertTrue(result["isError"])

        text = result["content"][0]["text"]
        self.assertNotIn("<script>", text)
        self.assertNotIn("\u200b", text)
        self.assertIn("&lt;script&gt;", text)

    def test_tools_list_should_suffix_descriptions_with_untrusted_notice(self):
        response = self.call("tools/list")
        tools = response["result"]["tools"]
        for tool in tools:
            self.assertTrue(tool["description"].endswith(UNTRUSTED_DATA_NOTICE))
            if tool["name"] == "Product.filter":
                self.assertIn("Perform a search", tool["description"])

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
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
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
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
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
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

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

    def test_tools_call_should_403_when_token_user_not_authorized_for_tenant(
        self,
    ):
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.unauthorized_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_tools_call_should_403_when_stale_token_exists_but_user_not_authorized_for_tenant(
        self,
    ):
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.stale_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_tools_call_should_403_when_token_belongs_to_another_tenant(self):
        # the user is authorized here but the token was issued on the public
        # schema, i.e. it doesn't exist in this tenant's schema
        with schema_context("public"):
            application = Application.objects.create(
                name=f"MCP cross tenant {timezone.now().timestamp()}",
                user=self.tester,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            AccessToken.objects.create(
                user=self.tester,
                application=application,
                token=self.cross_tenant_bearer_token,
                expires=timezone.now() + timedelta(hours=1),
                scope="kiwitcms:view",
            )

        self.assertTrue(self.tenant.authorized_users.filter(pk=self.tester.pk).exists())
        response = self.call(
            "tools/call",
            {"name": "Product.filter", "arguments": {}},
            bearer_token=self.cross_tenant_bearer_token,
            raw=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_initialize_should_succeed(self):
        response = self.call(
            "initialize",
            {
                "protocolVersion": "DRAFT-2026-v1",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertEqual(result["protocolVersion"], "DRAFT-2026-v1")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["instructions"], UNTRUSTED_DATA_NOTICE)
        self.assertEqual(result["serverInfo"]["name"], "kiwitcms")

    def test_initialize_should_fall_back_to_native_version(self):
        response = self.call(
            "initialize",
            {"protocolVersion": "1999-01-01"},
            bearer_token=self.bearer_token,
        )
        self.assertEqual(
            response["result"]["protocolVersion"], MCPHandler.PROTOCOL_VERSION
        )

    def test_notifications_initialized_is_accepted(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        response = self.client.post(
            "/mcp/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.bearer_token}",
        )
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)

    def test_tools_call_without_meta_should_succeed(self):
        user_should_have_perm(self.tester, "management.view_product")
        response = self.call(
            "tools/call",
            params={"name": "Product.filter", "arguments": {}},
            version=None,
            bearer_token=self.bearer_token,
        )
        result = response["result"]
        self.assertFalse(result["isError"])

    def test_unknown_method_should_error(self):
        response = self.call("nope", bearer_token=self.bearer_token)
        self.assertEqual(response["error"]["message"], 'Method not found: "nope"')
