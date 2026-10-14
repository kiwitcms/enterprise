# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json

from django.test import RequestFactory, SimpleTestCase

from modernrpc.views import handle_rpc_request

from tcms.rpc.registry import REGISTRY

from tcms_enterprise.mcp_server import MCPHandler, MCPServer


class TestMCPProtocol(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mcp_server = MCPServer(REGISTRY)

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
        request = self.factory.post(
            "/mcp/", data=json.dumps(payload), content_type="application/json"
        )
        return json.loads(handle_rpc_request(request, self.mcp_server).content)

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

    def test_tools_call_reports_authentication_error(self):
        response = self.call("tools/call", {"name": "Product.filter", "arguments": {}})
        self.assertTrue(response["result"]["isError"])

    def test_unknown_method_should_error(self):
        response = self.call("nope")
        self.assertIn("error", response)
