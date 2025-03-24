# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show Kiwi TCMS version"

    def handle(self, *args, **kwargs):
        self.stdout.write(settings.KIWI_VERSION)
