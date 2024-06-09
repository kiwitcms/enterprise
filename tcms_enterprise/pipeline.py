# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=unused-argument, keyword-arg-before-vararg

import uuid

from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from tcms.utils.permissions import initiate_user_with_default_setups


def email_is_required(strategy, details, backend, user=None, *args, **kwargs):
    if not details['email']:
        messages.error(
            strategy.request or backend.strategy.request,
            _("Email address is required")
        )
        return HttpResponseRedirect(reverse('tcms-login'))

    return None


def initiate_defaults(strategy, details, backend, user=None, *args, **kwargs):
    if user and kwargs.get('is_new', False):
        initiate_user_with_default_setups(user)


def random_password(strategy, details, backend, user=None, *args, **kwargs):
    """
        Generate's a random password b/c when it is None Django will not
        allow the user to reset it!
    """
    if user and kwargs.get('is_new', False):
        user.set_password(uuid.uuid4().hex)
        user.save()
