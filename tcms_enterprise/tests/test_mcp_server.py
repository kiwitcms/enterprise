# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json

from django_tenants.utils import tenant_context

from tcms.tests import user_should_have_perm
from tcms.tests.factories import ProductFactory
from tcms_tenants.tests import LoggedInTestCase
from tcms_enterprise.mcp_server import MCPHandler


class TestMCPServer(LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with tenant_context(cls.tenant):
            cls.product = ProductFactory(name="MCP product")

    def call(self, method, params=None, version=MCPHandler.PROTOCOL_VERSION):
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
        response = self.client.post(
            "/mcp/", data=json.dumps(payload), content_type="application/json"
        )
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
        response = self.call("tools/call", {"name": "Nope.nope", "arguments": {}})
        self.assertTrue(response["result"]["isError"])

    def test_tools_call_reports_authentication_error_when_not_logged_in(self):
        self.client.logout()
        response = self.call("tools/call", {"name": "Product.filter", "arguments": {}})
        self.assertTrue(response["result"]["isError"])

    def test_tools_call_reports_authentication_error_when_logged_in_without_permissions(
        self,
    ):
        self.assertFalse(self.tester.has_perm("management.view_product"))
        response = self.call("tools/call", {"name": "Product.filter", "arguments": {}})
        self.assertTrue(response["result"]["isError"])

    def test_tools_call_returns_success_when_logged_in_with_permissions(self):
        user_should_have_perm(self.tester, "management.view_product")
        response = self.call("tools/call", {"name": "Product.filter", "arguments": {}})
        self.assertFalse(response["result"]["isError"])

        products = json.loads(response["result"]["content"][0]["text"])
        names = []
        for product in products:
            names.append(product["name"])
        self.assertIn(self.product.name, names)

    def test_unknown_method_should_error(self):
        response = self.call("nope")
        self.assertIn("error", response)
