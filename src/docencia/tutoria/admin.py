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

from models import Tutor, Tutoria, Cita
from docencia.admin import BaseAdmin

class TutorAdmin(BaseAdmin):
    list_display = ('profesor', 'grupo')
    related_search_fields = {
        'profesor': ('persona__nombre', 'persona__apellidos'),
    }

admin.site.register(Tutor, TutorAdmin)

class TutoriaAdmin(BaseAdmin):
    list_display = ('tutor', 'hora', 'diaSemana', 'maxCitas')
    search_fields = ('tutor__profesor__persona__nombre', 'tutor__profesor__persona__apellidos',)
    related_search_fields = {
        'tutor': ('profesor__persona__nombre', 'profesor__persona__apellidos'),
    }

admin.site.register(Tutoria, TutoriaAdmin)

class CitaAdmin(BaseAdmin):
    list_display = ('tutoria', 'fecha', 'alumno', 'padre', 'madre', 'avisadoSMS', 'avisadoEMAIL')
    search_fields = ('tutoria__tutor__profesor__persona__nombre', 'tutoria__tutor__profesor__persona__apellidos',
        'alumno__nombre', 'alumno__apellido')
    date_hierarchy = 'fecha'
    related_search_fields = {
        'tutoria': ('tutor__profesor__persona__nombre', 'tutor__profesor__persona__apellidos'),
        'alumno': ('persona__nombre', 'persona__apellidos'),
    }

admin.site.register(Cita, CitaAdmin)
