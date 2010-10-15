# -*- coding: utf-8 -*-
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
from django.shortcuts import render_to_response 
from django.contrib.auth.decorators import login_required 
from django.template import RequestContext
from docencia.models import *
from docencia.models import *
from padres.models import *
from notificacion.models import TextoNotificacion, Notificacion

from docencia.auxFunctions import *
from docencia.tutoria.models import Cita, Tutoria

import os, operator

TEMPLATES = {'pas_nueva_cita':          'nuevaCita.html',
             'pas_lista_citas':         'listaCitas.html',             
             'default_pas_error_page':  'nuevaCita.html',
             'pas_reenvio_pass':        'reenviopassword.html',
             'pas_cita_detail':         'detailCita.html',
             'pas_cita_delete':         'listaCitas.html', }

def error_logging_pas(request):    
    context = {'error': 'Su usuario no estￃﾡ asignado a una cuenta de PAS.' }
    return render_to_response(
            TEMPLATES['default_pas_error_page'],
            context,
            context_instance=RequestContext(request))

@login_required
def reenvioPassword (request):
    """
        Permite buscar a un padre al que se le regenerará la su password y
        se le enviará por sms junto a su nombre de usuario.
    """
    context = {}
    pas = isPas(request.user)
    if not pas:
        context['error'] = 'Su usuario no está asignado a una cuenta de PAS'
        return render_to_response(
                "akademic/error.html",
                context,
                context_instance=RequestContext(request)
            )
    if request.POST:
        new_data = request.POST.copy()
        if new_data.has_key('query'):
            search_fields = ['persona__documento_identificacion', 'persona__nombre', 'persona__apellidos']
            for bit in new_data['query'].split():
                or_queries = [models.Q(**{'%s__icontains' % field_name: bit}) for field_name in search_fields]
            context['padres'] = Padre.objects.filter(reduce(operator.or_, or_queries))
            if not len(context['padres']):
                context['notFound'] = True
        elif new_data.has_key('padre'):
            passwd = User.objects.make_random_password(length=6)
            try:
                u = Padre.objects.get (persona = new_data['padre'])
            except Padre.DoesNotExist:
                return render_to_response(
                        "akademic/error.html",
                        context,
                        context_instance=RequestContext(request)
                    )
            u.persona.user.set_password(passwd)
            u.persona.user.save()
            texto = "Nombre de usuario: %s  Contraseña: %s" % (u.persona.user, passwd)
            t = TextoNotificacion(texto = texto)
            t.save ()
            try:
                n = Notificacion(
                    padre = u, 
                    alumno = u.get_hijos()[0],
                    fechaCreacion = datetime.datetime.now(), 
                    fechaEnvio = None, 
                    texto = t, 
                    estado = ESTADO_NOTIFICACION[0][0],
                    confidencial = True)
                n.save()
            except IndexError:
                return render_to_response(
                        "akademic/error.html", 
                        context,
                        context_instance=RequestContext(request)
                    )

    return render_to_response(
            TEMPLATES['pas_reenvio_pass'],
            context,
            context_instance=RequestContext(request)
        )

@login_required
def listaCitas(request, aviso=None):
    """
        Muestra una lista de citas al usuario de portería permitiendo ver los
        detalles correspondientes e incluso eliminar una cita concreta.
    """
    pas = isPas(request.user)
    if not pas:
        return error_logging_pas(request)
        
    context = {}
    context['task'] = 'listaCitas'
    # Estos parámetros son necesarios para el formulario fechas
    context['action'] = './'
    context['pas'] = pas
    context['citas'] = Cita.objects.all().order_by("fecha")
    if aviso:
        context['aviso'] = aviso

    return render_to_response(                              
            TEMPLATES['pas_lista_citas'],
            #"akademic/porteria/listaCitas.html", 
            context,
            context_instance=RequestContext(request)
                )
    
@login_required
def citaDetail(request, cita_id):
    """
        Muestra los detalles de una cita concreta.
    """
    context = {}
    pas = isPas(request.user)
    if not pas:
        context['error'] = 'Su usuario no está asignado a una cuenta de PAS'
        return render_to_response(
                "porteria/detailCita.html", 
                context,
                context_instance=RequestContext(request)
            )

    context['task'] = 'listaCitas'
    cita = Cita.objects.filter(pk = cita_id)
    if not cita:
        context['aviso'] = "La cita seleccionada no existe"
    else:
        context['cita'] = cita[0]
    return render_to_response(
            TEMPLATES['pas_cita_detail'],
            context,
            context_instance=RequestContext(request)
        )

