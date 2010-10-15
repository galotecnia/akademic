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
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import create_update
from django.template import RequestContext
from django.conf import settings
from django.utils.datastructures import SortedDict
from django.views.generic.list_detail import object_list

from docencia.faltas.models import *
from auxFunctions import *

from models import *
from forms import *
from docencia.auxmodels import NOMBRES_LARGOS_DIAS
from docencia.libs.djangoOOGalo import DjangoWriter

from notificacion.models import *
from notificacion.forms import MensajeTextoForm, FiltroNotificacionForm
from notificacion.constants import PADRE_MOVIL_NO_VERIFICADO, PADRE_SIN_MOVIL
from notificacion import enviar_notificacion_a_alumnos

from recursos.models import Reserva
from utils.iCalendar import *
from akademicLog import *

import re
import datetime
import calendar
import time
import operator
import os
import tempfile

from pincel.models import TraductorAlumno

logger = AkademicLog().logger

SESSION_KEY = '_auth_user_id'
LEGACY_USER_KEY = '_auth_legacy_user'
            
TEMPLATES = {'login': "login.html",
             'profesor_mostrar_listados': 'listadosProfesor.html'}

d_faltas = { 'faltas': {'F': FALTA_ASISTENCIA, 'R': RETRASO}, 
            'comportamiento': { 'C': FALTA_COMPORTAMIENTO, 'T': FALTA_TAREA, 'M': FALTA_MATERIAL},
          }

TIPO_F_C = {
    'faltas' :  {
        'task': 'horarioFaltas',
        'task2': 'faltasActual',
        'url': 'faltas',
        'fields': {'falta': 'F', 'ausencia': 'JE', 'retraso': 'R', 'uniforme': 'U'},
        },
    'comportamiento' : {
        'task': 'horarioComportamiento',
        'task2': 'comportamientoActual',
        'url': 'comportamiento',
        'fields': {'comportamiento': 'C', 'tarea': 'T', 'material': 'M'},
        },
    }

class LoginForm(forms.Form):
    usuario = forms.CharField(max_length=200)
    password = forms.CharField(max_length=200, widget=forms.PasswordInput)

def work_in_progress(request):
    response = HttpResponse()
    response.write('<h1 align="center">%s</h1>' % settings.INSTITUTION_NAME)
    response.write('<p></p><p></p>')
    response.write('<p><b>Estamos trabajando en mejorar la aplicación.<br>En breves instantes podrá hacer uso de ella.</b></p>')
    response.write('<p><b>Por favor, disculpen las molestias.</b></p>')
    return response

def gestionMenu (request, menu):
    """
        Actualiza la variable de sesion del breadcrumb para saber por donde vamos
        La variable "a" es necesaria pero estúpida. Tiene que estar ahí para que 
        funcionen correctamente las sesiones.
    """
    if 'menuBreadCrumb' in request.session:
        a = request.session['menuBreadCrumb'][:]
    else:
        a = []

    if menu == "subir":
        if (len(request.session['menuBreadCrumb']) > 1):
            menu = a[-2]
            a.pop()
        elif (len(request.session['menuBreadCrumb']) == 1):
            menu = "principal"
            a.pop()
        else:
            menu = "principal"
    elif menu == "menu":
        if (len(request.session['menuBreadCrumb']) > 0):
            menu = a[-1]
        else:
            menu = "principal"
    else:
        try:
            if a[-1] != menu:
                a.append (menu)
        except IndexError:
                a.append (menu)

    request.session['menuBreadCrumb'] = a
    return render_to_response (
                "akademic/menu/%s.html" % menu,
                None,
                context_instance=RequestContext(request),
            )

def akademicLogout(request): 
    """ 
        Saca al usuario del sistema y muestra la pantalla de login 
    """
    try:
        if request.session[LEGACY_USER_KEY] is not None and len (request.session[LEGACY_USER_KEY]) > 0:
            request.session[SESSION_KEY] = request.session[LEGACY_USER_KEY].pop ()
            return HttpResponseRedirect(reverse("profesor_faltas_actual", args=[]))
    except KeyError:
        pass

    logout (request) 
    return HttpResponseRedirect(reverse("login", args=[]))

def akademicLogin(request):
    """
        Muestra la pantalla de login.
    """
    context = {}
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['usuario'], 
                                password=form.cleaned_data['password'])
            if user:
                # El usuario es válido, lo logeamos en el sistema
                login(request, user)
                if isProfesor(user):               
                    return HttpResponseRedirect(reverse('profesor_faltas_actual', args=[]) )
                if isPadre(user):
                    return HttpResponseRedirect(reverse("padres_root", args=[]))
                if isPas(user):
                    return HttpResponseRedirect(reverse('pas_nueva_cita', args=[]))
                if isOrientador(user) and not (user.is_staff or user.is_superuser):
                    return HttpResponseRedirect(reverse('selecciona_grupo', args=[]))
                if isDirector(user) and not (user.is_staff or user.is_superuser):
                    return HttpResponseRedirect(reverse('informe_partes', args=[]))
                logger.debug("Usuario %s inválido: no tiene perfil asociado", user)
                return HttpResponseRedirect(reverse('listar_incidencias'))
            else:
                context['error'] = "Nombre de usuario y contraseña incorrectos"
    elif request.user.is_authenticated():
        if isProfesor(request.user) is not None:
            return HttpResponseRedirect(reverse('profesor_faltas_actual', args=[]) )
        if isPas(request.user) is not None:            
            return HttpResponseRedirect(reverse('pas_nueva_cita', args=[]) )
        if isPadre (request.user) is not None:
            return HttpResponseRedirect(reverse("padres_root", args=[]))

    form = LoginForm()
    errors = new_data = {}

    context['form'] = form
    return render_to_response(
            'akademic/richWebBrowser/' + TEMPLATES['login'],
            context, 
            context_instance=RequestContext(request)
        )

@profesor_requerido
def profesorIndex(request, profesor, task = 'faltasActual', semana_id = None, task_template = None):
    """
        Devuelve la página principal para un profesor
        dependiendo de su perfil.
        
        * Argumentos:
            => profesor_id: El identificador unívoco del profesor.
            => task: La tarea que se quiere llevar a cabo, puede ser:
            - faltasActual
            - horarioFaltas
            - comportamientoActual
            - horarioComportamiento
            - listaFaltas
            - listaComportamiento
            - notificacionesSms
            ... Y así uno por cada tarea que permitamos hacer.
            => task_template: se refiere al path del fichero que contiene
            el template. Si no se especifica nada (que será lo más común)
            el nombre del fichero será "akademic/<task>.html" Así podemos
            tener distintas "vistas" para un mismo task.
            
    """
    context = {}
    context['nivel'] = getPerfil(request.user)
    if not task:
        task = 'faltasActual'
    if not task_template:
        task_template = "akademic/" + task + ".html"
    context['task_template'] = task_template
    if task == 'faltasActual':
        # Obtenemos la clase en la que está el profesor ahora.
        aux = profesor.getFaltasFecha()
        if not aux or type(aux) == unicode:
            context['error'] = 'No tiene clase a esta hora'
        else:
            context['fechaView'] = aux['fechaView']
            context['fecha'] = aux['fecha']
            context['asignatura'] = aux['claseActual'][0].asignatura
            context['hora'] = aux['claseActual'][0].hora
            context['grupo'] = aux['claseActual'][0].grupo
            context['alumnos'] = aux['alumnos']
    if task == 'horarioFaltas':
        aux = profesor.getHorarioWeb()
        context['horario'] = aux['horario']
        context['horarioweb'] = aux['horarioweb']
        context['horas'] = aux['horas']
        context['semana'] = aux['semana']
        context['dias_semana'] = aux['dias_semana']
    return render_to_response(
            "akademic/profesor-index.html", 
            context,
            context_instance=RequestContext(request),
            )

