from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'iwa.views.home', name='home'),
    url(r'^iwa/', 'fp.views.index'),
    url(r'^auth_handler/', 'fp.views.auth_handler'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^main/', 'fp.views.main'),
    url(r'^artist/', 'fp.views.artist'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
                       
)
