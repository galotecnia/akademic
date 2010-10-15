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
from django.contrib.auth.decorators import login_required
from akademic2.incidencias.models import *
from django.core.mail import send_mail
from django.conf import settings
from django.template import RequestContext
from django.contrib.comments.models import Comment
from forms import UpdateIncidenciaForm, CommentForm, IncidenciaForm

@login_required
def index (request):
    context = {}
    context['task'] = 'incidencias'
    return render_to_response(
            'incidencias/richWebBrowser/index.html',
            context,
            context_instance=RequestContext(request)
        )

@login_required
def lista (request, tipo_incidencia = '0', estado = ''):
    query = Incidencia.objects.all().order_by('-fecha')
    context = {}
    context['task'] = 'incidencias'
    context['nombre'] = 'a ver..'
    if tipo_incidencia != '0':
        query = query.filter(tipoIncidencia = tipo_incidencia)
        context['nombre'] = 'tipo incidencia..'
        context['tipo_incidencia'] = tipo_incidencia
    if estado:
        query = query.filter(estado = estado)
        context['nombre'] = 'estado incidencia..'

    return list_detail.object_list (
        request,
        template_name = 'incidencias/richWebBrowser/listas.html',
        queryset = query,
        extra_context = context,
        allow_empty = True,
        )

@login_required
def detalles (request, incidencia_id):
    context = {}
    context['task'] = 'incidencias'
    i = Incidencia.objects.get(pk = incidencia_id)
    context['object'] = i
    rc = RequestContext(request)
    if request.POST:
        form = UpdateIncidenciaForm(request.POST)
        if form.is_valid():
            i.estado = form.cleaned_data['estado']
            i.prioridad = form.cleaned_data['prioridad']
            i.tipoIncidencia = form.cleaned_data['tipoIncidencia']
            i.save()
            cform = CommentForm(request.POST)
            if cform.is_valid():
                text = cform.cleaned_data['comment']
                if text:
                    cform.save(request, i)
                    # Preparamos el email del comentario
                    de = settings.DE
                    para = settings.PARA + [i.informador.email]
                    asunto = settings.ASUNTO
                    foward = u' %s ' % i.descripcionCorta
                    send_mail(
                        asunto % foward,
                        "Usuario: " + request.user.username + "\nTexto:" + text,
                        de,
                        para,
                        fail_silently=False
                    )
            return lista(request)
        else:
            context['form'] = form
            context['commentform'] = cform
    else:
        context['form'] = UpdateIncidenciaForm(i.__dict__)
        context['commentform'] = CommentForm()
    return render_to_response('incidencias/richWebBrowser/detalles.html', context, rc)

@login_required
def nueva (request):
    context = {}
    context['task'] = 'incidencias'
    rc = RequestContext(request)
    if request.POST:
        form = IncidenciaForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return lista(request)
        else:
            context['form'] = form
    else:
        context['form'] = IncidenciaForm()
    return render_to_response('incidencias/richWebBrowser/nueva.html', context, rc)

@login_required
def nuevoComentario(request):
    """
        Añade un comentario a una incidencia
    """
    return lista(request)