@login_required
def insertaFalta(request, tipo = 'faltas'):
    """
        Inserta las faltas correspondientes al formulario.
    """
    profesor = checkIsProfesor(request.user)

    if not request.POST:
        return HttpResponseRedirect(reverse("error", args=[]))
    # Obtenemos los datos que necesitamos para hacer las consultas.
    new_data = dict(request.POST)
    try:
        fecha = datetime.datetime.strptime(new_data.pop('fecha')[0], "%Y-%m-%d").date()
        next = new_data.pop('next')[0]
    except KeyError, e:
        logger.error(u'Falta algun campo en la inserccion de faltas: %s' % e)
        return HttpResponseRedirect(reverse("error", args=[])) 
    try:
        asignatura = Asignatura.objects.get(pk = new_data.pop('asignatura')[0])
        hora = Hora.objects.get(pk = new_data.pop('hora')[0]) 
    except KeyError, e:
        logger.error(u'Falta algun campo en la inserccion de faltas: %s' % e)
        return HttpResponseRedirect(reverse('error', args=[]))
    except ValueError, e:
        grupos_id = new_data.pop('hora')[0]
        hora = GrupoAula.objects.filter(id__in = grupos_id.split('_'))
        asignatura = None
    # Registro del envío
    # Comprobar si ya existe un parte previo y si no existe crear uno
    if asignatura:
        fechadt = datetime.datetime(fecha.year, fecha.month, fecha.day, hora.horaInicio.hour, hora.horaInicio.minute)
        now = datetime.datetime.now()
        # Crear un nuevo envío para este parte almacenando la IP, UA, etc.
        try:
            remote = request.META['REMOTE_ADDR']
            user_agent = request.META['HTTP_USER_AGENT']
        except:
            remote = "Testing ..."
            user_agent = "Django test client"
        parte, created = Parte.objects.get_or_create(profesor = profesor, asignatura = asignatura,fecha = fechadt)
        EnviosFaltas( parte = parte, fecha = now, ip = remote, user_agent = user_agent[:255]).save()
    else:
        fechadt = datetime.datetime(fecha.year, fecha.month, fecha.day, hour = 9)
        
    # Obtenemos el diccionario con los datos antiguos
    faltas = {}
    for k,v in d_faltas[tipo].items():
        for i in [str(i.id) for i in profesor.getFaltas(asignatura, fecha, hora, v).distinct()]:
            if i in faltas.keys():
                faltas[i].append(k)
            else:
                faltas[i] = [k]
    # Insertamos todas los datos nuevos
    uniformes_previos = profesor.getUniformes(asignatura, fecha, hora)
    ausentes = uniformes = []
    for indice,v in new_data.items():
        k = indice.split('_')[2]
        alu = Alumno.objects.get(pk = k)
        for value in v:
            if 'JE' == value:
                if not alu.estadoAusencia():
                    alu.setAusencia(True, fechadt)
                ausentes.append(int(k))
            elif 'U' == value:
                if not alu.estadoUniforme():
                    alu.setUniforme(fechadt.date())
                uniformes.append(int(k))
            elif (k not in faltas.keys() or value not in faltas[k]) and 'JE' not in v:
                if asignatura: 
                    Falta(alumno = alu, fecha = fecha, hora = hora, asignatura = asignatura, notificadoSMS = False, tipo = d_faltas[tipo][value]).save()
                else:
                    horas = []
                    for h in Horario.objects.filter(grupo__grupoaulaalumno__alumno = alu, diaSemana = fecha.weekday()+1).exclude(grupo__seccion = "Pendientes"):
                        if h.hora not in horas:
                            Falta(alumno = alu, fecha = fecha, hora = h.hora, asignatura = h.asignatura, notificadoSMS = False, tipo = d_faltas[tipo][value]).save()
                            horas.append(h.hora)

    # Borramos todas las faltas 
    for indice,v in faltas.items():
        alu = Alumno.objects.get(pk = indice)
        k = alu.persona.apellidos + '_' + alu.persona.nombre + '_' + str(alu.id)
        for tipo_falta in v:
            # Si hemos desmarcado todas las faltas del alumno o
            # hemos desmarcado la falta tipo_falta del alumno o
            # hemos activado la casilla JE
            if k not in new_data.keys() or \
               tipo_falta not in new_data[k] or \
               ('JE' in new_data[k] and tipo_falta != 'JE'):
                filter = Q(alumno = alu, fecha = fecha, tipo = d_faltas[tipo][tipo_falta])
                if asignatura:
                    filter = filter & Q(asignatura = asignatura, hora = hora)
                for f in Falta.objects.filter(filter):
                    f.delete()

    # Borramos todas las ausencias que hayan finalizado
    if tipo == 'faltas':
        for i in Ausencia.objects.filter(fin = None):
            if i.alumno.id not in ausentes:
                i.alumno.setAusencia(False)
        for i in uniformes_previos:
            if i.id not in uniformes:
                i.delUniforme(fechadt.date())
                  
    return HttpResponseRedirect(next)

@login_required
def faltas(request, inserta=False, fecha=None, hora_id=None, tipo='faltas'):
    """
        Renderiza la clase que tiene que impartir el profesor en un instante determinado. Si no se indica
        ningún instante de tiempo se obtiene del momento en el que se ejecuta el método. Si no tiene clase
        en dicho instante de tiempo se muestra un mensaje de error.
    """
    rc = RequestContext(request)
    profesor = checkIsProfesor(request.user)
    context = {}
    if fecha:
        actual = False
        task = TIPO_F_C[tipo]['task']
        if hora_id:
            url = TIPO_F_C[tipo]['url'] + '/%s/%s/' % (fecha, hora_id)
            context = profesor.getFaltasFecha(dia=datetime.datetime.strptime(fecha, '%d-%m-%Y'), 
                                         horas=hora_id, tipo=tipo)
        else:
            url = TIPO_F_C[tipo]['url'] + '/%s/' % fecha
            context = profesor.getFaltasFecha(dia=datetime.datetime.strptime(fecha, '%d-%m-%Y'),
                                        tipo=tipo)
    else:
        actual = True
        task = TIPO_F_C[tipo]['task2']
        url = task + '/'
        context = profesor.getFaltasFecha(tipo = tipo)
    
    if not context:
        context = {'error': 'No tiene clase a esta hora'}
    if type (context) == unicode:
        context = {'error': context}
    else:
        f = []
        if tipo == 'faltas':
            choices = (('F',''), ('R',''),('JE',''),('U', ''),)
        else:
            choices = (('C',''), ('T',''),('M','',),)
        grupos_id = ''
        for g in context['grupos']:
            grupos_id += str(g['clase'].id) + '_'
            kwargs = SortedDict()
            i = 1
            for a in g['alumnos']:
                initial = []
                for k,v in TIPO_F_C[tipo]['fields'].items():
                    if a[k]: initial.append(v)
                numero = str(a['alumno'].posicion) if settings.ORDENAR_POR_NUMERO_LISTA else str(i)
                indice = a['alumno'].persona.apellidos + '_' + a['alumno'].persona.nombre + '_' + str(a['alumno'].id)
                lab = numero + '</td><td><span class="nombre">' + a['alumno'].persona.nombre + '</span> <span class="apellido">' + a['alumno'].persona.apellidos + '</span>'
                kwargs[indice] = forms.MultipleChoiceField(label=lab, widget = MyCheckBoxMultiple, choices=choices, initial=initial, required=False)
                totales = a['total']
                setattr(kwargs[indice].widget, 'totales', totales)
                i += 1
            form = DynamicForm()
            form.setFields(kwargs)
            f.append({'form':form, 'grupo':g})
        context['grupos_id'] = grupos_id[0:len(grupos_id)-1]

        if inserta:
            context['aviso'] = "Sus faltas se han almacenado correctamente"
        #context['task'] = task
        context['next'] = settings.SITE_LOCATION + "/akademic/" + url
        context['form'] = f
        context['tipo'] = tipo
        context['dia'] = NOMBRES_LARGOS_DIAS[context['fecha'].weekday()]
        if tipo == 'faltas' and context['hora'] != 'Todo el dia':
            fechadt = datetime.datetime.combine(context['fecha'], context['hora'].horaInicio)
            try:
                context['parte'] = Parte.objects.get(profesor = profesor, asignatura = context['asignatura'], fecha = fechadt)
            except Parte.DoesNotExist:
                context['parte'] = None
    url = 'akademic/richWebBrowser/faltasActual.html' if actual else 'akademic/richWebBrowser/horarioFaltas.html'
    context['colspan'] = 6 if tipo == 'faltas' else 5
    return render_to_response( url, context, rc)

