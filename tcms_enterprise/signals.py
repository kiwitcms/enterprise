# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html


def bind_application_to_user(token, **kwargs):
    # dynamically registered clients have no owner until a user authorizes them
    if token.application.user_id is None and token.user_id is not None:
        token.application.user_id = token.user_id
        token.application.save(update_fields=["user"])
