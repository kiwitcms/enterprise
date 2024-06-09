# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django import template
from django.db import connection
from django.urls import reverse

register = template.Library()


@register.simple_tag
def next_url(request):
    """
        Return a URL which will faciliate GitHub login for tenants
        (avoiding request_uri mismatch) or a regular path when
        tcms_tenants is not installed.

        Used for the ?next= parameter of PSA URLs.
    """
    next_value = request.GET.get('next', '/')

    if connection.schema_name != 'public':
        next_value = reverse('tcms_tenants:redirect-to',
                             args=[connection.schema_name, next_value])

    # handle double slashes in case we want to redirect to tenant's root
    return next_value.replace('//', '/')
