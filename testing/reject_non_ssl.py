# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db.utils import OperationalError
from tcms.management.models import Classification

rejected = 0
try:
    classification, _ = Classification.objects.using("plain_text").get_or_create(
        name="core products"
    )
except OperationalError:
    rejected += 1

assert rejected > 0
