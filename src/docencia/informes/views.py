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

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse

from docencia.auxFunctions import getFechaRange, checkIsTutor, checkIsProfesor
from docencia.auxFunctions import  isDirector, isJefeEstudios, isOrientador
from docencia.auxFunctions import CSVResumenEvaluacion, checkIsJefeEstudios
from docencia.forms import RangoFechasForm
from docencia.models import Profesor, Alumno
from docencia.notas.models import Evaluacion
from docencia.notas.forms import EvaluacionForm
from docencia.tutoria.models import Tutor
from docencia.customExceptions import UnauthorizedAccess

from docencia.libs.djangoOOGalo import DjangoWriter

from akademicLog import *

import datetime
import time
import os

logger = AkademicLog().logger

def _limite_semana(fecha):
    """
        Devuelve las fechas correspondientes al lunes y domingo de la semana 
        seleccionada.
    """
    if not fecha:
        dia = datetime.datetime.now()
    else:
        dia = datetime.datetime.strptime(fecha, "%d-%m-%Y")
    lunes = dia - datetime.timedelta(days = dia.weekday())
    domingo = lunes + datetime.timedelta(days = 6)
    return lunes, domingo
        
@login_required
def resumen_tutor(request):
    """
        Devuelve un selector de fecha y una vez seleccionada la fecha
        un resumen de todos los eventos en las distintas
        asignaturas de la tutoría del usuario.
    """
    tutor = checkIsTutor(request.user)
    context = {}

    form = RangoFechasForm()
    if request.POST:
        form = RangoFechasForm(request.POST)
        if form.is_valid():
            fechaini = form.cleaned_data['fechaInicio']
            fechafin = form.cleaned_data['fechaFin']
            context['resumen'] = tutor.getResumenTutor(fechaini, fechafin)

    context['form'] = form
    return render_to_response(
            'akademic/richWebBrowser/resumenTutor.html',
            context,
            context_instance=RequestContext(request)
        )


@login_required
def informe_partes (request):
    """
        Informe de los partes que han enviado los profesores.
    """

    url = 'informe_parte_director.html'
    try:
        profesor = checkIsProfesor(request.user)
        if not isJefeEstudios(profesor):
            raise UnauthorizedAccess()
        url = 'informe_parte_jefeestudios.html'
    except UnauthorizedAccess:
        if not isDirector(request.user):
            raise UnauthorizedAccess("Necesita tener privilegios de Director o Jefe de\
                Estudios para acceder a este recurso")
    form = RangoFechasForm()
    fechaInicio = fechaFin = None
    if request.POST:
        form = RangoFechasForm(request.POST)
        if form.is_valid():
            fechaInicio = form.cleaned_data['fechaInicio']
            fechaFin = form.cleaned_data['fechaFin']

    # En la primera impresión de la vista, sin seleccionar
    # una fecha mostramos el rango desde hace un mes hasta la actualidad.
    if not fechaInicio and not fechaFin:
        fechaInicio, fechaFin = getFechaRange()

    context = {}
    context['fechaInicio'] = fechaInicio
    context['fechaFin'] = fechaFin

    informe = []
    for p in Profesor.objects.all().order_by('persona__apellidos', 'persona__nombre'):
        # FIXME: Esto no tiene en cuenta los días festivos, nosotros tampoco, pero los tenemos que
        # tener en el futuro.
        profe = {}
        total, partes, porcentaje = p.getInformePartes(fechaInicio, fechaFin)
        if total:
            profe['profesor'] = p
            profe['horas'] = total
            profe['partes'] = partes
            profe['porcentaje'] = porcentaje
            informe.append (profe)

    context['informe'] = informe

    context['form'] = form

    return render_to_response(
            'akademic/richWebBrowser/' + url,
            context,
            context_instance=RequestContext(request)
        )

@login_required
def informe_tutor(request, grupo = None):
    """
        Devuelve un selector de fecha y una vez seleccionada la fecha
        un informe detallado de todos los eventos producidos en las distintas
        asignaturas de la tutoría del usuario.
    """
    profesor = None
    if isOrientador(request.user) and grupo:
        tutor = Tutor.objects.get(grupo = grupo)
    else:
        profesor = checkIsProfesor(request.user)
        if isJefeEstudios(profesor):
            tutor = Tutor.objects.get(grupo = grupo)
        else:
            tutor = checkIsTutor(request.user)
    context = {}

    form = RangoFechasForm()
    if request.POST:
        form = RangoFechasForm(request.POST)
        if form.is_valid():
            fechaInicio = form.cleaned_data['fechaInicio']
            fechaFin = form.cleaned_data['fechaFin']
            context['resumen'] = tutor.getInformeTutor(fechaInicio, fechaFin)

    context['form'] = form
    url = "informeTutor.html"
    if profesor and isJefeEstudios(profesor):
        url = "informeJefeEstudios.html"
    elif grupo:
        url = "informeOrientador.html"
    return render_to_response(
            'akademic/richWebBrowser/' + url,
            context,
            context_instance=RequestContext(request)
        )

