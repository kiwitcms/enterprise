# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.contrib.auth.models import Group, User

unauthorized_user, _ = User.objects.get_or_create(
    username="unauthorized",
    is_active=True,
    is_staff=True,
    is_superuser=False,
    email="unauthorized@domain.com",
)
unauthorized_user.set_password("password")
unauthorized_user.save()

unauthorized_user.groups.add(Group.objects.get(name="Tester"))
