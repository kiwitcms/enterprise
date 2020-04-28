"""
    Should be called after superuser has been created *AND*
    after inactive accounts have been deleted! Verifies that
    `delete_inactive_accounts.py` does its job.
"""
from django.contrib.auth import get_user_model


USER = get_user_model()


assert USER.objects.filter(username__startswith='ldap_').count() == 3

for user in USER.objects.filter(username__startswith='ldap_'):
    assert user.is_staff == True
    assert user.groups.filter(name='Tester').count() == 1
