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

urlpatterns = patterns('padres.views',
	url(r'^$', 										    'padresIndex', name='padres_root'),
	url(r'^informacion-personal/$', 					'padresInfo', name='padres_personal_info'),
	url(r'^cuenta/$', 									'padresCuenta', name='padres_cuenta'),
	url(r'^actualiza-informacion-personal/$', 		    'updatePadresInfo', name='padres_actualiza_info'),
	url(r'^(?P<tipo_falta>(faltas\w*|retrasos))/$',     'listaFaltas', name='padres_faltas'),
	url(r'^(?P<hijo_id>\d+)/$(?P<tipo_falta>(faltas\w*|retrasos))/', 'listaFaltasHijo', name= 'padres_faltas_hijo'),
	url(r'^ausencias/$', 								'listaAusencias', name='padres_ausencias'),
	url(r'^ausencias/(?P<hijo_id>\d+)/$', 				'listaAusencias', name='padres_ausencias_hijo'),
	url(r'^citas/$',									'citasPadres', name='padres_cita'),
	url(r'^iCalendar/Akademic.ics$',					'getiCalendar', name='padres_icalendar'),
	url(r'^comentarios/$',								'comentarios', name='padres_comentarios'),
	url(r'^comentarios/(?P<comm_id>(\d+))/$',			'comentarios', name='padres_comentario'),
	url(r'^listaCalificaciones/$',						'listaCalificaciones', name='padres_calificaciones'),
	url(r'^boletin/$',									'boletin', name='padres_boletin'),
    url(r'^files/$',                                    'get_files', name='padres_files'),
    url(r'^send/(?P<file_id>\d+)/$',                    'send_file', name='padres_send_file'),
)

