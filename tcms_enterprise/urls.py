import os
from django.conf.urls import include, url

from tcms.urls import urlpatterns


urlpatterns += [
    url('', include('social_django.urls', namespace='social')),
]


# unconditional configuration of multi-tenant URLs
from tcms_tenants import urls as tcms_tenants_urls

urlpatterns += [
    url(r'^%stenants/' % os.environ.get('KIWI_TENANTS_URL_PREFIX', ''),
        include(tcms_tenants_urls, namespace='tenants')),
]
