"""
    Should be called after `ldap_sync_users`.
"""
from django.contrib.auth import get_user_model
from tcms_tenants.models import Tenant

tenant = Tenant.objects.get(schema_name="empty")

domain = tenant.domains.first()
domain.domain = "empty.testing.example.bg"
domain.save()

for user in get_user_model().objects.all():
    tenant.authorized_users.add(user)
