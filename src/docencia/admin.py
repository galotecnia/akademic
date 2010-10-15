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
from models import *
from pincel.models import *
import operator
from django.db import models
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
from django.conf.urls.defaults import patterns
from widgets import ForeignKeySearchInput

admin.site.register(TraductorAlumno)
admin.site.register(TraductorPadre)
admin.site.register(TipoVia)
admin.site.register(Municipio)
admin.site.register(Isla)
admin.site.register(Provincia)
admin.site.register(Profesion)
admin.site.register(EstudiosPadre)
admin.site.register(Pais)
admin.site.register(Autorizacion)
admin.site.register(Clasificacion)
admin.site.register(TipoEspacio)
admin.site.register(TipoConstruccion)
admin.site.register(TipoUso)
admin.site.register(Ubicacion)
admin.site.register(Concierto)
admin.site.register(Minusvalia)
admin.site.register(EstadoCivil)
admin.site.register(Centro)

class BaseAdmin(admin.ModelAdmin):

    related_search_fields = {}
    
    def __call__(self, request, url):
        if url is None:
            pass
        elif url == 'search':
            return self.search(request)
        return super(BaseAdmin, self).__call__(request, url)

    def get_urls(self):
        urls = super(BaseAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^search/$', self.search)
        )
        return my_urls + urls

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if isinstance(db_field, models.ForeignKey) and \
                db_field.name in self.related_search_fields:
            kwargs['widget'] = ForeignKeySearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
        return super(BaseAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def search(self, request):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)

        if search_fields and app_label and model_name and query:
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name

            model = models.get_model(app_label, model_name)
            qs = model._default_manager.all()
            for bit in query.split():
                or_queries = [models.Q(**{construct_search(
                    smart_str(field_name)): smart_str(bit)})
                        for field_name in search_fields.split(',')]
                other_qs = QuerySet(model)
                other_qs.dup_select_related(qs)
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs
                data = ''.join([u'%s|%s\n' % (f.__unicode__(), f.pk) for f in qs])
            
            return HttpResponse(data)
        return HttpResponseNotFound()

class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombreLargo', 'nombreCorto', 'abreviatura', 'metaAsignatura')
    list_filter = ('metaAsignatura',)
    search_fields = ('nombreLargo', 'nombreCorto')

admin.site.register(Asignatura, AsignaturaAdmin)

class AlumnoAdmin(BaseAdmin):

    list_display = ('__unicode__', 'cial', 'padre', 'potestadPadre', 'madre', 'potestadMadre') 
    related_search_fields = {
        'padre': ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion'),
        'madre': ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion'),
        'persona': ('nombre', 'apellidos', 'documento_identificacion'), 
    }
    search_fields = ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion')

admin.site.register(Alumno, AlumnoAdmin)

class GrupoAulaAdmin(admin.ModelAdmin):
    list_display = ('curso', 'seccion')
    list_filter = ('seccion', 'curso')

admin.site.register(GrupoAula, GrupoAulaAdmin)

class ProfesorAdmin(BaseAdmin):
    search_fields = ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion')
    related_search_fields = {
        'persona': ('nombre', 'apellidos', 'documento_identificacion'),
    }
    search_fields = ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion')

admin.site.register(Profesor, ProfesorAdmin)

class MatriculaAdmin(BaseAdmin):
    search_fields = ('alumno__persona__nombre', 'alumno__persona__apellidos', 'alumno__persona__documento_identificacion')
    list_display = ('grupo_aula_alumno', 'asignatura', 'tipo')
    list_filter = ('tipo',)

    related_search_fields = {
        'grupo_aula_alumno': ('alumno__persona__nombre', 'alumno__persona__apellidos', 'grupo'),
        'asignatura': ('nombreCorto', 'nombreLargo'),
    }

admin.site.register(Matricula, MatriculaAdmin)

class GrupoAulaAluAdmin(BaseAdmin):

    list_display = ('alumno', 'grupo')
    related_search_fields = {
        'alumno': ('persona__nombre', 'persona__apellidos', ),
    }
    search_fields = ('alumno__persona__nombre', 'alumno__persona__apellidos')

admin.site.register(GrupoAulaAlumno, GrupoAulaAluAdmin)

class NivelAdmin(admin.ModelAdmin):

    list_display = ('nombre', 'cursoEscolar', )
    list_filter = ('cursoEscolar', )

admin.site.register(Nivel, NivelAdmin)

class CoordinadorAdmin(BaseAdmin):

    related_search_fields = {
        'profesor': ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion'),
    }
    search_fields = ('profesor__persona__nombre', 'profesor__persona__apellidos', 'profesor__persona__documento_identificacion')

admin.site.register(CoordinadorCiclo, CoordinadorAdmin)

class JefeEstudiosAdmin(BaseAdmin):

    list_display = ('profesor', 'nivel')

    related_search_fields = {
        'profesor': ('persona__nombre', 'persona__apellidos', 'persona__documento_identificacion'),
    }
    search_fields = ('profesor__persona__nombre', 'profesor__persona__apellidos', 'profesor__persona__documento_identificacion')

admin.site.register(JefeEstudios, JefeEstudiosAdmin)

admin.site.register(Curso)

class CicloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel',)
    list_filter = ('nivel',)

admin.site.register(Ciclo, CicloAdmin)

class DiaEspecialAdmin(admin.ModelAdmin):
    list_filter = ('grupo', 'dia', )
    
admin.site.register(DiaEspecial, DiaEspecialAdmin)
