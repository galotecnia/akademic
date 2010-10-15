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

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect 
from django.core.urlresolvers import reverse 
from django.template import RequestContext

from docencia.models import *
from docencia.tutoria.models import Cita, Tutoria
from docencia.auxFunctions import *
from docencia.customExceptions import *
from docencia.libs.djangoOOGalo import DjangoWriter

from models import *
from forms import PadreInfoForm, PadrePassword 
from docencia.constants import *
from utils.iCalendar import events2iCalendar, HttpResponseCalendar, DURACION_CITA_POR_DEFECTO

from addressbook.models import *
import datetime, time, calendar

from django.conf import settings

import os

from authority.decorators import permission_required_or_403, permission_required
from docencia.permissions import AlumnoPermission

import logging

log = logging.getLogger('galotecnia')

# Número de citas a mostrar en la vista de "Visitas"
MIN_CITAS = 10
INF = 'INF'

tipoFaltas = {
    'faltas' : {
        'nombreInfantil': 'Faltas de Asistencia',
        'nombre' : 'Faltas de Asistencia',
        'tipo' : FALTA_ASISTENCIA
    },
    'faltasComportamientos' : {
        'nombreInfantil' : 'Ha estado triste',
        'nombre' : 'Faltas de Comportamiento',
        'tipo' : FALTA_COMPORTAMIENTO
    },
    'faltasTarea' : {
        'nombreInfantil' : 'No ha comido bien',
        'nombre' : 'Faltas de Tarea',
        'tipo' : FALTA_TAREA
    },
    'faltasMaterial' : {
        'nombreInfantil' : 'No ha trabajado',
        'nombre' : 'Faltas de Material',
        'tipo' : FALTA_MATERIAL
    },
    'retrasos' : {
        'nombreInfantil' : 'Retrasos',
        'nombre' : 'Retrasos',
        'tipo' : RETRASO
    },
}

TIPOS_CONTACTO = {'casa': T_PERSONAL, 'movil': M_PERSONAL, 'trabajo': T_TRABAJO, 'email': EM_PERSONAL, 'fax': F_PERSONAL,}

@permission_required('padres_permission.check_padre')
def padresIndex (request):
    """
        Muestra la pagina de bienvenida para los padres de los alumnos del colegio
    """
    padre = isPadre(request.user)
    context = {}
    context['padre'] = padre
    return render_to_response('padres/index.html', context, context_instance=RequestContext(request))

@permission_required('padres_permission.check_padre')
def padresInfo (request):
    """
        Método para mostrar la información personal
    """
    padre = isPadre(request.user)
    context = {}
    context['padre'] = padre
    return render_to_response('padres/informacion-personal.html', context, context_instance=RequestContext(request))

@permission_required('padres_permission.check_padre')
def updatePadresInfo (request):
    """
        Método para actualizar la información personal de los padres
    """
    padre = isPadre(request.user)
    context = {}
    context['padre'] = padre
    p = padre.persona
    rc = RequestContext(request)
    inicial = {'nombre': p.nombre, 'apellidos': p.apellidos, 'casa': p.tlf_casa(), 
        'movil': p.tlf_movil(), 'trabajo': p.tlf_trabajo(), 'email': p.email(),
        'fax': p.fax(), }
    form = PadreInfoForm(inicial) 
    context['form'] = form
    return render_to_response('padres/informacion-personal.html', context, rc)

