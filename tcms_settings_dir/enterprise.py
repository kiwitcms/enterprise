# pylint: disable=undefined-variable

import os
import raven
import dj_database_url

from django.utils.translation import gettext_lazy as _

from tcms import __version__

# update DB connection string from the DATABASE_URL environment variable
DATABASES['default'].update(  # noqa: F821, pylint: disable=objects-update-used
    dj_database_url.config()
)
if DATABASES['default']['ENGINE'].find('mysql') == -1:  # noqa: F821
    del DATABASES['default']['OPTIONS']                 # noqa: F821

# link to legal information, see https://github.com/kiwitcms/Kiwi/issues/249
LEGAL_MENU_ITEM = ('http://kiwitcms.org/legal/', _('Legal information'))
if LEGAL_MENU_ITEM not in HELP_MENU_ITEMS:   # noqa: F821
    HELP_MENU_ITEMS.append(LEGAL_MENU_ITEM)  # noqa: F821

# indicate that this is the Enterprise Edition
KIWI_VERSION = "%s-Enterprise" % __version__

# provides filename versioning
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

ROOT_URLCONF = 'tcms_enterprise.root_urls'

if 'raven.contrib.django.raven_compat' not in INSTALLED_APPS:   # noqa: F821
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')  # noqa: F821

if 'social_django' not in INSTALLED_APPS:   # noqa: F821
    INSTALLED_APPS.append('social_django')  # noqa: F821

SOCIAL_AUTH_URL_NAMESPACE = 'social'

if 'social_django.context_processors.backends' not in \
        TEMPLATES[0]['OPTIONS']['context_processors']:     # noqa: F821
    TEMPLATES[0]['OPTIONS']['context_processors'].append(  # noqa: F821
        'social_django.context_processors.backends')

if 'social_django.context_processors.login_redirect' not in \
        TEMPLATES[0]['OPTIONS']['context_processors']:     # noqa: F821
    TEMPLATES[0]['OPTIONS']['context_processors'].append(  # noqa: F821
        'social_django.context_processors.login_redirect')

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
    'tcms_enterprise.pipeline.random_password',
    'tcms_enterprise.pipeline.initiate_defaults',
]
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

try:
    RAVEN_VERSION = "%s-%s" % (KIWI_VERSION,
                               raven.fetch_git_sha(os.path.abspath(os.pardir)))
except raven.exceptions.InvalidGitRepository:
    RAVEN_VERSION = KIWI_VERSION

# configuration for Sentry. For now only backend errors are sent to Sentry
# by default all reports go to Mr. Senko
RAVEN_CONFIG = {
    'dsn': 'https://e9a370eba7bd41fe8faead29552f12d7:1417b740821a45ef8fe3ae68ea9bfc8b@sentry.io/277775',  # noqa: E501, pylint: disable=line-too-long
    'release': RAVEN_VERSION,
}


# make sure users from LDAP are assigned default settings
LDAP_AUTH_SYNC_USER_RELATIONS = 'tcms_enterprise.ldap.sync_user_relations'
