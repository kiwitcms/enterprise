# -*- coding: utf-8 -*-
#
# Copyright (c) 2025-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from django_tenants.utils import get_public_schema_name
from tcms.kiwi_auth import views
from tcms_tenants.utils import can_access, tenant_url


class LoginView(
    views.LoginViewWithCustomTemplate
):  # pylint: disable=missing-permission-required
    def get(self, request, *args, **kwargs):
        # reroute all Private Tenant requests through the Login@public.tenant page
        if request.tenant.schema_name != get_public_schema_name():
            public_tenant_url = tenant_url(request, get_public_schema_name()).rstrip(
                "/"
            )
            accounts_login = reverse("tcms-login").lstrip("/")
            next_page = reverse(
                "tcms_tenants:redirect-to", args=[request.tenant.schema_name, ""]
            )

            return HttpResponseRedirect(
                f"{public_tenant_url}/{accounts_login}?{self.redirect_field_name}={next_page}"
            )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        login_destination = self.request.tenant
        next_page = context.get(self.redirect_field_name, "/")
        if next_page.startswith("/kiwitcms_tenants/go/to/"):
            try:
                next_schema = next_page.rstrip("/").split("/")[-1]
                login_destination = login_destination.__class__.objects.get(
                    schema_name=next_schema
                )
            except ObjectDoesNotExist:
                pass

        context["X_Login_Destination_Name"] = login_destination.name
        context["X_Login_Destination_Url"] = tenant_url(
            self.request, login_destination.schema_name
        )

        return context

    def post(self, request, *args, **kwargs):
        if settings.PASSWORD_LOGIN_ENABLED:
            return super().post(request, *args, **kwargs)

        return HttpResponseForbidden()


class PasswordResetDisabled(View):  # pylint: disable=missing-permission-required
    http_method_names = ["get", "post", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        raise PermissionDenied("Permission denied")


@method_decorator(
    permission_required("attachments.view_attachment", raise_exception=True),
    name="dispatch",
)
class ViewAttachment(views.ViewAttachment):
    def get(self, request, path):
        if not can_access(request.user, request.tenant):
            raise PermissionDenied

        return super().get(request, path)
