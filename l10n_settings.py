import os

SECRET_KEY = 'generate-locales'


BASE_DIR = os.path.dirname(__file__)
LOCALE_PATHS = [os.path.join(BASE_DIR, 'tcms_enterprise', 'locale')]

# used only for running pylint
ROOT_URLCONF = 'tcms_enterprise.urls'
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "attachments",
]
