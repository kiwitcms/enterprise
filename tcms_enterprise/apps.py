# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    name = "tcms_enterprise"

    def ready(self):
        from oauth2_provider.signals import app_authorized

        from tcms_enterprise import signals

        app_authorized.connect(signals.bind_application_to_user)