@login_required
def horarioProfesor(request, semana = None, tipo = 'faltas'):
    """
        Devuelve el horario del profesor. El tipo puede ser o bien "faltas" o bien "comportamiento"
    """
    if tipo not in ('faltas', 'comportamiento'):
        raise Http404(u"Tipo de horario desconocido.")
    # FIXME: Utilizar los chequeos de roles nuevos 
    profesor = checkIsProfesor(request.user)
    context = profesor.getHorarioWeb(semana = semana)
    context['task'] = 'horarioFaltas'
    context['tipo'] = tipo
    return render_to_response(
            'akademic/richWebBrowser/horarioFaltas.html', 
            context, context_instance=RequestContext(request)
        )

def getCitasiCalendar(request):
    """
        Vista que permitirá descargar un archivo iCalendar con las citas de un
        profesor
    """
    tutor = checkIsTutor(request.user)
    profesor = tutor.profesor

    citas = ()
    try:
        tutor = Tutor.objects.get(
            profesor = profesor,
            grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL
        )
        tutoria = Tutoria.objects.get(tutor = tutor)
        citas = Cita.objects.filter(
            Q(tutoria = tutoria),
            Q(fecha__gte = datetime.datetime.now())
        ).order_by('fecha')
    except ObjectDoesNotExist:
        pass

    # Construimos la lista de eventos
    eventos = []
    for c in citas:
        e = {}
        e['resumen'] = "Reunirse con %s" % c.alumno 
        fecha = datetime.datetime.combine(c.fecha, c.tutoria.hora)
        e['comienzo'] = fecha
        e['final'] = fecha + DURACION_CITA_POR_DEFECTO
        e['uid'] = c.id
        eventos.append(e)

    ical = events2iCalendar(eventos)

    return HttpResponseCalendar(ical)

@login_required
def listaCitasProfes(request):
    """
        Este método dibujará un horario con las citas planificadas para el
        profesor que ha iniciado la sesión.
    """
    tutor = checkIsTutor(request.user)
    profesor = tutor.profesor
    context = {}

    if request.GET:
        if request.GET.has_key('semana'):
            context['calendario'] = Reserva.getCalendario(
                setDictFunction = setDictCitas,
                diccionarioAdicional = { 'profesor_id': profesor.id },
                semana = request.GET['semana']
            )
            context['semanaAnterior'] = int(request.GET['semana']) - 1
            context['semanaSiguiente'] = int(request.GET['semana']) + 1
        else:
            context['calendario'] = Reserva.getCalendario(
                setDictFunction = setDictCitas,
                diccionarioAdicional = { 'profesor_id': profesor.id },
            )
    else:
        context['calendario'] = Reserva.getCalendario(
            setDictFunction = setDictCitas,
            diccionarioAdicional = { 'profesor_id': profesor.id },
        )
        context['semanaAnterior'] = int(time.strftime("%W")) - 1
        context['semanaSiguiente'] = int(time.strftime("%W")) + 1

    return render_to_response(
            'akademic/richWebBrowser/listaCitas.html',
            context,
            context_instance=RequestContext(request)
        )