@permission_required('padres_permission.check_padre')
def listaFaltas (request, tipo_falta):
    """
        Muestra la lista de faltas de todos los hijos de un padre
    """
    if request.POST:
        post = request.POST.copy()
        if int(post['alumno_id']) != 0:
            return listaFaltasHijo (request, post['alumno_id'], tipo_falta)

    context = {}
    
    padre = isPadre(request.user)
    hijos = padre.get_hijos_matriculados()
    
    hijo_infantil = False
    hijo_noinfantil = False
    context['hijos'] = []
    p = AlumnoPermission(request.user)
    tipo = tipoFaltas[tipo_falta]['tipo']
    for i in hijos:
        if p.has_alu_priv(i):
            context['hijos'].append( { 
                'hijo' : i,
                'faltas' : i.getFaltas(tipo),
            } )
            g = i.getGrupo()
            if g and g.grupo.curso.ciclo.nivel.nombre == INF:
                hijo_infantil = True
            else:
                hijo_noinfantil = True

    if not context['hijos']:
        context['error'] = "No se han encontrado hijos"
        return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))

    context['nombre'] = ""
    if hijo_noinfantil:
        context['nombre'] += tipoFaltas[tipo_falta]['nombre']
    if hijo_infantil:
        if context['nombre'] != "":
            context['nombre'] += '/'
        context['nombre'] += tipoFaltas[tipo_falta]['nombreInfantil']
    context['numHijos'] = context['hijos'].__len__()
    return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))

@permission_required('padres_permission.check_padre')
def listaFaltasHijo (request, hijo_id, tipo_falta):
    """
        Muestra la lista de faltas de un hijo determinado
    """

    context = {}
    padre = isPadre(request.user)
    if (not padre.get_hijos_matriculados().filter(id = hijo_id)):
        context['error'] = "No se han encontrado hijos"
        return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))

    context['nombre'] = tipoFaltas[tipo_falta]['nombre']
    tipo = tipoFaltas[tipo_falta]['tipo']

    hijo = Alumno.objects.get(pk = hijo_id)
    context['hijos'] = []
    context['hijos'].append( { 
        'hijo' : hijo,
        'faltas' : hijo.getFaltas(tipo),
    } )
    context['numHijos'] = context['hijos'].__len__()
    context['filtrado'] = True

    return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))
    
@permission_required('padres_permission.check_padre')
def listaAusencias (request, hijo_id = None):
    """
        Muestra la lista de ausencias de un hijo determinado o de todos si hijo_id es None
    """
    context = {}

    if ((hijo_id is None) and request.POST):
        # El id del hijo o lo sacamos del post o de los parámetros de entrada
        post = request.POST.copy()
        if int(post['alumno_id']) != 0:
            hijo_id = int (post['alumno_id'])

    padre = isPadre(request.user)
    if hijo_id is not None: # Si tenemos hijo verificamos que tenga privilegio para ver los datos
        if (not padre.get_hijos_matriculados().filter(id = hijo_id)):
            context['error'] = "No se ha encontrado el hijo con id %d" % hijo_id
            return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))
        hijos = [Alumno.objects.get (pk = hijo_id)]
        context['filtrado'] = True
    else:
        hijos = padre.get_hijos_matriculados()

    context['nombre'] = 'Ausencias'
    context['hijos'] = []
    p = AlumnoPermission(request.user)
    for i in hijos:
        if p.has_alu_priv(i):
            context['hijos'].append( { 
                'hijo' : i,
                'faltas' : Ausencia.objects.filter (alumno = i),
            } )
    if not context['hijos']:
        context['error'] = "No se han encontrado hijos matriculados"
        return render_to_response('padres/faltas_generica.html', context, context_instance=RequestContext(request))
    context['numHijos'] = context['hijos'].__len__()
    return render_to_response('padres/ausencias.html', context, context_instance=RequestContext(request))
    
