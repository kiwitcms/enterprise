# enable additional authentication backends
# so we can perform some sanity testing

AUTHENTICATION_BACKENDS = [
    'social_core.backends.fedora.FedoraOpenId',
    'social_core.backends.github.GithubAppAuth',
    'social_core.backends.github.GithubOAuth2',

    'social_auth_kerberos.backend.KerberosAuth',

    'django.contrib.auth.backends.ModelBackend',
]
