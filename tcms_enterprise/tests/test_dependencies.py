# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import importlib.metadata

from django.test import SimpleTestCase


class TestInstalledVersions(SimpleTestCase):
    def test_dependencies_match_their_pins(self):
        for distribution in ("kiwitcms", "kiwitcms-enterprise"):
            for requirement in importlib.metadata.requires(distribution) or []:
                if "==" not in requirement:
                    continue

                requirement = requirement.split(";")[0]
                name, pinned = requirement.split("==")
                name = name.split("[")[0].strip()
                pinned = pinned.strip()
                installed = importlib.metadata.version(name)

                self.assertEqual(
                    installed,
                    pinned,
                    f"{name} is {installed} but {distribution} requires {pinned}",
                )
