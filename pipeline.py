from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from tcms.utils.permissions import initiate_user_with_default_setups


def email_is_required(strategy, details, backend, user=None, *args, **kwargs):
    if not details['email']:
        messages.error(
            strategy.request or backend.strategy.request,
            _("Email address is required")
        )
        return HttpResponseRedirect(reverse('tcms-login'))


def check_if_email_is_in_use(strategy, details, backend, user=None, *args, **kwargs):
    try:
        User.objects.get(email=details['email'])
    except User.DoesNotExist:
        pass

    messages.error(
        strategy.request or backend.strategy.request,
        _("A user with address %(email)s already exists") % {'email': details['email']}
    )
    return HttpResponseRedirect(reverse('tcms-login'))


def initiate_defaults(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        initiate_user_with_default_setups(user)
