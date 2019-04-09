from django.conf.urls import include, url

from tcms.urls import urlpatterns


urlpatterns += [
    url('', include('social_django.urls', namespace='social')),
]


try:
    from tcms_tenants import urls as tcms_tenants_urls

    urlpatterns += [
        url(r'^tenants/', include(tcms_tenants_urls, namespace='tenants')),
    ]
except ImportError:
    pass
