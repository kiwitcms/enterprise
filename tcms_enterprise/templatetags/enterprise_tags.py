# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

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
    next = request.GET.get('next', '/')

    if connection.schema_name != 'public':
        next = reverse('tcms_tenants:redirect-to', args=[connection.schema_name, next])

    # handle double slashes in case we want to redirect to tenant's root
    return next.replace('//', '/')
