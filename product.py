import os
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
