# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.contrib.auth.models import User

# no permissions to view attachments
regular_user, _ = User.objects.get_or_create(
    username="regular",
    is_active=True,
    is_staff=True,
    is_superuser=False,
    email="regular@domain.com",
)
regular_user.set_password("password")
regular_user.save()
