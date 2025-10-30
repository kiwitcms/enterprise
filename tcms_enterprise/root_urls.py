# Copyright (c) 2020-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import re_path
from django.conf import settings
from django.conf.urls import include
from django.views.defaults import permission_denied
from django.views.generic import RedirectView

from tcms.urls import urlpatterns
from tcms_enterprise import views


url_overrides = [
    re_path(
        r"^admin/login/",
        RedirectView.as_view(url="/accounts/login/", permanent=True),
    ),
    # override b/c pwd login can be disabled
    re_path(r"^accounts/login/", views.LoginView.as_view()),
]

# WARNING: overrides all password reset pages (form, done, confirm, complete)
# b/c we're matching the beginning of the URL path !
if not settings.PASSWORD_LOGIN_ENABLED:
    url_overrides.append(re_path(r"^accounts/passwordreset/", permission_denied))


urlpatterns = (
    url_overrides
    + urlpatterns
    + [
        re_path(r"", include("social_django.urls", namespace="social")),
    ]
)
