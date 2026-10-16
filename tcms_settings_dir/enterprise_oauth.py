# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=undefined-variable

from tcms_enterprise.mcp_scopes import SCOPES

# access tokens are per-tenant, just like tenant_groups
for app_list in (INSTALLED_APPS, TENANT_APPS):  # noqa: F821
    if "oauth2_provider" not in app_list:
        app_list.append("oauth2_provider")

OAUTH2_PROVIDER = {
    "PKCE_REQUIRED": True,
    "SCOPES": {},
}
for scope in SCOPES.values():
    OAUTH2_PROVIDER["SCOPES"][scope] = scope

# authenticate and expose the access token used by the request (bearer tokens)
for middleware in (
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "oauth2_provider.middleware.OAuth2ExtraTokenMiddleware",
):
    if middleware not in MIDDLEWARE:  # noqa: F821
        MIDDLEWARE.append(middleware)  # noqa: F821

backend = "oauth2_provider.backends.OAuth2Backend"  # pylint: disable=invalid-name
if backend not in AUTHENTICATION_BACKENDS:  # noqa: F821
    AUTHENTICATION_BACKENDS.append(backend)  # noqa: F821
