import os
import raven

from django.conf import settings


# indicate that this is the Enterprise Edition
KIWI_VERSION = "%s-ee-807" % settings.KIWI_VERSION


# provides filename versioning
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


ROOT_URLCONF = 'tcms.ee_urls'


# enable reporting errors to Setry for easier debugging
settings.INSTALLED_APPS += [
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

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'tcms.pipeline.initiate_defaults',
)


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
