# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from social_core.backends.github import GithubAppAuth as SocialGithubAppAuth


class GithubAppAuth(SocialGithubAppAuth):
    title = "GitHub"