@permission_required('padres_permission.check_padre')
def citasPadres(request):
    """
        Vista para la gestión de citas de los padres
    """
    context = {}
    padre = isPadre(request.user)
    if request.GET: # Nos han enviado un formulario
        if (request.GET.has_key('borrar') and request.GET.has_key('cita_id')):
            # Borrado de citas
            try:
                cita = Cita.objects.get(pk = request.GET['cita_id'])
            except Cita.DoesNotExist:
                context['error'] = 'No existe la cita'
                return render_to_response('padres/citas.html', context, context_instance=RequestContext(request))

            if (cita.padre and cita.alumno.padre != padre) or (cita.madre and cita.alumno.madre != padre):
                context['error'] = 'Fallo al borrar: los propietarios no corresponden'
                return render_to_response('padres/citas.html', context, context_instance=RequestContext(request))

            # TODO: También debería comprobar que la cita no haya pasado pero lo
            # dejo con prioridad baja.
            cita.delete()
            context['aviso'] = 'Cita eliminada'
        else:   
            # Creando nueva cita
            tut_id = request.GET['tutoria_id']
            fecha = request.GET['fecha']
            alu_id = request.GET['hijo']
            alumno = get_object_or_404(Alumno, pk = alu_id)
            tutoria = get_object_or_404(Tutoria, pk = tut_id)
            msg = Cita.nueva_cita(tutoria, fecha, alumno, padre)
            if msg:
                context['error'] = msg
                return render_to_response('padres/citas.html', context, context_instance=RequestContext(request))

            context['aviso'] = 'Su cita se ha creado satisfactoriamente'

    log.debug("Consultando hijos matriculados")
    hijos = padre.get_hijos_matriculados()
    log.debug("Hijos: %s" % hijos)
    log.debug("Consultando citas futuras")
    citas = Cita.objects.filter(alumno__in = hijos, fecha__gte = datetime.datetime.now()).order_by('fecha')
    context['citas'] = citas
    context['hijos'] = []
    p = AlumnoPermission(request.user)
    for i in hijos:
        log.debug("Consultando privilegios del padre sobre el alumno %s" % i)
        if p.has_alu_priv(i):
            context['hijos'].append(i.horario_tutorias())

    return render_to_response('padres/citas.html', context, context_instance=RequestContext(request))

@permission_required('padres_permission.check_padre')
def padresCuenta (request):
    """
        Gestiona el formulario del cambio de contraseÃ±a de los padres.
    """
    context = {}
    padre = isPadre(request.user)
    rc = RequestContext(request)
    if request.POST:
        form = PadrePassword(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data['old_pass']):
                request.user.set_password(form.cleaned_data['new_pass'])
                request.user.save()
                context['msg'] = u"Gracias. Su password se ha actualizado correctamente."
            else:
                context['msg'] = u"El password no coincide con el antiguo, intentelo de nuevo"
        else:
            context['msg'] = u"Ha repetido mal los nuevos passwords, vuelva a escribirlos correctamente"
    else:
        form = PadrePassword()
        context['form'] = form
    
    return render_to_response('padres/cuenta.html', context, rc)

@permission_required('padres_permission.check_padre')
def get_files(request):
    """
        Muestra todos los ficheros pendientes por descargar de los hijos
    """
    context = {}
    padre = isPadre(request.user)
    urls = []
    for hijo in padre.get_hijos_matriculados():
        url = {'hijo': hijo, 'files':[]}
        for file in hijo.fileattach_set.all():
            name = file.file.name.split('/')[-1]
            if not file.visto:
                name = '<b>%s</b>' % name
            url['files'].append({'id': file.id,'name': name})
        if url['files']:
            urls.append(url)
    context['urls'] = urls
    return render_to_response('padres/files.html', context, context_instance = RequestContext(request))

@permission_required('padres_permission.check_padre')        
def send_file(request, file_id = None):
    try:
        file = FileAttach.objects.get(pk = file_id)
    except FileAttach.DoesNotExist:
        return HttpResponseRedirect(reverse('padres_files'))
    file.visto = True
    file.save()
    url = settings.MEDIA_URL +'/' +  file.file.name
    return HttpResponseRedirect(url)

