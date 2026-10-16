# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta

from django.utils import timezone
from django_tenants.utils import schema_context, tenant_context

from oauth2_provider.models import get_access_token_model, get_application_model

from tcms_tenants.tests import LoggedInTestCase, UserFactory

AccessToken = get_access_token_model()
Application = get_application_model()


class TestAccessTokenIsPerTenant(LoggedInTestCase):
    def test_access_token_is_not_shared_between_schemas(self):
        with tenant_context(self.tenant):
            owner = UserFactory()
            application = Application.objects.create(
                name="MCP",
                user=owner,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            AccessToken.objects.create(
                user=owner,
                application=application,
                token="***",
                expires=timezone.now() + timedelta(hours=1),
                scope="kiwitcms:view",
            )
            self.assertEqual(AccessToken.objects.filter(user=owner).count(), 1)

        # the access token must not leak into the shared (public) schema
        with schema_context("public"):
            self.assertEqual(AccessToken.objects.filter(user=owner).count(), 0)
            self.assertEqual(Application.objects.filter(user=owner).count(), 0)