def _informePersonalizadoGrupo(context):
    """
       Genera un pdf con el informe personalizado de un Grupo de alumnos.
    """

    def limpia_tablas(writer, tablas):
        for t in tablas:
            writer.tableDeleteRow(t, 1)
   
    informe = DjangoWriter()
    informe.blank()
    informe.appendFile((os.path.join(settings.OOTEMPLATES, 'incidencias.odt')))
    informe.copyAll()
    info = {'tarea': {'lista': [], 'ind': 'totalTarea'},
            'comportamiento': {'lista': [], 'ind': 'totalComportamiento'},
            'material': {'lista': [], 'ind': 'totalMaterial'},
           }
    page = 1
    delete_tables = []
    for alu in context['informe']:
        fila = 3 
        info['tarea']['lista'] = []
        info['comportamiento']['lista'] = []
        info['material']['lista'] = []
        informe.pasteEnd()
        i = alu['informePersonal']
        for a in alu['informePersonal']['asignaturas']:
            asigna = u'%s' % a['asignatura']
            for k in info:
                for f in a[k]:
                    info[k]['lista'].append((asigna, '%s'%f.fecha.strftime('%d-%m-%Y'), '1'))
        logger.debug("Se intenta coger la tabla Table%d", (10*page-10+fila))
        tabla = u"Table3"
        if tabla in informe.getTables():
            tabla_name = u"Table%d"
        else:
            tabla_name = u"Tabla%d"
        informe.tableWriteInRow(tabla_name % (10*page-10+fila), 1, 'Total acumulado asistencia', str(i['totalFaltas']))
        fila += 1
        informe.tableWriteInRow(tabla_name % (10*page-10+fila), 1, 'Total acumulado retrasos', str(i['totalRetrasos']))
        fila += 1
        for k in info:
            initial = True
            table = tabla_name % (10*page-10+fila)
            fila += 1
            for asig, fecha, total in info[k]['lista']:
                if initial:
                    informe.tableWriteInRow(table, 1, asig, fecha, total)
                    initial = False
                else:
                    informe.tableAddRow(table, asig, fecha, total)
            if initial:
                delete_tables.append(table)
            informe.tableWriteInRow(tabla_name % (10*page-10+fila), 1, 'Total acumulado %s' % k, str(i[info[k]['ind']]))
            fila += 1
        grupo = context['curso']
        informe.searchAndReplacePage(None, '$$Tutor$$', u'%s' % context['profesor'].persona)
        informe.searchAndReplacePage(None, '$$Nombre$$', u'%s' %alu['alumno'].persona)
        informe.searchAndReplacePage(None, '$$Fecha1$$', context['fechaInicio'].strftime('%d de %B de %Y'))
        informe.searchAndReplacePage(None, '$$Fecha2$$', context['fechaFin'].strftime('%d de %B de %Y'))
        informe.searchAndReplacePage(None, '$$Curso$$', u'%s %s %s' % (grupo.curso.nombre, grupo.curso.ciclo.nivel.nombre, grupo.seccion))
        if page > 1: informe.appendPageBreak()
        page += 1
    limpia_tablas(informe, delete_tables)
    return informe

