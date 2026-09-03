# -*- coding: utf-8 -*-
#
# Copyright (c) 2025-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.views.generic.base import View

from tcms.kiwi_auth import views


class LoginView(
    views.LoginViewWithCustomTemplate
):  # pylint: disable=missing-permission-required
    def post(self, request, *args, **kwargs):
        if settings.PASSWORD_LOGIN_ENABLED:
            return super().post(request)

        return HttpResponseForbidden()


class PasswordResetDisabled(View):  # pylint: disable=missing-permission-required
    http_method_names = ["get", "post", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        raise PermissionDenied("Permission denied")
