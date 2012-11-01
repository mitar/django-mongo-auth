from django.conf.urls import patterns, include, url

from . import views
from .. import urls

urlpatterns = urls.build_patterns(views) + patterns('',
    url(r'^account/setlanguage/$', views.set_language, name='set_language'),
)
