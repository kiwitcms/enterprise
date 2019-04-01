# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django import template
from django.db import connection


register = template.Library()


@register.simple_tag
def next_url(request):
    """
        Return a full URL when working with tenants or
        a path when tcms_tenants is not installed.

        Used for the ?next= parameter of PSA URLs.
    """
    try:
        from tcms_tenants import utils

        return utils.tenant_url(request, connection.schema_name)
    except ImportError:
        return request.GET.get('next', '/')
