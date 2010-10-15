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
from views import *

urlpatterns = patterns('pas.views',
	url(r'^nuevaCita/$',                    'nuevaCita',        name='pas_nueva_cita'),
	url(r'^listaCitas/$',	                'listaCitas',       name='pas_lista_citas'),
	url(r'^reenvioPassword/$',	            'reenvioPassword',  name='pas_reenvio_pass'),
	url(r'^citas/(?P<cita_id>\d+)/detail/$','citaDetail',       name='pas_cita_detail'),
	url(r'^citas/(?P<cita_id>\d+)/delete/$','citaDelete',       name='pas_cita_delete'),
)