@login_required
def detailCitas(request, fecha):
    """
    """
    tutor = checkIsTutor(request.user)
    profesor = tutor.profesor
    context = {}

    try:
        tutoria = Tutoria.objects.get(
            Q(tutor__profesor__id = profesor.id)&
            Q(tutor__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
        )
    except Tutoria.DoesNotExist:
        context['error'] = 'Su usuario no tiene tutorías asignadas'
        return render_to_response("akademic/cita_detail.html", context, context_instance=RequestContext(request))

    f = datetime.datetime.fromordinal(int(fecha));
    diaSiguiente = f + datetime.timedelta(1);

    context['citas'] = Cita.objects.filter(
        Q(tutoria = tutoria),
        Q(fecha__gte = f),
        Q(fecha__lte = diaSiguiente)
    )

    return render_to_response('akademic/richWebBrowser/cita_detail.html', context, context_instance=RequestContext(request))

@login_required
def listasTutorAsignaturas(request):
    """
        Permite a un Tutor, visualizar las faltas que se ha producido en las distintas asignaturas
        que se imparten en su tutoría.
        Para ello primero le pregunta qué tipo de lista desea y de qué mes en concreto.
        Luego podrá seleccionar las asignaturas de las que desea obtener el listado.
        Y finalmente este se genera.
    """
    tutor = checkIsTutor(request.user)

    context = {}
    new_data = None
    context['task'] = "listasTutorAsignaturas"
    fechaTemplateSimple(context, request) # sobra diaActual
    context['tipoListado'] = OPCIONES_LISTADOS
    context['profesor'] = tutor.profesor
    context['listaAsignaturas'] = tutor.getAsignaturasTutoria()

    if request.POST:
        new_data = request.POST.copy()
        context['urlimprimir'] = "fechames=%s&fechanyo=%s&tipoListado=%s" % (
                new_data['fechames'], new_data['fechanyo'], new_data['tipoListado']
            )
        for i in new_data.getlist('asignaturas'):
            context['urlimprimir'] += '&asignaturas=%s' % i
    elif request.GET:
        new_data = request.GET.copy()
        context['fechaImpresion'] = datetime.datetime.now().strftime ('%d/%m/%y %T')

    if new_data is not None:
        # Obtenemos el mes y el anyo, habría que calcular el último día de este
        # mes para hacer las comparaciones
        mes = new_data['fechames']
        anyo = new_data['fechanyo']
        mescal = calendar.monthcalendar(int(anyo), int(mes))
        ultdia = max(mescal[len(mescal) - 1])
        tipoListado = new_data['tipoListado']
        # Obtenemos las asignaturas para las que se ha solicitado listado.
        asignas = Asignatura.objects.filter(pk__in = new_data.getlist('asignaturas'))
        fechaInicio = anyo + '-' + mes + '-01'
        fechaFin =  anyo + '-' + mes + '-' + str(ultdia)
        context['listados'] = tutor.getListados(tipoListado, asignas, fechaInicio, fechaFin)
    if request.GET:
        try:
            if int(new_data['csv']) == 1:
                return listadoCSV(context['listados'])
        except KeyError:
            pass
        return render_to_response( 'akademic/richWebBrowser/printListasTutorAsignaturas.html',
                context, context_instance=RequestContext(request))
    return render_to_response( 'akademic/richWebBrowser/listasTutorAsignaturas.html',
            context, context_instance=RequestContext(request))

@login_required
def listasTutorTotales(request):
    """
        Permite a un tutor visualizar los totales de incidencias de cada tipo que un alumno
        a generado en cada día del mes seleccionado.
    """
    tutor = checkIsTutor(request.user)

    context = {}
    new_data = None

    context['task'] = "listasTutorTotales"
    fechaTemplateSimple(context, request) # sobra mesActual y anyoActual
    context['tipoListado'] = OPCIONES_LISTADOS
    context['profesor'] = tutor.profesor
    #context['listaAsignaturas'] = tutor.getAsignaturasTutoria()
    if request.POST:
        new_data = request.POST.copy()
        context['urlimprimir'] = "fechames=%s&fechanyo=%s&tipoListado=%s" % (
                new_data['fechames'], new_data['fechanyo'], new_data['tipoListado']
            )
        for i in new_data.getlist('asignaturas'):
            context['urlimprimir'] += '&asignaturas=%s' % i
    elif request.GET:
        new_data = request.GET.copy()
        context['fechaImpresion'] = datetime.datetime.now().strftime ('%d/%m/%y %T')

    if new_data is not None:
        # Obtenemos el mes y el anyo, habría que calcular el último día de este
        # mes para hacer las comparaciones
        mes = new_data['fechames']
        anyo = new_data['fechanyo']
        mescal = calendar.monthcalendar(int(anyo), int(mes))
        ultdia = max(mescal[len(mescal) - 1])
        tipoListado = new_data['tipoListado']
        # Obtenemos las asignaturas para las que se ha solicitado listado.
        fechaInicio = anyo + '-' + mes + '-01'
        fechaFin =  anyo + '-' + mes + '-' + str(ultdia)
        context['listados'] = tutor.getListadosTotales(tipoListado, fechaInicio, fechaFin)
    
    if request.GET:
        try:
            if int(new_data['csv']) == 1:
                return listadoCSV(context['listados'])
        except KeyError:
            pass
        return render_to_response(
            'akademic/richWebBrowser/printListasTutorAsignaturas.html',
            context,
            context_instance=RequestContext(request)
        )

    return render_to_response(
        'akademic/richWebBrowser/listasTutorTotales.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def listadosProfesor(request):
    """
        Permite a un profesor ver los listados de faltas de los alumnos de las clases que
        imparte.
    """
    profesor = checkIsProfesor(request.user)

    context = {}
    new_data = None

    context['listaAsignaturas'] = profesor.getAsignaturas()
    context['task'] = 'listadosProfesor'
    fechaTemplateSimple(context, request) # sobra diaActual
    context['tipoListado'] = TIPO_FALTAS
    context['fecha_form'] = FechaMensualAnualForm()
    # Lo comentado es correcto según la doc de django, pero para que
    # funcione hay que mirar algo mas.
    #if request.method is 'POST':
    if request.POST:
        new_data = request.POST.copy()
        context['urlimprimir'] = "fechames=%s&fechanyo=%s&tipoListado=%s" % (
                new_data['fechames'], new_data['fechanyo'], new_data['tipoListado']
        )
        for i in new_data.getlist('asignaturas'):
            context['urlimprimir'] += '&asignaturas=%s' % i
    elif request.GET:
        new_data = request.GET.copy()
        context['fechaImpresion'] = datetime.datetime.now().strftime ('%d/%m/%y %T')

    if new_data is not None:
        # Obtenemos el mes y el anyo, habría que calcular el último día de este
        # mes para hacer las comparaciones
        mes = int(new_data['fechames'])
        anyo = int(new_data['fechanyo'])
        mescal = calendar.monthcalendar(int(anyo), int(mes))
        #ultdia = max(mescal[len(mescal) - 1])
        ultdia = calendar.monthrange(anyo, mes)[1]
        tipoListado = new_data['tipoListado']
        asignas = new_data.getlist('asignaturas')
        # Obtenemos las asignaturas para las que se ha solicitado listado.
        fechaInicio = str(anyo) + '-' + str(mes) + '-01'
        fechaFin =  str(anyo) + '-' + str(mes) + '-' + str(ultdia)
        context['listados'] = profesor.getListados(tipoListado, asignas, fechaInicio, fechaFin)

    if request.GET:
        try:
            if int(new_data['csv']) == 1:
                return listadoCSV (context['listados'])
            return render_to_response(
                    'akademic/richWebBrowser/printListasTutorAsignaturas.html',
                    context,
                    context_instance=RequestContext(request) )
        except KeyError:
            return render_to_response(
                    'akademic/richWebBrowser/printListasTutorAsignaturas.html',
                    context,
                    context_instance=RequestContext(request) )

    return render_to_response(
            'akademic/richWebBrowser/' + TEMPLATES['profesor_mostrar_listados'],
            context, context_instance=RequestContext(request) )
    
def selecciona_tipo_texto_notificacion(post, argumentos, context):
    predefinido = customizado = valor = exito = None
    if post.has_key('textoPredef'):
        #Debemos comprobar si realmente contiene algo, ya que en ciertos navegadores,
        #configuraciones es posible que exista la key, pero no tenga valor.
        if post['textoPredef']:
            predefinido = True
            valor = post['textoPredef']        
        del post['textoPredef']
        
    if post.has_key('textoCustom'):
        if post['textoCustom']:
            customizado = True
            valor = post['textoCustom']
        del post['textoCustom']
    
    if customizado and predefinido:        
        context['error'] = "Por favor, elija sólo un tipo de texto, no ambos a la vez"
        return None
    
    if predefinido:
        try:
            argumentos['texto_notificacion'] = TextoNotificacion.objects.get(pk=valor)
        except TextoNotificacion.DoesNotExist:
            context['error'] = 'Hubo un problema al intentar utilizar el texto predefinido.'
            return None                            
        exito = True
    
    if customizado:
        argumentos['texto_string'] = valor
        exito = True
        
    if exito:
        return True    
    context['error'] = 'Seleccione un texto para la notificación o escriba uno propio'    
    return None

def preparar_contexto_final_notificaciones(alumnos, kwargs, context):
        contador_sms, lista_errores_alumnos = enviar_notificacion_a_alumnos(alumnos, kwargs)
        context['aviso'] = "Se han generado " + str(contador_sms) + " sms"    
        if lista_errores_alumnos:
            context['lista_errores_movil_padres'] = lista_errores_alumnos
            
@tutor_requerido
def envio_notificacion_grupo(request, tutor = None, grupo = None):
    def response(orientador=False):
        template = "envio_notificaciones_sms_grupo_aula.html"
        if orientador:
            template = "envio_notificaciones_sms_orientador.html"
        return render_to_response(
                'akademic/richWebBrowser/' + template,
                context,
                context_instance=RequestContext(request))
    context = {}
    orientador = False
    if grupo:
        try:
            grupo = GrupoAula.objects.get(pk = grupo)
        except GrupoAula.DoesNotExist:
            context['error'] = 'No se eligio un valor, o bien el mismo estaba vacio.'
            return response()
        if grupo.seccion == "Pendientes":
            context['error'] = 'Este grupo no está habilitado para el envío de mensajes.'
            return response()
        breadcrumb = "Orientador >> Notificación sms alumnos"
        orientador = True
    elif tutor:
        breadcrumb = "Tutor >> Notificación sms por grupo"
        grupo = tutor.grupo
    else:
        raise Http404
    lista = Alumno.objects.filter(grupoaulaalumno__grupo=grupo)
    
    args = { 'lista': lista, 
            'legend': 'Por favor, seleccione los alumnos del grupo:' + grupo.__str__(), 'tipo': 'grupo' }
        
    context = { 'task': 'envio_notificacion_grupo',
                'texto_form': MensajeTextoForm(),
                'form': BaseCheckboxForm(**args),
                'no_submit_button': True,
                'no_form_tag': True,
                'predef': TextoNotificacion.objects.filter(generico=True),
                'breadcrumb': breadcrumb }
    
    if 'GET' in request.method:
        return response()
    
    post = request.POST.copy()
    #Quitamos del post lo que no nos interesa y tendremos únicamente una lista de id's
    del post['alumnos']
    del post['tipo']
    profesor = None
    if tutor: profesor = tutor.profesor
    kwargs = { 'profesor': profesor, 
               'estado': ESTADO_NOTIFICACION[0][0] }
    if not selecciona_tipo_texto_notificacion(post, kwargs, context):
            return response()        
    if not post:
        context['error'] = 'No se eligio un valor, o bien el mismo estaba vacio.'
        return response(orientador)
    alumnos = Alumno.filter(id__in=post.keys)
    preparar_contexto_final_notificaciones(alumnos, kwargs, context)
    return response()

@profesor_requerido
def notificacionSmsProfesor(request, profesor):
    """
        Gestión del envío de notificaciones SMS de un profesor cualquiera.
    """
    def response():
        return render_to_response(
            'akademic/richWebBrowser/notificacionSmsProfesor.html',
            context,
            context_instance=RequestContext(request) )
    
    def get_asignatura_grupo_from_post(valor):
                (asignatura_id, grupo_id) = valor.split('@')
                asignatura = Asignatura.objects.get(pk=asignatura_id)
                grupo = GrupoAula.objects.get(pk=grupo_id)
                return asignatura, grupo
            
    context = { 'task': 'notificacionSmsProfesor',               
                'error': None }
    
    if not request.POST:
        context['form'] = AsignaturasForm(profesor=profesor)
        return response()        
    post = request.POST.copy()
    
    if "asignatura" in post['tipo']:
        del post['tipo']
        #Post del form de asignaturas
        listados = []
        for valor in post.keys():
            asignatura, grupo = get_asignatura_grupo_from_post(valor)
            alumnos = grupo.getAlumnosAsignatura(asignatura)            
            leyenda = str(grupo) + ', ' + asignatura.nombreCorto            
            form = AlumnosCheckboxForm(lista_alumnos=alumnos, legend=leyenda)
            listados.append(form)
        if not listados:
            context['error'] = 'No se marcaron asignaturas'
            return response()
            
        context['listado_alumnos_por_grupo'] = listados
        context['no_submit_button'] = True
        context['no_form_tag'] = True
        return response()
    
    if "alumnos" in post['tipo']:
        del post['tipo']
        #Post desde form de alumnos
        alumnos_id = post.keys()
        if not alumnos_id:
            context['error'] = 'No se marcaron alumnos'
            return response()
                
        context['predef'] = TextoNotificacion.objects.filter(generico=True)
        context['alumnos_id'] = ','.join(alumnos_id)        
        context['texto_form'] = MensajeTextoForm()
        context['seleccion_texto'] = True
        return response()
    
    if "envio_mensajes" in post['tipo']:
        del post['tipo']
        #Post desde form de seleccion de mensaje
        argumentos = { 'profesor': profesor, 
                  'estado': ESTADO_NOTIFICACION[0][0] }
        if not selecciona_tipo_texto_notificacion(post, argumentos, context):
            return response()
        
        alumnos = [Alumno.objects.get(pk=alu) for alu in post['alumnos'].split(',') ]        
        preparar_contexto_final_notificaciones(alumnos, argumentos, context)        
        return response()
    
    context['error'] = "Hubo un error al enviar los mensajes"
    return response()

@login_required
def envio_notificaciones_sms_agrupadas(request, urlname=None):
    def response():
        return render_to_response(
                'akademic/richWebBrowser/envio_notificaciones_sms_agrupadas.html',
                context,
                context_instance=RequestContext(request) )
        
    profesor = isProfesor(request.user)
    if not isDirector(request.user) and not isJefeEstudios(profesor):
        raise UnauthorizedAccess("Necesita tener privilegios de Director o Jefe de\
            Estudios para acceder a este recurso")
    privilegio = None
    if isDirector(request.user):
        privilegio = 'director'
        breadcrumb = "Director"
    if isJefeEstudios(profesor) and not privilegio:
        privilegio = 'jefe_estudios'
        jefe = isJefeEstudios(profesor)
        breadcrumb = "Jefe de estudios"
        
    if 'niveles' in urlname:
        lista = Nivel.objects.filter(cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL)                     
        if 'jefe_estudios' in privilegio:
            lista = [jefe.nivel,]
        args = { 'lista': lista, 
            'legend': 'Por favor, seleccione un nivel', 'tipo': 'nivel' }
        breadcrumb += " >> Notificación sms masiva" 
    if 'cursos' in urlname:
        lista = Curso.objects.filter( 
            ciclo__nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL,).order_by('nombre', 'ciclo')
        if 'jefe_estudios' in privilegio:
            lista = lista.filter(ciclo__nivel=jefe.nivel)
        args = { 'lista': lista,
            'legend': 'Por favor, seleccione un curso', 'tipo': 'curso'}
        breadcrumb += " >> Notificación sms por curso"
        
    context = { 'task': 'notificacionSmsMasivo',
                'texto_form': MensajeTextoForm(),
                'form': BaseCheckboxForm(**args),
                'no_submit_button': True,
                'no_form_tag': True,
                'predef': TextoNotificacion.objects.filter(generico=True),
                'breadcrumb': breadcrumb }
    
    if 'GET' in request.method:
        return response()
    
    post = request.POST.copy()
    #Quitamos del post lo que no nos interesa y tendremos únicamente una lista de id's
    del post['alumnos']
    del post['tipo']
    kwargs = { 'profesor': profesor, 
               'estado': ESTADO_NOTIFICACION[0][0] }
    if not selecciona_tipo_texto_notificacion(post, kwargs, context):
            return response()        
    if not post:
        context['error'] = 'No se eligio un valor, o bien el mismo estaba vacio.'
        return response()
   
    # Revisar que los grupos no sean de seccion pendientes
    if 'niveles' in urlname:    
        niveles_str = post.keys()
        niveles = Nivel.objects.filter(cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL, id__in=niveles_str)
        matriculas = Matricula.objects.filter(grupo_aula_alumno__grupo__curso__ciclo__nivel__in=niveles,
            grupo_aula_alumno__grupo__curso__ciclo__nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL) 
        #.exclude(
        # grupo_aula_alumno__grupo__seccion = 'Pendientes')
        alumnos = Alumno.filter(grupoaulaalumno__matricula__in=matriculas).distinct()
    if 'cursos' in urlname:
        cursos_str = post.keys()
        cursos = Curso.objects.filter(id__in=cursos_str)
        matriculas = Matricula.objects.filter(grupo_aula_alumno__grupo__curso__in=cursos,
            grupo_aula_alumno__grupo__curso__ciclo__nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL) 
        #.exclude(
        # grupo_aula_alumno__grupo__seccion = 'Pendientes')
        alumnos = Alumno.filter(grupoaulaalumno__matricula__in=matriculas).distinct()
            
    preparar_contexto_final_notificaciones(alumnos, kwargs, context)
    return response()    
  
@login_required
def posesion (request):
    """
        Este método cambia el usuario de la sesion
    """
    profesor = None
    try:
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor) and not isCoordinador(profesor):
            raise UnauthorizedAccess()
    except UnauthorizedAccess:
        if not isDirector(request.user):
            raise UnauthorizedAccess("Necesita tener privilegios de Director, Jefe de\
                Estudios o Coordinador de ciclo para acceder a este recurso")

    context = {}
    context['task'] = 'poseer'

    if request.POST:
        #profesor = Profesor.objects.get(pk=request.POST['profesor'])
        profesor = get_object_or_404(Profesor, pk=request.POST['profesor'] )
        try:
            user = User.objects.get(personaperfil__profesor=profesor)#.usuario
            try:
                if request.session[LEGACY_USER_KEY] is None:
                    request.session[LEGACY_USER_KEY] = [request.user.id]
                else:
                    request.session[LEGACY_USER_KEY].append (request.user.id)
            except KeyError:
                    request.session[LEGACY_USER_KEY] = [request.user.id]
            request.session[SESSION_KEY] = user.id
            return HttpResponseRedirect(reverse("profesor_faltas_actual", args=[]))
        except User.DoesNotExist:
            context['error'] = "El profesor seleccionado no dispone de usuario en el sistema, contacte con el administrador."
            
    try:
        coordinador = CoordinadorCiclo.objects.filter(profesor = profesor)
        if not coordinador:
            raise CoordinadorCiclo.DoesNotExist
        for j in coordinador:
            # Filtrar todos los profesores del ciclo del cual este profesor 
            # es coordinador
            if j.ciclo == -1:
                busca_ciclo = "UNI"
            else:
                busca_ciclo = j.ciclo
            aux = Horario.objects.filter( 
                            Q(grupo__curso__ciclo = busca_ciclo) &
                            Q(grupo__curso__ciclo__nivel = j.ciclo.nivel)).values('profesor').order_by('profesor').distinct()
            profesores = []
            for i in aux:
                # No tiene sentido que se "posea" a si mismo.
                if i['profesor'] != profesor.id:
                    profesores.append(Profesor.objects.get(pk = i['profesor']))
            context['listaProfesores'] = profesores
    except CoordinadorCiclo.DoesNotExist, AttributeError:
        pass
    try:
        jefe = JefeEstudios.objects.get(profesor = profesor)
        # Filtrar todos los profesores que estan bajo la supervisión del jefe de
        # estudios, que no se que profesores son.
        aux = Horario.objects.filter(grupo__curso__ciclo__nivel = jefe.nivel).values('profesor').order_by('profesor').distinct()
        profesores = []
        for i in aux:
            # No tiene sentido que se "posea" a si mismo.
            if i['profesor'] != profesor.id:
                profesores.append(Profesor.objects.get(pk = i['profesor']))
        context['listaProfesores'] = profesores
    except JefeEstudios.DoesNotExist, AttributeError:
        pass
    # Sólo tomamos los profesores que realmente están impartiendo clases
    # en este momento.
    if isDirector(request.user):
        aux = Horario.objects.all().values('profesor').order_by('profesor').distinct()
        profesores = []
        for i in aux:
            # No tiene sentido que se "posea" a si mismo.
            if not profesor or i['profesor'] != profesor.id:
                profesores.append(Profesor.objects.get(pk = i['profesor']))
        context['listaProfesores'] = profesores
    if not isCoordinador(profesor):
        return render_to_response(
                'akademic/richWebBrowser/poseer.html',
                context,
                context_instance=RequestContext(request)
            )
    else:
        return render_to_response(
                'akademic/richWebBrowser/poseerCoordinadorCiclo.html',
                context,
                context_instance=RequestContext(request)
            )


@login_required
def logPartes(request):
    """
        Muestra una lista de partes enviados
    """
    pass


def _validarNota(nota, salida):
    """
       Valida que una nota sea un entero, y si lo es que sea mayor o igual que cero
       y menor o igual que diez.
       Devuelve none si todo ha ido bien, sino devuelve una cadena para insertarla
       en context['aviso']
       Si la nota es correcta, devuelve en la clave nota del diccionario salida el valor
       si no, rellena ese campo con una cadena vacia.

    """
    msg = ""
    alumno = salida["alumno"]
    try:
        salida['nota'] = int(nota)
        if salida['nota'] > 10:
            msg = ERROR_NOTA_MAYOR % (alumno.nombre, alumno.apellidos)
        elif salida['nota'] < 0:
            msg = ERROR_NOTA_MENOR % (alumno.nombre, alumno.apellidos)
    except ValueError:
        context['aviso'] = ERROR_NOTA_NO_NUMERICA % (alumno.nombre, alumno.apellidos)
    return msg



@login_required
def evaluacionProfesor(request, tutor = False):
    """
        Permite a un profesor ver el listado de asignaturas que se imparte para poder evaluar 
        a sus alumnos.
        Si tutor = false, se trata de un profesor el que hace la consulta y solo puede evaluar
        las asignaturas de las que da clase.
        Si tutor = true, se trata de un tutor y puede visualizar y modificar las listas de su
        tutoria.
    """
    context = {}
    if not tutor:
        profesor = checkIsProfesor(request.user)
        context['listaAsignaturas'] = profesor.getAsignaturas()
        context['task'] = 'evaluacionProfesor'
    else:
        tutor = checkIsTutor(request.user)
        profesor = tutor.profesor
        context['listaAsignaturas'] = tutor.getAsignaturasTutoria()
        context['task'] = 'evaluacionTutor'

    new_data = None
    listaEvaluaciones = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
    if listaEvaluaciones:
        context['listaEvaluaciones'] = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
    else:
        context['error'] = "Aún no se han definido las sesiones de evaluación."
        context['listaEvaluaciones'] = []
    if request.POST:
        new_data = request.POST.copy()
        evaluacion = Evaluacion.objects.get( pk = new_data['evaluacion'])
        context['evaluacion'] = evaluacion
        #context['notasTextuales'] = NOTAS_TEXTUALES
        if new_data.has_key('asignaturas'):
            salida = []
            for i in new_data.getlist('asignaturas'):
                aux = {}
                (asignatura_id, grupo_id) = i.split('@')
                aux['asignatura'] = Asignatura.objects.get(pk = asignatura_id)
                aux['grupo'] = GrupoAula.objects.get(pk = grupo_id)
                listadoAlumnos = aux['grupo'].getAlumnosAsignatura(aux['asignatura'])
                # Una vez tenemos los alumnos habría que ver si ya existe una evaluación previa
                # para cada uno de ellos, es decir, si ya se han pasado sus notas.
                # Si se han pasado, lo lógico sería que apareciera su nota previa y que pudiera
                # modificarse, si no => casilla vacía.
                alumnos = []
                for alumno in listadoAlumnos:
                    diccio = {}
                    diccio['alumno'] = alumno
                    diccio['calificacion'] = alumno.getCalificacionAsignatura(evaluacion, aux['asignatura'])
                    alumnos.append(diccio)
                    
                aux['alumnos'] = alumnos
                salida.append(aux)
                context['listados'] = salida
        else:
            del new_data['evaluacion']
            # Si tiene esta clave tiene el resto tb.
            notas = []
            dirty = False
            for calificacion in new_data.keys():
                diccio = {}
                (alumno, asignatura) = calificacion.split('@')
                diccio['alumno'] = Alumno.objects.get(pk = alumno)
                diccio['asignatura'] = Asignatura.objects.get(pk = asignatura)
                if new_data[calificacion]:
                    msg = _validarNota(new_data[calificacion], diccio)
                    if msg:
                        if context.has_key('aviso'):
                            context['aviso'] += "<br/>" + msg
                        else:
                            context['aviso'] = msg
                        continue
                else:
                    diccio['nota'] = ""

                diccio['alumno'].setCalificacionAsignatura(evaluacion, diccio['asignatura'], diccio['nota'])
                dirty = True
            if context.has_key('aviso') and dirty:
                context['aviso'] += "<br/>Sus calificaciones se han almacenado correctamente."
            elif dirty:
                context['aviso'] = "Sus calificaciones se han almacenado correctamente."

    return render_to_response(
        'akademic/richWebBrowser/evaluacionProfesor.html',
        context,
        context_instance=RequestContext(request)
        )


@login_required
def evaluarCompetencias(request):
    """
       Permite a un tutor evaluar las competencias basicas de
       los alumnos de su tutoria.
    """
    tutor = checkIsTutor(request.user)
    alumnos = tutor.grupo.getAlumnos()
    kwargs = {}
    for a in alumnos:
        kwargs[a.id] = forms.BooleanField(label = a.persona.apellidos + u", " + a.persona.nombre) 
    form = DynamicForm()
    form.setFields(kwargs)

    context = {"form": form, "tutor": tutor}
    return render_to_response(
        'akademic/richWebBrowser/evaluarCompetencias.html',
        context,
        context_instance=RequestContext(request)
    )
    
@login_required
def nuevaEvaluacion(request):
    """
        Gestión de envío de notificaciones SMS a todos los alumnos de un nivel
    """
    if not isDirector(request.user):
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor):
            raise UnauthorizedAccess("Necesita tener privilegios de Director o Jefe de\
                Estudios para acceder a este recurso")

    context = {}
    context['task'] = 'nuevaEvaluacion'
    context['listaEvaluaciones'] = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
    context['cursoEscolarActual'] = settings.CURSO_ESCOLAR_ACTUAL
    return create_update.create_object (
        request,
        Evaluacion,
        template_name = "akademic/nuevaEvaluacion.html",
        post_save_redirect = settings.SITE_LOCATION + "/akademic/nuevaEvaluacion/",
        extra_context = context,
    )

