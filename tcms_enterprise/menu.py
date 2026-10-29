# Copyright (c) 2020-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Follows the format of ``tcms.settings.common.MENU_ITEMS``
MENU_ITEMS = [
    (
        _("API Help"),
        [
            (
                _("Documentation"),
                "https://kiwitcms.readthedocs.io/en/latest/api/index.html",
            ),
            (_("Context for LLMs"), "/static/api/llms.txt"),
            (_("OpenAPI schema"), "/static/api/openapi.json"),
        ],
    ),
    (
        _("Model Context Protocol"),
        [
            (
                _("Authorized Tokens"),
                reverse_lazy("oauth2_provider:authorized-token-list"),
            ),
        ],
    ),
]
