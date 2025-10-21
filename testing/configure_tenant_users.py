# Copyright (c) 2021-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

"""
Should be called after `ldap_sync_users`.
"""
from django.contrib.auth import get_user_model

from tcms.management.models import Classification, Product, Version
from tcms.testplans.models import PlanType, TestPlan

from tcms_tenants.models import Tenant

tenant = Tenant.objects.get(schema_name="empty")

domain = tenant.domains.first()
domain.domain = "empty.testing.example.bg"
domain.save()

for user in get_user_model().objects.all():
    tenant.authorized_users.add(user)


# this should be on the main tenant
classification, _ = Classification.objects.get_or_create(name="core products")
product, _ = Product.objects.get_or_create(
    name="Kiwi TCMS", classification=classification
)
version, _ = Version.objects.get_or_create(value="devel", product=product)

TestPlan.objects.create(
    name="Check if uploading files works",
    product=product,
    product_version=version,
    type=PlanType.objects.first(),
    author=get_user_model().objects.last(),
    text="""Kiwi TCMS Enterprise can render Mermaid.js diagrams, see:
```mermaid
flowchart LR
    Start --> Stop
```""",
)