@login_required
def citaDelete(request, cita_id):
    """
        Elimina una cita
    """
    context = {}

    pas = isPas(request.user)
    if not pas:
        context['error'] = 'Su usuario no está asignado a una cuenta de PAS'
        return render_to_response(
                TEMPLATE['pas_cita_lista'],
                context,
                context_instance=RequestContext(request)
            )

    context['task'] = 'listaCitas'
    cita = Cita.objects.filter(pk = cita_id)
    if not cita:
        aviso = "La cita seleccionada no existe"
    else:
        cita[0].delete()
        aviso = "La cita se ha eliminado correctamente"
    return listaCitas(request, aviso)
    
@login_required
def nuevaCita(request):
    """
        Este método permite poner citas en las horas de tutoría
        al personal de la portería del centro.
    """    
    pas = isPas(request.user)
    if not pas:
        return error_logging_pas(request)    

    context = {}
    context['task'] = 'nuevaCita'
    # Estos parámetros son necesarios para el formulario fechas
    context['action'] = './'
    context['pas'] = pas
    context['grupos'] = GrupoAula.objects.filter(curso__ciclo__nivel__cursoEscolar = 
                settings.CURSO_ESCOLAR_ACTUAL).exclude(seccion = "Pendientes").order_by(
                    'curso__ciclo__nivel', 'curso', 'seccion')
    context['etapa'] = 'grupos'
    
    def html_response():
        return render_to_response(
            TEMPLATES['pas_nueva_cita'],
            context,
            context_instance=RequestContext(request) )
    
    if request.POST:
        new_data = request.POST.copy()
        if new_data.has_key('etapa'):
            if new_data['etapa'] == 'grupos':
                # Se ha seleccionado el grupo con el que se quiere trabajar.
                # Simplemente tendremos que mostrar los alumnos pertenecientes a ese
                # grupo
                if new_data.has_key('grupo'):
                    # Devolver los alumnos del grupo y el tutor, obviamente que estén matriculados
                    context['etapa'] = 'alumno'
                    alus = GrupoAulaAlumno.objects.filter(grupo=new_data['grupo']).values('alumno').distinct()
                    alusId = []
                    for i in alus:
                        alusId.append(i['alumno'])
                    alumnos = Alumno.filter(id__in=alusId)
                    context['alumnos'] = alumnos
                    context['tutor'] = Tutor.objects.filter(grupo=new_data['grupo'])[0]
                else:
                    context['aviso'] = "No ha seleccionado un grupo"
            elif new_data['etapa'] == 'alumno':
                # Estamos en la selección de alumno
                if new_data.has_key('alumnosel'):
                    context['alumno'] = Alumno.objects.get(pk=new_data['alumnosel'])
                    context['tutor'] = Tutor.objects.get(pk=new_data['tutor'])
                    tut = Tutoria.objects.filter(tutor=context['tutor'])
                    if tut:
                        context['tutoria'] = tut[0]
                        context['fechas'] = context['tutoria'].proximasFechas(context['alumno'])
                        context['etapa'] = "cita"
                    else:
                        context['aviso'] = "No hay horario de atención a padres definido"
                        context['etapa'] = "grupos"
                else:
                    context['aviso'] = "No ha seleccionado al alumno"
            elif new_data['etapa'] == 'cita':
                try:
                    (dia, mes, anyo) = new_data['fechasel'].split('-')
                except KeyError:
                    context['aviso'] = "No ha elegido un grupo"
                    return html_response()                                            
                tut = Tutor.objects.get(pk = new_data['tutor'])
                tutoria = Tutoria.objects.filter(tutor = tut)[0]
                alu = Alumno.objects.get(pk = new_data['alumno'])                
                fecha = datetime.datetime(year = int(anyo), month= int(mes), day = int(dia))
                if new_data.has_key('madre'):
                    madre = True
                else:
                    madre = False
                if new_data.has_key('padre'):
                    padre = True
                else:
                    padre = False                
                ncita = Cita(tutoria = tutoria, padre = padre, madre = madre, 
                            alumno = alu, fecha = fecha, avisadoSMS = False, 
                            avisadoEMAIL = False)
                ncita.save()
                context['aviso'] = "Se ha reservado la cita correctamente"
    else:
        context['aviso'] = "Sólo se listan los cursos para los que se ha definido alguna tutoría"

    return html_response()
