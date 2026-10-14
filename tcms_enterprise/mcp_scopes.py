# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

SCOPES = {
    "view": "kiwitcms:view",
    "add": "kiwitcms:add",
    "change": "kiwitcms:change",
    "delete": "kiwitcms:delete",
}


def scope_for_permission(codename):
    name = codename.split(".")[-1]
    verb = name.split("_", 1)[0]
    return SCOPES.get(verb)


def declared_permissions(method):
    implicit_permissions = {
        "User.update": ["auth.change_user"],
    }

    # permissions_required() returns a closure over the permission codenames
    auth = getattr(method, "auth", None)
    if auth is not None:
        closure = getattr(auth, "__closure__", None)
        if closure:
            freevars = getattr(getattr(auth, "__code__", None), "co_freevars", ())
            for name, cell in zip(freevars, closure):
                if name == "perms":
                    return list(cell.cell_contents)

    return list(implicit_permissions.get(method.name, []))


def required_scopes(method):
    permissions = declared_permissions(method)
    if not permissions:
        # public method, no permission check
        if getattr(method, "auth", None) is None:
            return set()

        # authenticated but no specific permission, e.g. django_login_required
        return {"kiwitcms:view"}

    scopes = set()
    for codename in permissions:
        scope = scope_for_permission(codename)
        if scope is None:
            raise ValueError(f"Cannot map {codename} to an MCP scope")
        scopes.add(scope)

    return scopes


def has_required_scopes(required, granted):
    return required.issubset(granted)
