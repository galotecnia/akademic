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
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from docencia.libs.djangoOOGalo import DjangoWriter

from models import *
from padres.models import Padre
from pas.models import Pas
from models import Ciclo
from dateFunctions import *
from customExceptions import UnauthorizedAccess

from tutoria.models import Tutor, Tutoria, Cita

import datetime
import csv
import logging
import os

from pincel.models import TraductorAlumno

logger = logging.getLogger('galotecnia')

def getFechaRange():
    """
       Devuelve una fecha de inicio que coincide que es el día anterior menos un mes y
       una fecha de fin que es el día de hoy.
    """
    today = datetime.date.today()
    delta = datetime.timedelta(days=today.day)
    diff = today - delta
    previous_month = datetime.date(year=diff.year, month=diff.month, day=today.day)
    return (previous_month, today)

def fechaTemplate(context, fdia=None, fmes=None, fanyo=None, idia=None, imes=None, ianyo=None):
    context['diasMes'] = range(1,32)
    context['meses'] = OPCIONES_MESES
    context['anyos'] = range(settings.CURSO_ESCOLAR_ACTUAL - 2, settings.CURSO_ESCOLAR_ACTUAL + 3)
    if not fmes or not fanyo:
        # no nos pasan nada completo, fecha actual
        fechaActual = datetime.datetime.now()
    else:
        # fecha que nos pasan
        if not fdia: fdia = 1

        fechaActual = normalizarFecha(fanyo, fmes, fdia)

    context['diaActual'] = int (fechaActual.strftime("%d"))
    context['mesActual'] = fechaActual.strftime("%m")
    context['anyoActual'] = int (fechaActual.strftime("%Y"))
    if imes is None or ianyo is None:
        # no nos pasan nada completo, restamos un mes
        # FIXME: si now = 1 de marzo de 2008, inicio = 29 de enero
        fechaInicio = fechaActual - datetime.timedelta(31,0,0)
    else:
        # fecha que nos pasan
        if idia is None: idia = 1

        fechaInicio = normalizarFecha(ianyo, imes, idia)
    context['diaInicio'] = int (fechaInicio.strftime("%d"))
    context['mesInicio'] = fechaInicio.strftime("%m")
    context['anyoInicio'] = int (fechaInicio.strftime("%Y"))

def fechaTemplateRange(context, request):
    if request.POST:
        # esta funcion (hash, key) da int(hash[key]) si key esta en hash, y None si no esta
        f = lambda h, k: (k in h) and int(h[k]) or None
        x = request.POST
        idia = f(x, 'fechaidia')
        imes = f(x, 'fechaimes')
        ianyo = f(x, 'fechaianyo')
        fdia = f(x, 'fechafdia')
        fmes = f(x, 'fechafmes')
        fanyo = f(x, 'fechafanyo')
        fechaTemplate(context, fdia, fmes, fanyo, idia, imes, ianyo)
    else:
        fechaTemplate(context)

def fechaTemplateSimple(context, request):
    if request.POST:
        # esta funcion (hash, key) da int(hash[key]) si key esta en hash, y None si no esta
        f = lambda h, k: (k in h) and int(h[k]) or None
        x = request.POST
        fdia = f(x, 'fechadia')
        fmes = f(x, 'fechames')
        fanyo = f(x, 'fechanyo')
        fechaTemplate(context, fdia, fmes, fanyo)
    else:
        fechaTemplate(context)

def getPerfil(user):
    """
        Devuelve el perfil para un usuario dado en forma de un diccionario.
        {'tipo': 'profesor'|'error', 'nivel': [['profesor'], ['jefe estudios'], ....]}
    """
    result = {}
    niveles = []
    profesor = isProfesor(user)
    if (profesor):
        result['profesor'] = profesor
        niveles.append('profesor')
        if (isTutor(profesor)):
            niveles.append('tutor')
        if (isCoordinador(profesor)):
            niveles.append('coordinador ciclo')
        if (isJefeEstudios(profesor)):
            niveles.append('jefe estudios')
        if (isVerificador(user)):
            niveles.append('verificador')
    if (isDirector(user)):
        niveles.append('director')
    if (isOrientador(user)):
        niveles.append('orientador')
    if not profesor and (user.is_staff or user.is_superuser):
        niveles = []
    if (isPas(user)):
        niveles.append('pas')
    result['nivel'] = niveles
    return result

