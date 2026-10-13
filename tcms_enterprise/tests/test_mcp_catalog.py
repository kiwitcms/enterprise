# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import re

from django.test import SimpleTestCase

from tcms.rpc.views import json_rpc_server

from tcms_enterprise.mcp_catalog import build_catalog

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class TestBuildCatalog(SimpleTestCase):
    def test_catalog_is_not_empty(self):
        self.assertTrue(build_catalog())

    def test_names_are_valid_and_unique(self):
        seen = []
        for tool in build_catalog():
            self.assertRegex(tool["name"], NAME_RE)
            self.assertNotIn(tool["name"], seen)
            seen.append(tool["name"])

    def test_every_tool_has_a_description(self):
        for tool in build_catalog():
            self.assertTrue(tool["description"])

    def test_every_tool_has_an_object_input_schema(self):
        for tool in build_catalog():
            self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_known_tool_and_schema(self):
        product_filter = None
        for tool in build_catalog():
            if tool["name"] == "Product.filter":
                product_filter = tool
                break

        self.assertIsNotNone(product_filter)
        schema = product_filter["inputSchema"]
        self.assertIn("query", schema["properties"])
        self.assertTrue(schema["additionalProperties"])

    def test_all_api_methods_are_exposed(self):
        catalog_names = []
        for tool in build_catalog():
            catalog_names.append(tool["name"])

        json_rpc_methods = 0
        for rpc_name, wrapper in json_rpc_server.procedures.items():
            if not wrapper.is_available_in_json_rpc:
                continue
            if rpc_name.startswith("system."):
                continue

            json_rpc_methods += 1
            self.assertIn(rpc_name, catalog_names)

        self.assertEqual(len(catalog_names), json_rpc_methods)

    def test_system_methods_are_not_exposed(self):
        names = []
        for tool in build_catalog():
            names.append(tool["name"])

        self.assertNotIn("system.listMethods", names)
        self.assertNotIn("system.methodHelp", names)
        self.assertNotIn("system.methodSignature", names)
