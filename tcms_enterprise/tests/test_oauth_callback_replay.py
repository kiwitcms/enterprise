# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from http import HTTPStatus
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.messages import get_messages
from django.test import override_settings
from django.urls import reverse

from django_tenants.test.client import TenantClient

from social_core.backends.gitlab import GitLabOAuth2

from tcms_tenants.tests import LoggedInTestCase

AUTH_BACKENDS = [
    "social_core.backends.gitlab.GitLabOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

GITLAB_USER = {
    "id": 1234567,
    "username": "johannwang",
    "name": "Johann Wang",
    "email": "johann.wang@example.com",
}

SESSION_UNAVAILABLE = "authentication session is unavailable"


def access_token_response():
    return {"access" + "_token": "test-token", "token_type": "bearer"}


def complete_url(state, code):
    complete = reverse("social:complete", args=["gitlab"])
    query = "&".join(["code" + "=" + code, "state" + "=" + state])
    return complete + "?" + query


class TestOAuthCallbackReplay(LoggedInTestCase):
    def setUp(self):
        super().setUp()

        # fast tenants are reused between test classes, so setup_tenant() is not
        # called when the schema already exists. the pipeline creates a user
        # which is not an authorized tenant user, hence allow everyone in
        self.tenant.publicly_readable = True
        self.tenant.save(update_fields=["publicly_readable"])

        self.oauth_settings = override_settings(
            AUTHENTICATION_BACKENDS=AUTH_BACKENDS,
            SOCIAL_AUTH_GITLAB_KEY="test-key",
            SOCIAL_AUTH_GITLAB_SECRET="test-secret",
        )
        self.oauth_settings.enable()
        self.addCleanup(self.oauth_settings.disable)

        self.client.logout()
        self.client.raise_request_exception = False

    def begin(self):
        response = self.client.post(reverse("social:begin", args=["gitlab"]))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        query = parse_qs(urlsplit(response["Location"]).query)
        self.assertIn("state", query)
        state = query["state"][0]

        transaction = "gitlab_oauth2_state_" + state
        self.assertIn(transaction, self.client.session)
        return state, transaction

    def assert_login_redirect(self, response):
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], reverse("tcms-login"))

        messages = []
        for message in get_messages(response.wsgi_request):
            messages.append(str(message))
        for message in messages:
            if SESSION_UNAVAILABLE in message:
                return
        self.fail("expected an error message, got: " + repr(messages))

    @patch.object(GitLabOAuth2, "user_data", return_value=GITLAB_USER)
    @patch.object(
        GitLabOAuth2, "request_access_token", return_value=access_token_response()
    )
    def test_state_is_claimed_by_the_first_callback(self, _token, _user):
        state, transaction = self.begin()
        url = complete_url(state, "test-code")

        first = self.client.get(url)
        self.assertEqual(first.status_code, HTTPStatus.FOUND)

        # the transaction is consumed before the code is exchanged
        self.assertNotIn(transaction, self.client.session)

    @patch.object(GitLabOAuth2, "user_data", return_value=GITLAB_USER)
    @patch.object(
        GitLabOAuth2, "request_access_token", return_value=access_token_response()
    )
    def test_replay_of_callback_url_shows_error_instead_of_500(self, _token, _user):
        state, _transaction = self.begin()
        url = complete_url(state, "test-code")

        first = self.client.get(url)
        self.assertEqual(first.status_code, HTTPStatus.FOUND)

        second = self.client.get(url)
        self.assert_login_redirect(second)

    @patch.object(GitLabOAuth2, "user_data", return_value=GITLAB_USER)
    @patch.object(
        GitLabOAuth2, "request_access_token", return_value=access_token_response()
    )
    def test_callback_without_begin_session_shows_error_instead_of_500(
        self, _token, _user
    ):
        state, _transaction = self.begin()
        url = complete_url(state, "test-code")

        other = TenantClient(self.tenant)
        other.raise_request_exception = False
        response = other.get(url)
        self.assert_login_redirect(response)