def isPas(user):
    # TODO: Controlar esto mejor
    try:
        profile = user.get_profile()
    except PersonaPerfil.DoesNotExist:
        return None
    try:
        return profile.pas
    except Pas.DoesNotExist:
        return None

def isProfesor(user):
    # TODO: Controlar esto mejor
    try:
        profile = user.get_profile()
    except PersonaPerfil.DoesNotExist:
        return None
    except AttributeError:
        return None
    try:
        return profile.profesor
    except Profesor.DoesNotExist:
        return None

def isPadre(user):
    # 20090910: Se ha añadido la posibilidad de pasar una persona como argumento
    # TODO: Controlar esto mejor
    try:
        profile = user.get_profile()
    except PersonaPerfil.DoesNotExist:
        return None
    except AttributeError:    # user es una persona no un user
        try:
            profile = user.personaperfil
        except PersonaPerfil.DoesNotExist:
            return None

    try:
        return profile.padre
    except Padre.DoesNotExist:
        return None

def checkIsProfesor(user):
    """
        Comprobamos si el usuario que se nos pasa como argumento es un
        UsuarioProfesor. Este método lanzará una excepción que será capturada en
        el middleware.
    """
    err_msg = 'Necesita tener privilegios de profesor para acceder a este recurso'
    prof = isProfesor(user)
    if (not prof):
        raise UnauthorizedAccess(err_msg)
    return prof

def isTutor(profesor):
    try:
        return Tutor.objects.get(
            profesor = profesor,
            grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL
        )
    except Tutor.DoesNotExist:
        return None
    except Tutor.MultipleObjectsReturned:
        return Tutor.objects.filter(profesor = profesor, grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)[0]

def checkIsTutor(user):
    """
        Comprobamos si el usuario que se nos pasa como argumento es un
        Tutor. Este método lanzará una excepción que será capturada en
        el middleware.
    """
    err_msg = 'Necesita tener privilegios de tutor para acceder a este recurso'
    try:
        profesor = checkIsProfesor(user)
    except UnauthorizedAccess:
        raise UnauthorizedAccess(err_msg)
    tut = isTutor(profesor)
    if (not tut):
        raise UnauthorizedAccess(err_msg)
    return tut

#TODO: Buscar la manera de sacar factor común de estos decoradores.
def tutor_requerido(function=None):
    """
        Comprueba que el usuario logeado sea tutor, y lo devuelve 
        como parámetro a la función decorada.
    """
    def _decorar(funcion_base):
        def _comprobacion_base(request, *args, **kwargs):
            tutor = None
            profesor = isProfesor(request.user)
            if profesor:
                tutor = isTutor(profesor)
            return funcion_base(request, tutor, *args, **kwargs)
        
        _comprobacion_base.__name__ = funcion_base.__name__
        _comprobacion_base.__dict__ = funcion_base.__dict__
        _comprobacion_base.__doc__  = funcion_base.__doc__
        
        return _comprobacion_base
    
    if function:
        return _decorar(function)
    else:
        return _decorar
    
def profesor_requerido(function=None):
    """
        Comprueba que el usuario logeado sea profesor, y lo devuelve 
        como parámetro a la función decorada.
    """
    def _decorar(funcion_base):
        def _comprobacion_base(request, *args, **kwargs):
            profesor = checkIsProfesor(request.user)
            return funcion_base(request, profesor)
        
        _comprobacion_base.__name__ = funcion_base.__name__
        _comprobacion_base.__dict__ = funcion_base.__dict__
        _comprobacion_base.__doc__  = funcion_base.__doc__
        
        return _comprobacion_base
    
    if function:
        return _decorar(function)
    else:
        return _decorar

def isCoordinador(profesor):
    # Esto es un hack cochino. Documentalo bien por si esto lo vamos a vender
    try:
        return CoordinadorCiclo.objects.filter(
            profesor=profesor,
            ciclo__nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL)
    except CoordinadorCiclo.DoesNotExist:
        return None

