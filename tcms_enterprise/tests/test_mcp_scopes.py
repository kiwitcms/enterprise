# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.test import SimpleTestCase

from tcms.rpc.views import json_rpc_server

from tcms_enterprise.mcp_scopes import (
    SCOPES,
    declared_permissions,
    has_required_scopes,
    required_scopes,
    scope_for_permission,
)


class TestScopeForPermission(SimpleTestCase):
    def test_valid_permission_codename_returns_scope(self):
        self.assertEqual(
            scope_for_permission("management.view_product"), "kiwitcms:view"
        )
        self.assertEqual(scope_for_permission("management.add_product"), "kiwitcms:add")
        self.assertEqual(
            scope_for_permission("testcases.change_testcase"), "kiwitcms:change"
        )
        self.assertEqual(
            scope_for_permission("testcases.delete_testcase"), "kiwitcms:delete"
        )

    def test_invalid_permission_codename_returns_none(self):
        self.assertIsNone(scope_for_permission("something.custom_thing"))
        self.assertIsNone(scope_for_permission("novb_whatever"))


class TestDeclaredPermissions(SimpleTestCase):
    def test_method_with_permissions_required_decorator(self):
        wrapper = json_rpc_server.procedures["Product.filter"]
        self.assertEqual(declared_permissions(wrapper), ["management.view_product"])

    def test_public_method_has_no_permissions(self):
        wrapper = json_rpc_server.procedures["Auth.login"]
        self.assertEqual(declared_permissions(wrapper), [])

    def test_methods_with_implicitly_declared_permissions(self):
        wrapper = json_rpc_server.procedures["User.update"]
        self.assertEqual(declared_permissions(wrapper), ["auth.change_user"])


class TestRequiredScopes(SimpleTestCase):
    def test_for_methods_with_view_add_change_delete_permission(self):
        procedures = json_rpc_server.procedures
        self.assertEqual(
            required_scopes(procedures["Product.filter"]), {"kiwitcms:view"}
        )
        self.assertEqual(
            required_scopes(procedures["Product.create"]), {"kiwitcms:add"}
        )
        self.assertEqual(
            required_scopes(procedures["TestCase.update"]), {"kiwitcms:change"}
        )
        self.assertEqual(
            required_scopes(procedures["TestCase.remove"]), {"kiwitcms:delete"}
        )

    def test_public_method_has_no_scopes(self):
        self.assertEqual(
            required_scopes(json_rpc_server.procedures["Auth.login"]), set()
        )

    def test_login_only_method_requires_view(self):
        self.assertEqual(
            required_scopes(json_rpc_server.procedures["Bug.details"]),
            {"kiwitcms:view"},
        )

    def test_scope_for_methods_with_implicit_permissions(self):
        self.assertEqual(
            required_scopes(json_rpc_server.procedures["User.update"]),
            {"kiwitcms:change"},
        )

    def test_every_exposed_method_maps_to_known_scopes(self):
        for rpc_name, wrapper in json_rpc_server.procedures.items():
            if not wrapper.is_available_in_json_rpc:
                continue
            if rpc_name.startswith("system."):
                continue

            scopes = required_scopes(wrapper)
            for scope in scopes:
                self.assertIn(scope, SCOPES.values())


class TestHasRequiredScopes(SimpleTestCase):
    def test_when_required_is_subset_of_granted_should_pass(self):
        self.assertTrue(
            has_required_scopes({"kiwitcms:view"}, {"kiwitcms:view", "kiwitcms:add"})
        )
        self.assertTrue(has_required_scopes(set(), {"kiwitcms:add"}))
        self.assertTrue(has_required_scopes(set(), set()))

    def test_when_required_is_missing_from_granted_should_fail(self):
        self.assertFalse(has_required_scopes({"kiwitcms:add"}, {"kiwitcms:view"}))
        self.assertFalse(has_required_scopes({"kiwitcms:delete"}, set()))
