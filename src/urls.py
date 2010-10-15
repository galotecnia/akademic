# -*- encoding: utf-8 -*-
"""
    Akademic: Herramienta para el control del alumnado en centros escolares.

    Copyright (C) 2010  Galotecnia Redes Sistemas y Servicios S.L.L. <info@galotecnia.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
import authority

admin.autodiscover()
authority.autodiscover()

if settings.MAINTENANCE:
    akademic_patterns = patterns('',
        (r'^admin/',             include(admin.site.urls)),
        (r'',          'docencia.views.work_in_progress'), 
    )
else:
    akademic_patterns = patterns('',
        (r'^$',                 'docencia.views.akademicLogin'),
        url(r'^accounts/login/$',  'docencia.views.akademicLogin', name='login'),
        url(r'^accounts/logout/$', 'docencia.views.akademicLogout', name='logout'),
        (r'^akademic/',          include('docencia.urls')),
        (r'^admin/',             include(admin.site.urls)),
        (r'^incidencias/',       include('incidencias.urls')),
        (r'^recursos/',          include('recursos.urls')),
        (r'^conector/',          include('conector.urls')),
        (r'^padres/',            include('padres.urls')),
        (r'^pas/',               include('pas.urls')),
        (r'^authority/',         include('authority.urls')),
        # Sólo en modo de desarrollo.
        (r'^site-media/(.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )

cleaned_site_location = settings.SITE_LOCATION.lstrip('/')
if cleaned_site_location != "": cleaned_site_location += "/"

urlpatterns = patterns('',
    (cleaned_site_location, include(akademic_patterns)),
)
