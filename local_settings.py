import os
import raven
import dj_database_url

from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _


# update DB connection string from the DATABASE_URL environment variable
settings.DATABASES['default'].update(dj_database_url.config())

# link to legal information, see https://github.com/kiwitcms/Kiwi/issues/249
settings.HELP_MENU_ITEMS.append(
    ('http://kiwitcms.org/legal/', 'Legal information')
)

# indicate that this is the Enterprise Edition
KIWI_VERSION = "%s-Enterprise" % settings.KIWI_VERSION


# provides filename versioning
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
settings.STATICFILES_DIRS.insert(0, os.path.join(settings.TCMS_ROOT_PATH, 'ee_static'))

ROOT_URLCONF = 'tcms_enterprise.urls'


# enable reporting errors to Setry for easier debugging
settings.INSTALLED_APPS += [
    'tcms_enterprise',
    'raven.contrib.django.raven_compat',
    'social_django',
]  # noqa: F405

SOCIAL_AUTH_URL_NAMESPACE = 'social'

settings.PUBLIC_VIEWS.extend([
    'social_django.views.auth',
    'social_django.views.complete',
    'social_django.views.disconnect',
])

settings.TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect',
])
settings.TEMPLATES[0]['DIRS'].insert(0, os.path.join(settings.TCMS_ROOT_PATH, 'ee_templates'))

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'tcms_enterprise.pipeline.email_is_required',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'tcms_enterprise.pipeline.initiate_defaults',
]
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

try:
    raven_version = "%s-%s" % (KIWI_VERSION, raven.fetch_git_sha(os.path.abspath(os.pardir)))
except raven.exceptions.InvalidGitRepository:
    raven_version = KIWI_VERSION


# configuration for Sentry. For now only backend errors are sent to Sentry
# by default all reports go to Mr. Senko
RAVEN_CONFIG = {
    'dsn': 'https://e9a370eba7bd41fe8faead29552f12d7:1417b740821a45ef8fe3ae68ea9bfc8b@sentry.io/277775',  # noqa: E501
    'release': raven_version,
}

##### only if outside docker image has defined a PostgreSQL database
if os.environ.get('KIWI_DB_ENGINE', '').find('postgresql') > -1:
    try:
        import tcms_tenants

        # Allows serving non-public tenants on a sub-domain
        # WARNING: doesn't work well when you have a non-standard port-number
        KIWI_TENANTS_DOMAIN = os.environ.get('KIWI_TENANTS_DOMAIN', 'tenant.localdomain')

        # share login session between tenants
        SESSION_COOKIE_DOMAIN = ".%s" % KIWI_TENANTS_DOMAIN

        ##### start multi-tenant settings override
        settings.DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'

        DATABASE_ROUTERS = [
            'django_tenants.routers.TenantSyncRouter',
        ]

        settings.MIDDLEWARE.insert(0, 'django_tenants.middleware.main.TenantMainMiddleware')
        settings.MIDDLEWARE.append('tcms_tenants.middleware.BlockUnauthorizedUserMiddleware')

        TENANT_MODEL = "tcms_tenants.Tenant"
        TENANT_DOMAIN_MODEL = "tcms_tenants.Domain"

        settings.INSTALLED_APPS.insert(0, 'django_tenants')
        settings.INSTALLED_APPS.insert(1, 'tcms_tenants')

        TENANT_APPS = [
            'django.contrib.contenttypes',
            'django.contrib.sites',

            'attachments',
            'django_comments',
            'modernrpc',
            'simple_history',

            'tcms.core.contrib.comments.apps.AppConfig',
            'tcms.core.contrib.linkreference',
            'tcms.management',
            'tcms.testcases.apps.AppConfig',
            'tcms.testplans.apps.AppConfig',
            'tcms.testruns.apps.AppConfig',
        ]

        # everybody can access the main instance
        SHARED_APPS = settings.INSTALLED_APPS

        # main navigation menu
        settings.MENU_ITEMS.append(
            (_('TENANT'), [
                (_('Create'), reverse_lazy('tcms_tenants:create-tenant')),
                ('-', '-'),
                (_('Authorized users'), '/admin/tcms_tenants/tenant_authorized_users/'),
            ]),
        )

        # attachments storage
        DEFAULT_FILE_STORAGE = "tcms_tenants.storage.TenantFileSystemStorage"
        MULTITENANT_RELATIVE_MEDIA_ROOT = "tenant/%s"
    except ImportError:
        pass
