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
from django.http import HttpResponseRedirect #, Http404
from django.views.generic import create_update, list_detail
from django.template import RequestContext
from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse

from docencia.auxFunctions import checkIsVerificador
from docencia.tutoria.models import Tutor
from padres.models import Padre
from docencia.models import GrupoAula
from notificacion.models import Notificacion
import logging

import re, datetime, calendar, time

SESSION_KEY = '_auth_user_id'
LEGACY_USER_KEY = '_auth_legacy_user'

def verificados(request):
    return direct_to_template(request, template = 'akademic/richWebBrowser/verificados.html')

def desdoble(request):
    return direct_to_template(request, template = 'akademic/richWebBrowser/desdoble.html')

def seleccionaCurso(request):

    checkIsVerificador(request.user)
    context = {'object_list': GrupoAula.objects.filter(curso__ciclo__nivel__cursoEscolar = 
        settings.CURSO_ESCOLAR_ACTUAL).exclude(seccion = "Pendientes")}
    return direct_to_template(request, template = 'akademic/grupoaula_list.html', extra_context = context)

def verificaCurso(request, grupo_id):

    def restituye(padre):
        if padre.persona.user:
            u = padre.persona.user
            padre.persona.user = None
            padre.persona.save()
            u.delete()
        padre.verificado = None 
        padre.save()
        
    checkIsVerificador(request.user)
    datos = []
    grupo = GrupoAula.objects.get(pk = grupo_id)
    # for alumno in tutor.grupo.getAlumnos():
    for alumno in grupo.getAlumnos():
        aux = {'alumno': alumno}
        aux['padres'] = []
        if alumno.padre: aux['padres'].append(alumno.padre)
        if alumno.madre: aux['padres'].append(alumno.madre)
        datos.append(aux)
    if request.method == "GET":
        context = {'datos': datos}
        return render_to_response("akademic/verificacion.html", context, context_instance=RequestContext(request))
    else:
        verificados = request.POST.getlist('verificado')
        blancos = request.POST.getlist('is_blanco')
        for data in datos:
            for padre in data['padres']:
                if u"%s" % padre.id in blancos:
                    padre.is_blanco = True
                    restituye(padre)
                else:
                    if u"%s" % padre.id in verificados:
                        if not padre.verificado:
                            padre.verificado = datetime.datetime.now()
                            padre.save()
                            # Creamos o actualizamos el usuario
                            passwd = padre.generate_user()
                            msg = u"Estimado %s, su nombre de usuario es %s y su clave es %s" % (padre, padre.persona.user.username, passwd)
                            try:
                                Notificacion.envia_notificacion(padre, data['alumno'], msg, confidencial=True)
                            except RuntimeError, e:
                                # warn("Esto es una equivocación. El padre %s no tiene teléfono" % padre)
                                restituye(padre)
                    else:
                        padre.is_blanco = False
                        restituye(padre)
        return HttpResponseRedirect(reverse('verificados', args = []))
