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

urlpatterns = patterns('docencia.informes.views',
    url(r'^resumen_tutor/$',            'resumen_tutor', name = 'resumen_tutor'),
    url(r'^informe_tutor/$',            'informe_tutor', name = 'informe_tutor'),
    url(r'^informe_tutor/(?P<grupo>\d+)/$', 'informe_tutor', name = 'informe_tutor_grupo'),
    url(r'^informe_partes/$',           'informe_partes', name = 'informe_partes'),
    url(r'^informe_personalizado/$',    'informe_personalizado', name = 'informe_personalizado'),
    url(r'^informe_personalizado/(?P<grupo>\d+)/$', 'informe_personalizado', name = 'informe_personalizado_grupo'),
    url(r'^resumenEvaluacionProfesor/$', 'resumenEvaluacionProfesor', {'tipo': 'Profesor'}, name = 'resumen_evaluacion_profesor'),
    url(r'^resumenEvaluacionTutor/$',   'resumenEvaluacionProfesor', {'tipo': 'Tutor'}, name = 'resumen_evaluacion_tutor'),
    url(r'^resumenEvaluacionTutor/(?P<grupo>\d+)/$', 'resumenEvaluacionProfesor', {'tipo': 'Tutor'}, name = 'resumen_evaluacion_tutor_grupo'),
    url(r'^informe_absentismo/$', 'informe_absentismo', name='informe_absentismo'),
)