@login_required
def informe_personalizado(request, grupo = None):
    """
        Devuelve el listado de todos los alumnos de la tutoría y un
        formulario con un intervalo de fechas para generar los informes
        personalizados.
    """
    if isOrientador(request.user) and grupo:
        tutor = Tutor.objects.get(grupo = grupo)
    else:
        tutor = checkIsTutor(request.user)
    context = {}

    form = RangoFechasForm()


    if request.POST:
        new_data = request.POST.copy()
        form = RangoFechasForm(request.POST)
        if form.is_valid():
            fechaInicio = form.cleaned_data['fechaInicio']
            fechaFin = form.cleaned_data['fechaFin']
            context['fechaInicio'] = fechaInicio
            context['fechaFin'] = fechaFin
            context['curso'] = tutor.grupo
            informe = []
            for alu in Alumno.filter(pk__in = new_data.getlist('seleccion')):
                aux = {}
                aux['alumno'] = alu
                aux['informePersonal'] = alu.getResumenTutor(fechaInicio, fechaFin, False)
                informe.append(aux)                
            context['informe'] = informe
            if informe and 'pdfSubmit' in new_data:
                context['profesor'] = tutor.profesor
                informe = _informePersonalizadoGrupo(context)
                return informe.HttpResponsePDF(filename="informes")
                

    # Esto se pasa en el contexto para indicar que hay más de un formulario en la vista.
    context['noform'] = True
    context['profesor'] = tutor.profesor
    context['grupo'] = tutor.grupo
    context['alumnos'] = tutor.grupo.getAlumnos()
    context['form'] = form
    
    url = "listaAlumnosTutoria.html"
    if grupo:
        url = "listaAlumnosOrientador.html" 
    return render_to_response(
            'akademic/richWebBrowser/' + url,
            context,
            context_instance=RequestContext(request)
        )
        
@login_required
def resumenEvaluacionProfesor(request, tipo = 'Profesor', grupo = None):
    """
        Devuelve los totales de asistencia, retrasos, comportamiento, tarea y
        material en las asignaturas y grupos que ha seleccionado el profesor
        de entre las que él mismo imparte, para facilitar la evaluación
    """
    context = {}
    if tipo == 'Profesor':
        profesor = checkIsProfesor(request.user)
        context['listaAsignaturas'] = profesor.getAsignaturas()
    else:
        if isOrientador(request.user) and grupo:
            tutor = Tutor.objects.get(grupo = grupo)
        else:
            tutor = checkIsTutor(request.user)
        context['listaAsignaturas'] = tutor.getAsignaturasTutoria()
    form = RangoFechasForm()
    d = request.POST or request.GET
    if d:
        form = RangoFechasForm(d)
        asignas = d.getlist('asignaturas')
        if form.is_valid():
            fechaInicio = form.cleaned_data['fechaInicio']
            fechaFin = form.cleaned_data['fechaFin']
            context['fechaInicio'] = fechaInicio
            context['fechaFin'] = fechaFin
            context['urlimprimir'] = "fechaInicio_year=%s&fechaInicio_month=%s&fechaInicio_day=%s&" % (
            fechaInicio.year, fechaInicio.month, fechaInicio.day)
            context['urlimprimir'] += "fechaFin_year=%s&fechaFin_month=%s&fechaFin_day=%s" % (
            fechaFin.year, fechaFin.month, fechaFin.day)
            for i in asignas:
                context['urlimprimir'] += '&asignaturas=%s' % i
            if tipo == 'Profesor':
                context['listados'] = profesor.getResumenEvaluacion(asignas, fechaInicio, fechaFin)
            else:
                context['listados'] = tutor.profesor.getResumenEvaluacion(asignas, fechaInicio, fechaFin)
        context['fechaImpresion'] = datetime.datetime.now()

    context['form'] = form
    context['noform'] = True

    if request.GET:
        if request.GET.has_key('csv'):
            return CSVResumenEvaluacion (context['listados'])
        return render_to_response('akademic/richWebBrowser/printResumenEvaluacionProfesor.html',
                context, context_instance=RequestContext(request))
    url = "resumenEvaluacion%s.html"
    if grupo:
        url = "resumenEvaluacionOrientador%s.html"
    return render_to_response('akademic/richWebBrowser/' + url % tipo,
            context, context_instance=RequestContext(request))

@login_required
def informe_absentismo(request):
    """
        Devuelve una plantilla xls con el informe de absentismo 
        por cada grupo asociado al jefe de estudios
    """
    rc = RequestContext(request)
    context = {}
    jefe_estudios = checkIsJefeEstudios(request.user)
    if request.POST:
        form = EvaluacionForm(request.POST)
        if form.is_valid():
            ev = form.cleaned_data['evaluacion']
            xls = jefe_estudios.get_xls_absentismo(ev)
            response = HttpResponse(mimetype='application/mx-excel')
            response['Content-Disposition'] = 'attachment; filename=informe_absentismo.xls'
            xls.save(response)
            return response
    else:
        form = EvaluacionForm()
    context['form'] = form
    return render_to_response('akademic/richWebBrowser/informeAbsentismo.html', 
        context, rc)
