# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import base64

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from tcms_enterprise.markdown import mermaid2url


class TestMermaid2Url(SimpleTestCase):
    def test_url_is_built_from_renderer_and_source(self):
        source = "flowchart LR\n    Start --> Stop"
        url = mermaid2url(source)

        prefix = "https://mermaid.ink/img/"
        suffix = "?type=png"
        self.assertTrue(url.startswith(prefix))
        self.assertTrue(url.endswith(suffix))

        encoded = url[len(prefix) : -len(suffix)]
        self.assertEqual(base64.b64decode(encoded).decode("utf8"), source)

    @override_settings(MERMAID_RENDERER_URL="https://example.com/render")
    def test_renderer_url_is_configurable(self):
        self.assertTrue(
            mermaid2url("graph TD").startswith("https://example.com/render/")
        )


class TestDatabase(TestCase):
    def test_migrations_run_and_db_works(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="sanity", password="sanity")
        self.assertEqual(user_model.objects.get(pk=user.pk).username, "sanity")
