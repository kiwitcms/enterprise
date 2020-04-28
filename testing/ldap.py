"""
    Should be called after superuser has been created *AND*
    after inactive accounts have been deleted! Verifies that
    `delete_inactive_accounts.py` does its job.
"""
from django.contrib.auth import get_user_model


USER = get_user_model()


assert USER.objects.filter(username__startswith='ldap_').count() == 3
