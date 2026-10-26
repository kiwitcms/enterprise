# Copyright (c) 2020-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import re
from urllib.parse import urlsplit

from django.urls import re_path
from django.conf import settings
from django.conf.urls import include
from django.views.generic import RedirectView

from oauth2_provider import urls as oauth2_urls
from oauth2_provider import views as oauth2_views

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
if not settings.PASSWORD_RESET_ENABLED:
    url_overrides.append(
        re_path(r"^accounts/passwordreset/", views.PasswordResetDisabled.as_view())
    )


if not urlsplit(settings.MEDIA_URL).netloc:
    # route requests to /uploads/ internally and then back to Nginx
    prefix = re.escape(settings.MEDIA_URL.lstrip("/"))
    url_overrides.append(
        re_path(
            f"^{prefix}(?P<path>.*)$",
            views.ViewAttachment.as_view(),
        )
    )


urlpatterns = (
    url_overrides
    + urlpatterns
    + [
        re_path(
            r"^\.well-known/oauth-authorization-server$",
            oauth2_views.OAuthServerMetadataView.as_view(),
            name="oauth-server-metadata",
        ),
        re_path(
            r"^\.well-known/oauth-protected-resource(?:/.*)?$",
            views.OAuthProtectedResource.as_view(),
        ),
        re_path(
            r"^mcp/oauth-protected-resource/$",
            views.OAuthProtectedResource.as_view(),
            name="mcp-oauth-protected-resource",
        ),
        re_path(r"^mcp/", views.mcp_server.view, name="mcp-endpoint"),
        re_path(r"^o/", include(oauth2_urls)),
        re_path(r"", include("social_django.urls", namespace="social")),
    ]
)
