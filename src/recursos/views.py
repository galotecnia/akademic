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
from django.views.generic import list_detail
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse

from recursos.models import *

from docencia.models import OPCIONES_MESES
from docencia.auxFunctions import fechaTemplateSimple
from django.template import RequestContext
from forms import ReservaForm, RecursoForm
from models import *



import time
import datetime
from authority.decorators import permission_required_or_403, permission_required

RANGO_HORAS = ('08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30',
    '19:00', '19:30', '20:00')

@permission_required('recursopermission.acceso_recurso', None)
def index (request):
    context = {}
    context['task'] = 'recursos'
    return render_to_response(
            'recursos/richWebBrowser/index.html', 
            context,
            context_instance=RequestContext(request)
        )

@permission_required('recursopermission.acceso_recurso', None)
def listatipo (request, tipo_recurso = None):
    context = {}
    context['task'] = 'recursos'
    context['TIPOS_DE_RECURSO'] = TIPOS_DE_RECURSO
    return list_detail.object_list (request,
        queryset = Recurso.getDisponibles(tipo_recurso),
        allow_empty = True,
        template_name = 'recursos/richWebBrowser/recursos_list.html',
        extra_context = context)

@permission_required('recursopermission.acceso_recurso', None)
def reservas (request, tipo_recurso = None):
    context = {}
    context['task'] = 'recursos'
    context['TIPOS_DE_RECURSO'] = TIPOS_DE_RECURSO
    return list_detail.object_list (request,
        queryset = Reserva.getReservas(tipo = tipo_recurso, usuarioResponsable = request.user.id),
        template_name = 'recursos/richWebBrowser/reservas.html',
        allow_empty = True,
        extra_context = context)

@permission_required('recursopermission.acceso_recurso', None)
def eliminarReserva (request, reserva_id):
    try:
        reserva = Reserva.objects.get (Q(responsable = request.user) & Q(pk = reserva_id))
    except Reserva.DoesNotExist:
        log.error(u"Intentando eliminar una reserva que no existe")
        return HttpResponseRedirect(reverse("lista_reservas", args=[]))
    if request.POST:
        if request.POST.has_key ('aceptar'):
            reserva.delete ()
        return HttpResponseRedirect(reverse("lista_reservas", args=[]))
    else:
        context = {}
        context['reserva'] = reserva
        context['task'] = 'recursos'
        return render_to_response(
                'recursos/richWebBrowser/confirma-borrado.html', 
                context,
                context_instance=RequestContext(request)
            )

@permission_required('recursopermission.reservar_recurso', None)
def nuevaReserva (request, recurso_id):
    """
        Este método utiliza la infraestructura para el manipulador porque las nuevas
        reservas hay que tratarlas con cuidado a la hora de introducirlas en la base
        de datos.
    """
    #manipulador = Reserva.AddManipulator ()
    
    errors = {}
    if request.POST:
        new_data = request.POST.copy ()
        new_data['responsable'] = request.user.id
        new_data['inicio_date'] = new_data['fechaianyo'] + '-' + new_data['fechaimes'] + '-' + new_data['fechaidia']
        new_data['fin_date'] = new_data['inicio_date']
        new_data['fin'] = new_data['fin_date'] + " " + new_data['fin_time']
        new_data['inicio'] = new_data['inicio_date'] + " " + new_data['inicio_time']
        form = ReservaForm(new_data)
        if form.is_valid():
            if form.cleaned_data['inicio'] > form.cleaned_data['fin']:
                errors['inicio_date'] = ['La fecha de inicio no puede ser mayor que la de fin']
            if form.cleaned_data['inicio'] < datetime.datetime.now():
                errors['fin_date'] = ['La fecha de inicio no puede ser anterior al día de hoy']
            colisiones = Reserva.objects.filter (
                    Q(recurso = new_data['recurso']) & (
                        (
                            Q(inicio__lt = form.cleaned_data['inicio']) & Q(fin__gt = form.cleaned_data['inicio'])
                        )
                            |
                        (
                            Q(inicio__lt = form.cleaned_data['fin']) & Q(fin__gt = form.cleaned_data['fin'])
                        )
                            |
                        (
                            Q(inicio__gt = form.cleaned_data['inicio']) & Q(fin__lt = form.cleaned_data['fin'])
                        )
                    )
                )
            if colisiones:
                errors['colision'] = "Lo sentimos, este recurso se encuentra ya reservado en este espacio de tiempo"
                errors['reservas_previas'] = colisiones
            if not errors:
                form.save()
        else:
            errors = form.errors

    else:
        errors = new_data = {}
        form = ReservaForm()

    context = {}
    fechaTemplateSimple(context, request) # sobra diaActual, mesActual, anyoActual
    context['recurso_id'] = recurso_id
    context['errors'] = errors
    context['form'] = form
    context['reservas'] = Reserva.getReservas (recurso_id)
    context['task'] = 'recursos'
    context['user'] = request.user
    context['diasMes'] = range(1,32)
    context['meses'] = OPCIONES_MESES
    context['anyos'] = range(settings.CURSO_ESCOLAR_ACTUAL, settings.CURSO_ESCOLAR_ACTUAL + 4)
    context['horas'] = RANGO_HORAS 
    if request.GET:
        try:
            context['calendario'] = Reserva.getCalendario(
                    setDictFunction = setDictRecurso,
                    diccionarioAdicional = {'recurso_id' : recurso_id},
                    semana = request.GET['semana']
                )
            context['semanaAnterior'] = int(request.GET['semana']) - 1
            context['semanaSiguiente'] = int(request.GET['semana']) + 1

        except:
            context['calendario'] = Reserva.getCalendario(
                    setDictFunction = setDictRecurso,
                    diccionarioAdicional = {'recurso_id' : recurso_id},
                )

    else:
        context['calendario'] = Reserva.getCalendario(
                    setDictFunction = setDictRecurso,
                    diccionarioAdicional = {'recurso_id' : recurso_id},
                )
        context['semanaAnterior'] = int(time.strftime("%W")) - 1
        context['semanaSiguiente'] = int(time.strftime("%W")) + 1
    return render_to_response (
            'recursos/richWebBrowser/nueva-reserva.html',
            context,
            context_instance=RequestContext(request)
        )

@permission_required('recursopermission.acceso_recurso', None)
def nuevo_recurso(request):
    context = {}
    if request.POST:
        form = RecursoForm(request.POST)
        if form.is_valid():
            item = form.save()
            context['msg'] = "Recurso %s creado con éxito" % item
        else:
            context['form'] = form
    if not 'form' in context:
        form = RecursoForm()
        context['form'] = form
    return render_to_response(
            'recursos/richWebBrowser/nuevo_recurso.html',
            context,
            context_instance = RequestContext(request))
