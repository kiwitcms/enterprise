from django.urls import re_path
from django.conf.urls import include

from tcms.urls import urlpatterns


urlpatterns += [
    re_path(r'', include('social_django.urls', namespace='social')),
]