def checkIsCoordinador(user):
    """
        Comprobamos si el usuario que se nos pasa como argumento es un
        CoordinadorCiclo. Este método lanzará una excepción que será capturada en
        el middleware.
    """
    err_msg = 'Necesita tener privilegios de coordinador de ciclo para acceder a este recurso'
    try:
        profesor = checkIsProfesor(user)
    except UnauthorizedAccess:
        raise UnauthorizedAccess(err_msg)
    cc = isCoordinador(profesor)
    if (not cc):
        raise UnauthorizedAccess(err_msg)
    return cc

def isJefeEstudios(profesor):
    try:
        return JefeEstudios.objects.get(
            profesor=profesor, nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL)
    except JefeEstudios.DoesNotExist:
        return None

def checkIsJefeEstudios(user):
    """
        Comprobamos si el usuario que se nos pasa como argumento es un
        JefeEstudios. Este método lanzará una excepción que será capturada en
        el middleware.
    """
    err_msg = 'Necesita tener privilegios de jefe de estudios para acceder a este recurso'
    try:
        profesor = checkIsProfesor(user)
    except UnauthorizedAccess:
        raise UnauthorizedAccess(err_msg)
    je = isJefeEstudios(profesor)
    if (not je):
        raise UnauthorizedAccess(err_msg)
    return je

def isDirector(user):
    return user.has_perm('addressbook.is_director')

def checkIsDirector(user):
    """
        Comprobamos si el usuario que se nos pasa como argumento es un
        Director. Este método lanzará una excepción que será capturada en
        el middleware.
    """
    err_msg = 'Necesita tener privilegios de director para acceder a este recurso'
    if not user.has_perm('addressbook.is_director'):
        raise UnauthorizedAccess(err_msg)
    return user

def isOrientador(user):
    return user.has_perm('addressbook.is_orientador')

def checkIsOrientador(user):
    err_msg = 'Necesita tener privilegios de orientador para acceder a este recurso'
    if not user.has_perm('addressbook.is_orientador'):
        raise UnauthorizedAccess(err_msg)
    return user

def isVerificador(user):
    return user.has_perm('addressbook.is_verificador')
    # return user.id == settings.VERIFICADOR

def checkIsVerificador(user):
    err_msg = 'Necesita tener privilegios para verificar datos'
    if not isVerificador(user):
        raise UnauthorizedAccess(err_msg)