def boletinesGrupoPDF(grupos, formato='pdf'):
    """
        Genera boletines en PDF para cada uno de los grupos seleccionados.
    """
    boletin = DjangoWriter()
    boletin.loadFile(os.path.join (settings.OOTEMPLATES, 'boletin.odt'))
    boletin.copyAll()

    no_promocionan_de_primaria = [1291, 1749, 1277, 1283, 1284, 1339, 1289, 1455, 1346, 1337, 1125]
    no_promocionan_de_secundaria = []
    no_promocionan = no_promocionan_de_primaria + no_promocionan_de_secundaria
    alumnos_no_promocionan = TraductorAlumno.objects.filter(registro__in=no_promocionan).values_list('akademic', flat=True)
    
    cont = 1
    mediaBoletines = 0.0
    for g in grupos:
        alumnos = g.getAlumnos()
        numAlu = len(alumnos)
        tstart = time.time()
        for a in alumnos:
            t1 = time.time()
            boletin.pasteEnd()
            a.generaBoletin(boletin, data=alumnos_no_promocionan)
            boletin.appendPageBreak()
            t2 = time.time()
            mediaBoletines += t2-t1
            logger.info("Boletin %d generado" % cont)
            cont += 1

    tfin = time.time()
    mediaBoletines = mediaBoletines/cont
    if formato == 'odt':
        return boletin.HttpResponseODT(filename = "boletines")
    return boletin.HttpResponsePDF(filename = "boletines")

