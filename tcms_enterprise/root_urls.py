from django.conf.urls import include, url

from tcms.urls import urlpatterns


urlpatterns += [
    url('', include('social_django.urls', namespace='social')),
]
