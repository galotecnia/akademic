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
from models import Calificacion, InformeEvaluacion, CalificacionCompetencia, Competencia, Evaluacion
from docencia.admin import BaseAdmin

class CalificacionCompetenciaAdmin(BaseAdmin):
    
    related_search_fields = {
        'alumno': ('persona__nombre', 'persona__apellidos')
    }
    list_filter = ('evaluacion',)

admin.site.register(CalificacionCompetencia, CalificacionCompetenciaAdmin)

class CalificacionAdmin(BaseAdmin):
    
    related_search_fields = {
        'matricula': ('grupo_aula_alumno__alumno__persona__nombre', 'grupo_aula_alumno__alumno__persona__apellidos', 'asignatura__nombreCorto', 'asignatura__nombreLargo'), 
    }
    list_filter = ('evaluacion',)
    search_fields = ('matricula__grupo_aula_alumno__alumno__persona__nombre', 'matricula__grupo_aula_alumno__alumno__persona__apellidos')

admin.site.register(Calificacion, CalificacionAdmin)

class InformeEvaluacionAdmin(BaseAdmin):
    
    related_search_fields = {
        'alumno': ('persona__nombre', 'persona__apellidos'),
    }

admin.site.register(InformeEvaluacion, InformeEvaluacionAdmin)
admin.site.register(Competencia)
admin.site.register(Evaluacion)
