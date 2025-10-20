# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.http import HttpResponseForbidden

from tcms.kiwi_auth import views


class LoginView(
    views.LoginViewWithCustomTemplate
):  # pylint: disable=missing-permission-required
    def post(self, request, *args, **kwargs):
        if settings.PASSWORD_LOGIN_ENABLED:
            return super().post(request)

        return HttpResponseForbidden()


class PasswordResetView(
    views.PasswordResetView
):  # pylint: disable=missing-permission-required
    def get(self, request, *args, **kwargs):
        if settings.PASSWORD_LOGIN_ENABLED:
            return super().get(request)

        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        if settings.PASSWORD_LOGIN_ENABLED:
            return super().post(request)

        return HttpResponseForbidden()
