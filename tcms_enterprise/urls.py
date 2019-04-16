import os
from django.conf.urls import include, url

from tcms.urls import urlpatterns


urlpatterns += [
    url('', include('social_django.urls', namespace='social')),
]


# only if outside docker image has defined a PostgreSQL database
if os.environ.get('KIWI_DB_ENGINE', '').find('postgresql') > -1:
    try:
        from tcms_tenants import urls as tcms_tenants_urls

        urlpatterns += [
            url(r'^%stenants/' % os.environ.get('KIWI_TENANTS_URL_PREFIX', ''),
                include(tcms_tenants_urls, namespace='tenants')),
        ]
    except ImportError:
        pass