@login_required
def generarBoletin(request):
    """
       Genera boletines en PDF bajo demanda.
    """
    profesor = checkIsProfesor(request.user)
    context = {}
    filter = Q(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
    url = 'generar_boletines_director.html'
    if not isDirector(request.user):
        url = 'generar_boletines_jefe_estudios.html'
        filter = filter & Q(pk = profesor.jefeestudios_set.get().nivel.id)
        if not isJefeEstudios(profesor):
            raise UnauthorizedAccess("Necesita tener privilegios de Director o Jefe de\
                Estudios para acceder a este recurso")
    if profesor.ver_boletines():
        if not request.POST:
            niveles = Nivel.objects.filter(filter)
            context["niveles"] = niveles
        else:
            new_data = request.POST.copy()
            if new_data.has_key("nivel"):
                nivel = Nivel.objects.filter(pk__in = new_data.getlist("nivel"))
                grupos = GrupoAula.objects.filter(curso__ciclo__nivel__in = nivel).exclude(seccion = "Pendientes").order_by("curso__ciclo__nivel", "curso", "seccion")
                context["grupos"] = grupos
            if new_data.has_key("grupo"):
                grupos_id = new_data.getlist("grupo")
                grupos = GrupoAula.objects.filter(pk__in = grupos_id).exclude(seccion = "Pendientes").order_by("curso__ciclo__nivel", "curso", "seccion")
                if 'odt' in request.GET:
                    return boletinesGrupoPDF(grupos, 'odt')
                return boletinesGrupoPDF(grupos)
    else:
        context['msg'] = "No existen evaluaciones disponibles actualmente."

    return render_to_response(
        'akademic/richWebBrowser/' + url,
        context,
        context_instance=RequestContext(request)
    )

@login_required
def boletinQT(request):
    """
        Vista de prueba, para testear el funcionamiento de webkit
        como backend de generación de pdf.
    """
    grupos = GrupoAula.objects.filter(curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL).exclude(seccion = 
        "Pendientes").order_by("curso__ciclo__nivel", "curso", "seccion")

    boletines = []
    for i in grupos:
        boletines.append(i.getBoletinesAlumnos())

    context = {'boletines': boletines}
    return render_to_response(
        'akademic/richWebBrowser/boletin.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def selecciona_grupo(request):
    context = {}
    d = {str(GRUPO): 'informe_tutor_grupo', str(AREA): 'resumen_evaluacion_tutor_grupo', str(ALUMNO): 'informe_personalizado_grupo'}
    if not isOrientador(request.user):
        context['error'] = _(u"No tiene permiso para acceder a esta sección")
    else:
        if request.POST:
            form = SelectGrupoForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                return HttpResponseRedirect(reverse(d[data['tipo']], args = [data['grupo'].id]))
        else:
            form = SelectGrupoForm()
        context['form'] = form
    context['breadcrumb'] = 'Orientador >> Informes'
    context['legend'] = 'Escoja un grupo y tipo de informe para continuar'
    return render_to_response('akademic/richWebBrowser/selecciona_grupo_orientador.html',
            context,
            context_instance=RequestContext(request)
    )

@login_required
def selecciona_grupo_sms(request):
    context = {}
    if not isOrientador(request.user):
        context['error'] = _(u"No tiene permiso para acceder a esta sección")
    else:
        if request.POST:
            form = GrupoForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                return HttpResponseRedirect(reverse('notificacion_sms_grupo_orientador', args = [data['grupo'].id]))
        else:
            form = GrupoForm()
        context['form'] = form
    context['breadcrumb'] = 'Orientador >> Notificacion sms alumnos'
    context['legend'] = 'Escoja un grupo para continuar'
    return render_to_response('akademic/richWebBrowser/selecciona_grupo_sms_orientador.html',
            context,
            context_instance = RequestContext(request)) 

@login_required
def grupo_informe_je(request):
    context = {}
    je = checkIsJefeEstudios(request.user)
    if request.POST:
        form = GrupoForm(request.POST, nivel = je.nivel)
        if form.is_valid():
            data = form.cleaned_data
            return HttpResponseRedirect(reverse('informe_tutor_grupo', args = [data['grupo'].id]))
        else:
            context['form'] = form
    else:
        context['form'] = GrupoForm(nivel = je.nivel)
    context['breadcrumb'] = 'Jefe de Estudios >> Informe de grupo'
    context['legend'] = 'Escoja un grupo para continuar'
    return render_to_response('akademic/richWebBrowser/selecciona_grupo_jefe_estudios.html',
            context, context_instance = RequestContext(request))

@login_required
def comentario(request):
    """
        Permite enviar comentarios a alumnos de la tutoria del profesor
    """
    tutor = checkIsTutor(request.user)
    profesor = tutor.profesor

    context = {}

    if request.POST:
        alu = request.POST['alu']
        subject = request.POST['subject']
        texto = request.POST['texto']
        if not alu:
            context['error'] = 'Ha de seleccionar un alumno'
        elif not subject:
            context['error'] = 'Ha de escribir un resumen del comentario en el campo <em>Asunto</em>'
        elif not texto:
            context['error'] = 'Ha de escribir texto en el comentario'
        else:
            comm = Comentario()
            comm.alumno = Alumno.objects.get(pk = alu)
            comm.profesor = profesor
            comm.resumen = subject
            comm.texto = texto
            comm.save()
            context['enviado'] = True
            context['aviso'] = 'Comentario enviado satisfactoriamente'
    else:
        alumnos = tutor.grupo.getAlumnos()
        context['alumnos'] = alumnos
    return render_to_response(
        'akademic/richWebBrowser/comentario.html',
        context,
        context_instance=RequestContext(request)
        )


@login_required
def estadoNotificacion(request, page=1):
    """
        Gestión de envío de notificaciones SMS a todos los alumnos por cursos
    """
    try:
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor) and not isCoordinador(profesor):
            raise UnauthorizedAccess()
    except UnauthorizedAccess:
        if not isDirector(request.user):
            raise UnauthorizedAccess("Necesita tener privilegios de Director, Jefe de\
                Estudios o Coordinador de ciclo para acceder a este recurso")
     
    notificaciones = Notificacion.objects.all().order_by("-fechaCreacion")    
    filter = ""
    if request.POST or request.GET:    
        post_data = request.POST.copy() if request.POST else request.GET.copy()
        fechas_form = RangoFechasForm(post_data)
        filtro_form = FiltroNotificacionForm(post_data)
    else:
        fechas_form = RangoFechasForm()
        filtro_form = FiltroNotificacionForm()
    
    if fechas_form.is_valid():
        fecha_inicio = fechas_form.cleaned_data['fechaInicio']
        fecha_final = fechas_form.cleaned_data['fechaFin']
        #NOTE:
        #En el filtro queremos incluir los objectos del mismo día escogido, 
        #por lo que le añadimos un dia de más, ya que un lte no funciona correctamente.
        #Arreglar esto en la fuente del problema implicaría tocar el modelo inicial. 
        #No es algo trivial. Se hace la primera vez nada mas, si se itera por las
        #sucesivas paginas no se incrementa en un dia          
        if not request.GET:
            fecha_final += datetime.timedelta(1)
        filter += "&fechaInicio_day=%s&fechaInicio_month=%s&fechaInicio_year=%s" % (fecha_inicio.day, fecha_inicio.month, fecha_inicio.year)
        filter += "&fechaFin_day=%s&fechaFin_month=%s&fechaFin_year=%s" % (fecha_final.day, fecha_final.month, fecha_final.year)
        notificaciones = notificaciones.filter(fechaCreacion__gte=fecha_inicio,
                                               fechaCreacion__lte=fecha_final)        
    if filtro_form.is_valid():
        #TODO: Incluir en las opciones el filtrar sin tener en cuenta el tipo
        #comprobar si la key en el post es 'tipo' y se iguala a cero
        filtro = filtro_form.cleaned_data['filtro']
        filter += "&filtro=%s" % filtro
        notificaciones = notificaciones.filter(estado=filtro)
    context = { 'action': './',
                'task': 'estadoNotificacion',
                'form': fechas_form,
                'no_submit_button': True,
                'no_form_tag': True,
                'form_legend': "Seleccione un rango de fechas",
                'filtro_form': filtro_form,
                'filter': filter,
            }
    return object_list(request,
        queryset = notificaciones,
        template_name = 'akademic/richWebBrowser/notificacion_list.html',
        paginate_by = NOTIFICACIONES_POR_PAGINA,
        extra_context = context 
    )

@login_required
def reenvioPassword (request):
    """
        Permite buscar a un padre al que se le regenerará su password y
        se le enviará por sms junto a su nombre de usuario.
    """
    checkIsVerificador(request.user)
    context = {}

    if request.POST:
        new_data = request.POST.copy()
        if new_data.has_key('query'):
            search_fields = ['persona__documento_identificacion__icontains', 'persona__nombre__icontains', 'persona__apellidos__icontains']
            allPadres = QuerySet(Padre)
            for bit in new_data['query'].split():
                or_queries = [models.Q(**{field_name: bit}) for field_name in search_fields]
                other_qs = QuerySet(Padre)
                other_qs.dup_select_related(allPadres)
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                allPadres = allPadres & other_qs

            # allPadres = allPadres.filter(id__in = Padre.objects.all().values_list("persona", flat=True))

            context['padres'] = allPadres
            if not len(context['padres']):
                context['notFound'] = True
        elif new_data.has_key('padre'):
            passwd = User.objects.make_random_password(length=6)
            try:
                u = Padre.objects.get(pk = new_data['padre'])
            except Padre.DoesNotExist:
                return render_to_response(
                        "akademic/error.html",
                        context,
                        context_instance=RequestContext(request)
                    )
            u.persona.user.set_password(passwd)
            u.persona.user.save()
            u.persona.save()
            texto = u"Nombre de usuario: %s  Contraseña: %s" % (u.persona.user.username, passwd)
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
            'akademic/richWebBrowser/reenvioPassword.html',
            context,
            context_instance=RequestContext(request)
        )

