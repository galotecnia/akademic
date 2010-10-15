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

urlpatterns = patterns('incidencias.views',
    url(r'^$',                                               'index', name="incidencias"),
    url(r'^lista/(?P<tipo_incidencia>\d+)/(?P<estado>\w*)/', 'lista', name="listar_incidencias"),
    url(r'^lista/(?P<tipo_incidencia>\d+)/',                 'lista', name="listar_incidencias"),
    url(r'^lista/',                                          'lista', name="listar_incidencias"),
    url(r'^detalles/(?P<incidencia_id>\d+)/',                'detalles', name="detalles_incidencia"),
    url(r'^nueva/',                                          'nueva', name="nueva_incidencia"),
    url(r'^comentario/',                                     'nuevoComentario', name="nuevo_comentario"),
    url(r'^cerrar/(?P<incidencia_id>\d+)/',                  'lista', name="cerrar_incidencia"),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^nuevaok/', 'direct_to_template', {'template': 'incidencias/nueva-mensaje-ok.html'}, name="nueva_incidencia_ok"),
)
