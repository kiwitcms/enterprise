# Copyright (c) 2020-2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=undefined-variable
import os

# enable additional authentication backends
# so we can perform some sanity testing


for backend in (
    "social_core.backends.fedora.FedoraOpenId",
    "social_core.backends.github.GithubAppAuth",
    "social_core.backends.github.GithubOAuth2",
    "social_core.backends.gitlab.GitLabOAuth2",
    "social_core.backends.keycloak.KeycloakOAuth2",
    "social_auth_kerberos.backend.KerberosAuth",
    "django_python3_ldap.auth.LDAPBackend",
):
    if backend not in AUTHENTICATION_BACKENDS:  # noqa: F821
        AUTHENTICATION_BACKENDS.insert(0, backend)  # noqa: F821


if "django_python3_ldap" not in INSTALLED_APPS:  # noqa: F821
    INSTALLED_APPS.append("django_python3_ldap")  # noqa: F821


LDAP_AUTH_URL = "ldap://openldap_server:389"
LDAP_AUTH_USE_TLS = True
LDAP_AUTH_SEARCH_BASE = "ou=People,dc=example,dc=com"


SOCIAL_AUTH_KEYCLOAK_KEY = "kiwitcms-web-app"
SOCIAL_AUTH_KEYCLOAK_SECRET = os.environ["KC_CLIENT_SECRET"]
SOCIAL_AUTH_KEYCLOAK_PUBLIC_KEY = os.environ["KC_PUBLIC_KEY"]
SOCIAL_AUTH_KEYCLOAK_AUTHORIZATION_URL = (
    "http://kc.example.bg:8080/auth/realms/kiwi/protocol/openid-connect/auth"
)
SOCIAL_AUTH_KEYCLOAK_ACCESS_TOKEN_URL = (
    "http://kc.example.bg:8080/auth/realms/kiwi/protocol/openid-connect/token"
)


ANONYMOUS_ANALYTICS = False
