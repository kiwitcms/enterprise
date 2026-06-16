# Copyright (c) 2020-2021 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import os

SECRET_KEY = "generate-locales"


BASE_DIR = os.path.dirname(__file__)
LOCALE_PATHS = [os.path.join(BASE_DIR, "tcms_enterprise", "locale")]

# used only for running pylint
ROOT_URLCONF = "tcms_enterprise.urls"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "attachments",
]
