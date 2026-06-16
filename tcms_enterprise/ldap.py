# Copyright (c) 2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django_python3_ldap import utils

from tcms.utils.permissions import initiate_user_with_default_setups


def sync_user_relations(user, ldap_attributes):
    """
    Assign users default group(s) and permissions!
    """
    utils.sync_user_relations(user, ldap_attributes)
    initiate_user_with_default_setups(user)
