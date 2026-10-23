# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.contrib.auth.models import User

from tcms.utils.permissions import initiate_user_with_default_setups

mcp_user, _ = User.objects.get_or_create(
    username="openclaw-dev",
    is_active=True,
    is_staff=True,
    is_superuser=False,
    email="openclaw-dev@domain.com",
)
mcp_user.set_password("password")
mcp_user.save()
initiate_user_with_default_setups(mcp_user)