def getiCalendar (request):
    """
        Este método no requiere login ya que se debería usar la autenticación de
        apache para filtrar el acceso al mismo. Dado un usuario padre devuelve un
        documento iCalendar con sus citas
    """

    padre = isPadre(request.user)
    if not padre:
        log.debug(u"Intentando crear un iCalendar para un usuario no padre")
        return HttpResponseRedirect(reverse("error", args=[]))
    citas = Cita.objects.filter(padre = padre, fecha__gte = datetime.datetime.now()).order_by('fecha')

    # Construimos la lista de eventos
    eventos = []
    for c in citas:
        e = {}
        e['resumen'] = "Reunirse con %s" % c.tutoria.tutor
        fecha = datetime.datetime.combine(c.fecha, c.tutoria.hora)
        e['comienzo'] = fecha
        e['final'] = fecha + DURACION_CITA_POR_DEFECTO
        eventos.append(e)

    ical = events2iCalendar(eventos)

    return HttpResponseCalendar(ical)

@permission_required('padres_permission.check_padre')
def comentarios(request, comm_id = None):
    """
        Vista de los comentarios creados por los profesores sobre los hijos de un
        determinado padre.
    """
    context = {}
    context['nombre'] = 'Comentarios'
    
    if comm_id == None:
        padre = isPadre(request.user)
        hijos = padre.get_hijos_matriculados()
        context['hijos'] = []
        p = AlumnoPermission(request.user)
        for i in hijos:
            if p.has_alu_priv(i):
                context['hijos'].append( { 
                    'hijo' : i,
                    'comentarios' : i.getComentarios(),
                } )
        if not context['hijos']:
            context['error'] = "No se han encontrado hijos"
            return render_to_response('padres/comentarios.html', context, context_instance=RequestContext(request))
        context['numHijos'] = len(context['hijos'])
    else:
        try:
            context['comm'] = Comentario.objects.get(pk = comm_id)
            context['comm'].leido = True
            context['comm'].save()
        except Comentario.DoesNotExist:
            context['error'] = 'Lo sentimos, el comentario que está intentando ver no existe'

    return render_to_response('padres/comentarios.html', context, context_instance=RequestContext(request))


@permission_required('padres_permission.check_padre')
def listaCalificaciones (request):
    """
        Muestra las calificaciones de los hijos
    """
    context = {}
    context['hijos'] = []
    context['nombre'] = "Calificaciones"
    if request.POST:
        post = request.POST.copy()
        if int(post['alumno_id']) != 0:
            try:
                i = Alumno.objects.get(pk = post['alumno_id'])
                context['hijos'].append( {
                    'hijo': i, 
                    'evaluaciones': i.getCalificaciones(None, True),
                })
            except Alumno.DoesNotExist:
                context['error'] = "El hijo seleccionado no existe"
            return render_to_response('padres/listaCalificaciones.html', context, context_instance=RequestContext(request))
    
    padre = isPadre(request.user)
    hijos = padre.get_hijos_matriculados()
    p = AlumnoPermission(request.user)
    for i in hijos:
        if p.has_alu_priv(i):
            context['hijos'].append( { 
                'hijo' : i,
                'evaluaciones' : i.getCalificaciones(None, True),
            } )
    context['numHijos'] = len(context['hijos'])
    return render_to_response('padres/listaCalificaciones.html', context, context_instance=RequestContext(request))


@permission_required('padres_permission.check_padre')
def boletin(request):
    """
        Muestra un boletín en formato imprimible.
    """
    if request.REQUEST.has_key('alumno') and request.REQUEST.has_key('evaluacion'):
        try:
            alumno = Alumno.objects.get(pk = request.REQUEST['alumno'])
        except Alumno.DoesNotExist:
            raise FatalError("El alumno no existe en la base de datos")
        writer = DjangoWriter()
        writer.loadFile(os.path.join(settings.OOTEMPLATES, 'boletin.odt'))
        alumno.generaBoletin(writer)
        return writer.HttpResponsePDF(filename = 'boletin')
            
    else:
        raise FatalError("No se han encontrado los argumentos correctos")