def informeNagios(request):
    """
        Devuelve el número de notificaciones pendientes de enviar en akademic
        en una vista sencilla para facilitar la monitorización desde NAGIOS.
    """

    if request.META['REMOTE_ADDR'] == settings.MONITORING_TOOL_IP:
        numNotificacion = Notificacion.objects.filter(
                        estado = ESTADO_NOTIFICACION[0][0],
                        fechaEnvio__isnull = True
                        ).count()
        return HttpResponse(numNotificacion)
    else:
        return HttpResponseForbidden()

@login_required
def special_days_list(request):
    context = {}
    url = "dias_especiales_list_director.html"
    filter = Q()
    try:
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor):
            if isCoordinador(profesor):
                url = "dias_especiales_list_coordinador.html"
            else:
                raise UnauthorizedAccess()
        filter = Q(grupo__in = profesor.get_grupos())
    except UnauthorizedAccess:
        if not isDirector(request.user):
            raise UnauthorizedAccess("Necesita tener privilegios de Director, Jefe de\
                Estudios o Coordinador de ciclo para acceder a este recurso")
    form_list = []
    for dia in DiaEspecial.objects.filter(filter).distinct():
        aux = {'form': DiaEspecialForm(instance = dia), 'dia_id': dia.id}
        form_list.append(aux)
  
    context['form_list'] = form_list 
    return render_to_response (
        'akademic/richWebBrowser/' + url,
        context,
        context_instance = RequestContext(request))

