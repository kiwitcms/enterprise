# Copyright (c) 2020-2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import re_path
from django.conf.urls import include

from tcms.urls import urlpatterns


urlpatterns += [
    re_path(r'', include('social_django.urls', namespace='social')),
]
