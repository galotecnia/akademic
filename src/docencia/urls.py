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
from faltas.models import Parte

urlpatterns = patterns('',
    (r'^informes/',     include('docencia.informes.urls')),
    (r'^verificacion/', include('docencia.verificacion.urls')),
)

urlpatterns += patterns('docencia.views',
    url(r'^$',                                      'akademicLogin', name='login'),
    url(r'^error/$',                                'error', name='error'),
    url(r'^menu/(?P<menu>\w+)/$',                   'gestionMenu', name='gestion_menu'),
    url(r'^profesor-index(/(?P<task>\w+)(/(?P<semana_id>\d+))?)?/$', 'profesorIndex', name='profesor_index'),
    url(r'^faltasActual/$',                         'faltas', {'tipo': 'faltas'}, name='profesor_faltas_actual'),
    url(r'^faltasActual/(?P<inserta>\d)/$',         'faltas', {'tipo': 'faltas'}, name='profesor_faltas_inserta'),
    url(r'^faltas/(?P<fecha>\d+-\d+-\d+)/(?P<hora_id>\d+)/$', 'faltas', {'tipo': 'faltas'}, name='profesor_faltas_fecha'),
    url(r'^faltas/(?P<fecha>\d+-\d+-\d+)/(?P<hora_id>\d+)/(?P<inserta>\d)/$', 'faltas', {'tipo': 'faltas'}, name='profesor_faltas_fecha_inserta'),
    url(r'^faltas/(?P<fecha>\d+-\d+-\d+)/$', 'faltas', {'tipo': 'faltas', 'hora_id': None}, name='profesor_faltas_especiales'),
    url(r'^faltas/(?P<fecha>\d+-\d+-\d+)/(?P<inserta>\d)/$', 'faltas', {'tipo': 'faltas', 'hora_id': None}, name='profesor_faltas_especiales_inserta'),
    url(r'^comportamientoActual/$',                 'faltas', {'tipo': 'comportamiento'}, name='profesor_comportamiento_actual'),
    url(r'^comportamiento/(?P<fecha>\d+-\d+-\d+)/(?P<hora_id>\d+)/$', 'faltas', {'tipo': 'comportamiento'}, name='profesor_comportamiento_fecha'),
    url(r'^comportamiento/(?P<fecha>\d+-\d+-\d+)/$', 'faltas', {'tipo': 'comportamiento', 'hora_id': None}, name='profesor_comportamiento_especial'),
    url(r'^insertafaltas/$',                        'insertaFalta', {'tipo': 'faltas'}, name='profesor_inserta_faltas'),
    url(r'^insertacomportamiento/$',                'insertaFalta', {'tipo': 'comportamiento'}, name='profesor_inserta_comportamiento'),
    url(r'^horarioFaltas(/(?P<semana>-?\d+))?/$',   'horarioProfesor', {'tipo': 'faltas'}, name='profesor_horario_faltas'),
    url(r'^horarioComportamiento(/(?P<semana>-?\d+))?/$', 'horarioProfesor', {'tipo': 'comportamiento'}, name='profesor_horario_comportamiento'),
    url(r'^listasTutorAsignaturas/$',               'listasTutorAsignaturas', name='tutor_lista_asignaturas'),
    url(r'^printListasTutorAsignaturas/$',          'listasTutorAsignaturas', name='tutor_print_lista_asignaturas'),
    url(r'^listasTutorTotales/$',                   'listasTutorTotales', name='tutor_lista_totales'),
    url(r'^listadosProfesor/$',                     'listadosProfesor', name='profesor_mostrar_listados'),
    url(r'^Akademic.ics$',                          'getCitasiCalendar', name='get_citas_calendar'),
    url(r'^citas/$',                                'listaCitasProfes', name='profesor_lista_citas'),
    url(r'^citas/(?P<fecha>\d+)/$',                 'detailCitas', name='profesor_detail_citas'),
    url(r'^notificacionSmsProfesor/$',              'notificacionSmsProfesor', name='notificacion_sms_profesor'),
    url(r'^notificacionSmsMasivo/$',                'envio_notificaciones_sms_agrupadas', 
                                                        { 'urlname': 'niveles'}, name='notificacion_sms_masivo'),
    url(r'^notificacionSmsPorCurso/$',              'envio_notificaciones_sms_agrupadas', 
                                                        { 'urlname': 'cursos'}, name='notificacion_sms_curso'),
                                                        
    url(r'^notificacion_sms_grupo/$',               'envio_notificacion_grupo', name='notificacion_sms_grupo'),  
    url(r'^notificacion_sms_grupo/(?P<grupo>\d+)/$', 'envio_notificacion_grupo', name='notificacion_sms_grupo_orientador'),                                  
    url(r'^estadoNotificacion/$',                   'estadoNotificacion', name='estado_notificacion'),
    url(r'^estadoNotificacion/(?P<page>\d+)/$',     'estadoNotificacion', name='estado_notificacion'),    
    url(r'^poseer/$',                               'posesion', name='profesor_posesion'),
    #url(r'^evaluacionProfesor/$',                   'evaluacionProfesor', name='profesor_evaluacion'),
    #url(r'^evaluacionTutor/(?P<tutor>\w+)/$',       'evaluacionProfesor', name='tutor_evaluacion'),
    url(r'^evaluarCompetencias/$',                  'evaluarCompetencias', name='evaluar_competencias'),
    url(r'^nuevaEvaluacion/$',                      'nuevaEvaluacion', name='nueva_evaluacion'),
    url(r'^generarBoletin/$',                       'generarBoletin', name='generar_boletin'),
    url(r'^comentario/$',                           'comentario', name='comentario'),
    url(r'^reenvioPassword/$',                      'reenvioPassword', name='reenvio_password'),

    url(r'^informeNagios/$',                        'informeNagios', name='informe_nagios'),
    url(r'^boletinQT/$',                            'boletinQT', name='boletin_qt'),
    url(r'^grupo/$',                                'selecciona_grupo', name='selecciona_grupo'),
    url(r'^grupo_sms/$',                            'selecciona_grupo_sms', name='selecciona_grupo_sms'),
    url(r'^grupo_je/$',                             'grupo_informe_je', name='selecciona_grupo_je'),
    url(r'^dias_especiales/$',                      'gestion_dias_especiales', name='dias_especiales'),
    url(r'^lista_dias_especiales/$',                'special_days_list', name='lista_dias_especiales'),
    url(r'^eliminar_dia/(?P<dia_id>\d+)/$',         'del_special_day', name='dia_especial_eliminar'),
    url(r'^attach_file/$',                          'attach_file', name='attach_file'),
)

parte_dict = {
    'queryset': Parte.objects.all(),
}

urlpatterns += patterns('django.views.generic.list_detail',
    url(r'^partes/$',                               'object_list', dict(parte_dict, paginate_by=20, allow_empty=True), name='partes'),
    url(r'^partes/page(?P<page>[0-9]+)/$',          'object_list', dict(parte_dict, paginate_by=20, allow_empty=True), name='partes_page'),
    url(r'^parte/(?P<object_id>[0-9]+)/$',          'object_detail', parte_dict, name='parte_object'),
)