@login_required
def del_special_day(request, dia_id = None):
    try:
        dia = DiaEspecial.objects.get(pk = dia_id)
        msg = "El dia especial %s ha sido eliminado." % dia
        dia.delete()
    except DiaEspecial.DoesNotExist:
        msg = "No existe el día especial indicado."
    return HttpResponseRedirect(reverse('lista_dias_especiales', args = []))    

@login_required
def gestion_dias_especiales(request):
    
    context = {}
    url = "dias_especiales_director.html"
    try:
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor):
            if isCoordinador(profesor):
                url = "dias_especiales_coordinador.html"
            else:
                raise UnauthorizedAccess()
    except UnauthorizedAccess:
        if not isDirector(request.user):
            raise UnauthorizedAccess("Necesita tener privilegios de Director, Jefe de\
                Estudios o Coordinador de ciclo para acceder a este recurso")

    if request.POST:
        form = SpecialDaysForm(request.POST, user = request.user)
        if form.is_valid():
            data = form.cleaned_data
            if 'create' in request.POST:
                dia = data['day']
                motivo = data['motivo']
                changes = 0
                for k in request.POST.keys():
                    if k.startswith('res_'):
                        [eti, ids] = k.split('_', 1)
                        for id in ids.split('_'):
                            changes += DiaEspecial.create(dia, motivo, id, request.POST.getlist(k))
                        break
                context['cambios'] = changes
                form = SpecialDaysForm(user = request.user)
            else:
                context['form_list'] = [ResponsablesForm(grupo = data['grupo'])] 
        context['form'] = form
    else:
        form = SpecialDaysForm(user = request.user)
        context['form'] = form

    return render_to_response(
            'akademic/richWebBrowser/' + url,
            context, 
            context_instance=RequestContext(request))

@login_required
def attach_file(request):
    context = {}
    profesor = checkIsProfesor(request.user)
    send_form = True
    if request.POST:
        form = FileAttachForm(request.POST, request.FILES, profesor = profesor)
        if form.is_valid():
            item = form.save()
            context['msg'] = 'El archivo ha sido subido con éxito'
        else:
            send_form = False
            context['form'] = form
    if send_form:
        form = FileAttachForm(profesor = profesor)
        context['form'] = form
        
    return render_to_response('akademic/richWebBrowser/files.html', context, context_instance=RequestContext(request))
     
