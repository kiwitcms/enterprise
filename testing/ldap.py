# Copyright (c) 2020-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

"""
Should be called after superuser has been created!
Verifies that `ldap_sync_users` does its job.
"""
from django.contrib.auth import get_user_model


USER = get_user_model()


assert USER.objects.filter(username__startswith="ldap_").count() == 3

for user in USER.objects.filter(username__startswith="ldap_"):
    assert user.is_active == True
    assert user.is_staff == True
    assert user.groups.filter(name="Tester").count() == 1
