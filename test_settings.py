# pylint: disable=undefined-variable

# enable additional authentication backends
# so we can perform some sanity testing

AUTHENTICATION_BACKENDS = [
    'social_core.backends.fedora.FedoraOpenId',
    'social_core.backends.github.GithubAppAuth',
    'social_core.backends.github.GithubOAuth2',

    'social_auth_kerberos.backend.KerberosAuth',

    'django_python3_ldap.auth.LDAPBackend',

    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]


if 'django_python3_ldap' not in INSTALLED_APPS:   # noqa: F821
    INSTALLED_APPS.append('django_python3_ldap')  # noqa: F821


LDAP_AUTH_URL = "ldap://openldap_server:389"
LDAP_AUTH_USE_TLS = True
LDAP_AUTH_SEARCH_BASE = "ou=People,dc=example,dc=com"
