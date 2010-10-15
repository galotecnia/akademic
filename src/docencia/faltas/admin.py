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

from django.contrib import admin
from models import Parte, EnviosFaltas, Falta, Ausencia
from docencia.admin import BaseAdmin

class ParteAdmin(BaseAdmin):
    list_display = ('profesor', 'asignatura', 'fecha')
    list_filter = ('profesor',)
    search_fields = ('fecha', 'profesor__persona__nombre', 'profesor__persona__apellidos',
        'asignatura__nombreCorto', 'asignatura__nombreLargo')
    related_search_fields = {
        'profesor': ('persona__nombre', 'persona__apellidos'),
        'asignatura': ('nombreCorto', 'nombreLargo'),
    }

admin.site.register(Parte, ParteAdmin)

class EnvioFaltasAdmin(BaseAdmin):
    list_display = ('parte', 'fecha', 'ip', 'user_agent')
    list_filter = ('ip',)
    search_fields = ('fecha', 'ip', 'user_agent', 'parte__profesor__persona__nombre', 'parte__profesor__persona__apellidos',
        'parte__asignatura__nombreCorto', 'parte__asignatura__nombreLargo')
    related_search_fields = {
        'parte': ('profesor__persona__nombre', 'profesor__persona__apellidos', 'asignatura__nombreCorto', 'asignatura__nombreLargo')
    }

admin.site.register(EnviosFaltas, EnvioFaltasAdmin)

class FaltaAdmin(BaseAdmin):
    list_display = ('alumno', 'fecha', 'hora', 'asignatura', 'notificadoSMS', 'tipo')
    list_filter = ('asignatura', 'hora')
    search_fields = ('fecha', 'hora__denominacion', 'alumno__persona__nombre', 'alumno__persona__apellidos',
        'asignatura__nombreCorto', 'asignatura__nombreLargo')
    related_search_fields = {
        'alumno': ('persona__nombre', 'persona__apellidos'),
        'asignatura': ('nombreCorto', 'nombreLargo'),
    }
admin.site.register(Falta, FaltaAdmin)

class AusenciaAdmin(BaseAdmin):
    list_display = ('alumno', 'inicio', 'fin', 'notificadoSMS')
    search_fields = ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion', 'motivo')
    related_search_fields = {
        'alumno': ('persona__nombre', 'persona__apellidos'),
    }

admin.site.register(Ausencia, AusenciaAdmin)