def setDictCitas(fecha, diccionario):
    """
        Clasifica la fecha según si se puede pedir cita o no...
    """
    try:
        tutoria = Tutoria.objects.get(
            Q(tutor__profesor__id = diccionario['profesor_id']),
            Q(tutor__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
        )
    except Tutoria.DoesNotExist:
        return ({'texto': " ", 'class': 'vacio'})
    except:
        return ({'texto': "Error", 'class': 'error'})

    if (tutoria.diaSemana-1 != fecha.weekday() or
        tutoria.hora.hour != fecha.hour):
        # Si no existe tutoría a esa hora
        return ({'texto': " ", 'class': 'vacio'})

    # Si llegamos hasta aquí exista la tutoría. Hay que comprobar si tiene citas.
    citas = Cita.objects.filter(tutoria = tutoria, fecha = fecha)
    if len(citas) == 0:
        return ({'texto': "Libre", 'class': 'libre'})
    else:
        cont = 0
        for i in citas:
            cont += 1
        return ({'texto': cont, 'class': 'ocupado', 'a': fecha.toordinal()})

def listadoCSV (listado):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=listado.csv'

    writer = csv.writer(response)
    for asigna in listado:
        for alu in asigna['alumnos']:
            fila = []
            fila.append(alu['alumno'].persona.nombre.encode('utf-8') + " " + alu['alumno'].persona.apellidos.encode('utf-8'))
            for dia in alu['faltas']:
                if dia is not None and dia != 0:
                    if type (dia) == str:
                        fila.append (1)
                    else:
                        fila.append (dia)
                else:
                    fila.append (0)
            fila.append (alu['total'])
            writer.writerow (fila)
    return response

def CSVResumenEvaluacion (listado):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=listado.csv'

    writer = csv.writer(response)
    for asigna in listado:
        for alu in asigna['faltas']:
            fila = []
            fila.append(alu['alumno'].persona.nombre.encode('utf-8') + " " + alu['alumno'].persona.apellidos.encode('utf-8'))
            fila.append (alu['totalAsistencia'])
            fila.append (alu['totalRetrasos'])
            fila.append (alu['totalComportamiento'])
            fila.append (alu['totalTarea'])
            fila.append (alu['totalMaterial'])
            writer.writerow (fila)
    return response

def error(request):
    context = {}
    return render_to_response(
            'akademic/error.html',
            context,
            context_instance=RequestContext(request)
        )

def getCiclosJornadaContinua():
    ciclos = []
    for c in settings.CICLOS_JORNADA_CONTINUA:
        try:
            nivel = get_object_or_404(Nivel, nombre = c['nivel'], cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
            ciclos.append(get_object_or_404(Ciclo, nombre = c['ciclo'], nivel = nivel))
        except Http404, e:
            pass
    return ciclos

def genera_boletines(directory, odt = False, dry_run = False, pdc = False, niveles = [], curso = []):
    """
        Genera todos los boletines para los niveles pasados como argumento
    """
    filter = {'curso__ciclo__nivel__cursoEscolar': settings.CURSO_ESCOLAR_ACTUAL}
    
    #no_promocionan_de_primaria = [1291, 1749, 1277, 1283, 1284, 1339, 1289, 1455, 1346, 1337, 1125]
    #no_promocionan_de_secundaria = [6, 17, 18, 22, 29, 31, 40, 46, 47, 55, 78, 87, 111, 116, 119, 124, 125, 130, 133, 135, 137, 141, 
    #   142, 143, 152, 153, 171, 174, 178, 179, 185, 186, 187, 188, 191, 201, 202, 203, 204, 220, 244, 252, 254, 270, 301, 308, 340, 668, 
    #   678, 684, 687, 689, 690, 693, 697, 699, 700, 708, 712, 714, 715, 717, 719, 720, 725, 782, 808, 841, 849, 851, 854, 864, 867, 871, 
    #   874, 875, 876, 878, 881, 883, 886, 887, 893, 894, 898, 902, 914, 1020, 1036, 1037, 1038, 1041, 1045, 1047, 1053, 1061, 1062, 1069, 1073, 
    #   1074, 1078, 1088, 1090, 1095, 1110, 1114, 1381, 1382, 1560, 1567, 1647, 1654, 1747, 1753, 1760, 1852, 1857, 1871, 1952, 1958, 1961, 
    #   1962, 1966, 1969, 1970, 1973, 1974, 1975]
    #no_promocionan = no_promocionan_de_primaria + no_promocionan_de_secundaria
    #alumnos_no_promocionan = TraductorAlumno.objects.filter(registro__in=no_promocionan).values_list('akademic', flat=True)
   
    exclude_sections = ['Pendientes']
    if not pdc:
        exclude_sections.append('PDC')
    exclude = {'seccion__in': exclude_sections}
    if niveles:
        filter['curso__ciclo__nivel__nombre__in'] = niveles.split(',')
    if curso:
        filter['curso__nombre__in'] = curso.split(',')
    for g in GrupoAula.objects.filter(**filter).exclude(**exclude):
        if not dry_run:
            boletin = DjangoWriter()
            boletin.loadFile(os.path.join (settings.OOTEMPLATES, 'boletin.odt'))
            boletin.copyAll()
        alumnos = 0
        for a in g.getAlumnos():
            if not dry_run:
                boletin.pasteEnd()
                a.generaBoletin(boletin)
                boletin.appendPageBreak()
            alumnos += 1
        logger.info("Boletin del grupo %s generado para %d alumnos.", g.__unicode__(), alumnos)

        name = "%s." % g.display_boletin()
        name += 'odt' if odt else 'pdf'
        full_name = os.path.join(directory, name) 
        if not dry_run:
            logger.info("Guardando el fichero en %s" % full_name)
            boletin.saveODT(full_name) if odt else boletin.savePDF(full_name)
            boletin.close()

