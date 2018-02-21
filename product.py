import os
import raven
from .common import *

# Debug settings
DEBUG = False

### Add any site-specific Kiwi settings below this line
# for more information about available settings see
# http://kiwitcms.readthedocs.io/en/latest/configuration.html

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'change-me'


# Administrators error report email settings
ADMINS = [
    # ('Your Name', 'your_email@example.com'),
]


### DO NOT CHANGE THE SETTINGS BELOW

# provides filename versioning
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# indicate that this is the Enterprise Edition version
KIWI_VERSION = "%s-ee" % KIWI_VERSION

# enable reporting errors to Setry for easier debugging
INSTALLED_APPS += ['raven.contrib.django.raven_compat']  # noqa: F405

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
