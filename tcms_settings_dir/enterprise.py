# Copyright (c) 2020-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=undefined-variable

import sentry_sdk
import dj_database_url

from django.utils.translation import gettext_lazy as _

from tcms import __version__

# update DB connection string from the DATABASE_URL environment variable
DATABASES["default"].update(  # noqa: F821, pylint: disable=objects-update-used
    dj_database_url.config()
)
if DATABASES["default"]["ENGINE"].find("mysql") == -1:  # noqa: F821
    del DATABASES["default"]["OPTIONS"]  # noqa: F821

# link to legal information, see https://github.com/kiwitcms/Kiwi/issues/249
LEGAL_MENU_ITEM = ("http://kiwitcms.org/legal/", _("Legal information"))
if LEGAL_MENU_ITEM not in HELP_MENU_ITEMS:  # noqa: F821
    HELP_MENU_ITEMS.append(LEGAL_MENU_ITEM)  # noqa: F821

# indicate that this is the Enterprise Edition
KIWI_VERSION = f"{__version__}-Enterprise"

# the service which renders Mermaid.js diagrams as PNG
MERMAID_RENDERER_URL = "https://mermaid.ink/img"

# provides filename versioning
STORAGES["staticfiles"][  # noqa: F821
    "BACKEND"
] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

ROOT_URLCONF = "tcms_enterprise.root_urls"

if "social_django" not in INSTALLED_APPS:  # noqa: F821
    INSTALLED_APPS.append("social_django")  # noqa: F821

SOCIAL_AUTH_URL_NAMESPACE = "social"

if (
    "social_django.context_processors.backends"
    not in TEMPLATES[0]["OPTIONS"]["context_processors"]  # noqa: F821
):
    TEMPLATES[0]["OPTIONS"]["context_processors"].append(  # noqa: F821
        "social_django.context_processors.backends"
    )

if (
    "social_django.context_processors.login_redirect"
    not in TEMPLATES[0]["OPTIONS"]["context_processors"]  # noqa: F821
):
    TEMPLATES[0]["OPTIONS"]["context_processors"].append(  # noqa: F821
        "social_django.context_processors.login_redirect"
    )

SOCIAL_AUTH_PIPELINE = [
    "social_core.pipeline.social_auth.social_details",
    "tcms_enterprise.pipeline.email_is_required",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "tcms_enterprise.pipeline.random_password",
    "tcms_enterprise.pipeline.initiate_defaults",
]
SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]

# https://plausible.io/kiwitcms-enterprise
PLAUSIBLE_DOMAIN = "kiwitcms-enterprise"

# https://app.scarf.sh/analytics/kiwitcms?pixelId=e9299ee8-1145-4c49-94fc-689f629f0de2
SCARF_PIXEL_ID = "e9299ee8-1145-4c49-94fc-689f629f0de2"

# configuration for Sentry. By default all reports go to Kiwi TCMS
sentry_sdk.init(
    dsn="https://e9a370eba7bd41fe8faead29552f12d7@o126041.ingest.sentry.io/277775",  # noqa: E501, pylint: disable=line-too-long
    # no performace monitoring b/c we hit quota limits
    enable_tracing=False,
    release=KIWI_VERSION,
)


# make sure users from LDAP are assigned default settings
LDAP_AUTH_SYNC_USER_RELATIONS = "tcms_enterprise.ldap.sync_user_relations"

# set to False to disable password login functionality
PASSWORD_LOGIN_ENABLED = True
