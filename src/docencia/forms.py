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
from django.forms.widgets import SelectMultiple, CheckboxInput, Select 
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput
from django.forms.extras.widgets import SelectDateWidget
from django.forms.util import ValidationError
from django.utils.dates import MONTHS
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings

from itertools import chain
from django.forms.widgets import CheckboxInput 

from auxFunctions import getFechaRange, checkIsProfesor, isDirector, isJefeEstudios, isCoordinador
from customExceptions import UnauthorizedAccess

from notificacion.constants import *

import datetime
import re
from constants import *
from models import GrupoAula, Nivel, Ciclo, Profesor, JefeEstudios, CoordinadorCiclo, DiaEspecial, FileAttach

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')
FILE_EXT = ['jpeg', 'jpg', 'doc', 'xdoc', 'odt', 'pdf']

from auxmodels import OPCIONES_MESES
    
def get_today():
    return datetime.date.today()

def choices_anuales():
    rango = range(settings.CURSO_ESCOLAR_ACTUAL - 2, settings.CURSO_ESCOLAR_ACTUAL + 3)
    salida = []
    for item in rango:
        salida.append((item, item) )
    return salida

class DynamicForm(forms.Form):
    """
       Formulario dinamico
    """
    def setFields(self, kwds):
        """
           Set the fields in the form.
        """
        keys = kwds.keys()
        #keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

    def setData(self, kwds):
        """
           Set the data to include in the form
        """
        keys = kwds.keys()
        #keys.sort()
        for k in keys:
            self.data[k] = kwds[k]
        self.is_bound = True
    
    def print_fields(self):
        for key, field in self.fields.iteritems():
            k =  str(key) + ": " + str(field)
    
    def validate(self, post):
        """
        Validate the contents of the form
        """
        for name,field in self.fields.items():
            try:
                field.clean(post[name])
            except ValidationError, e:
                self.errors[name] = e.messages
                
class AsignaturasForm(DynamicForm):
    tipo = forms.CharField(initial='asignaturas', required=True, 
                           show_hidden_initial=False, widget=forms.HiddenInput)
    legend = 'Seleccione al menos una asignatura'
    
    def __init__(self, *args, **kwargs):
        try:
            profesor = kwargs['profesor']
            del kwargs['profesor']
        except KeyError:
            pass
        
        super(DynamicForm, self).__init__(*args, **kwargs)
        if profesor:
            self.set_asignaturas_de_profesor(profesor)
            
    def set_asignaturas_de_profesor(self, profesor):
        kwargs = {}
        for tupla in profesor.getAsignaturas():            
            label = unicode(tupla['asignatura']) + ' - ' + unicode(tupla['grupo'])
            key = str(tupla['asignatura'].id) + '@' + str(tupla['grupo'].id)
            self.fields[key] = forms.BooleanField(label=label)
            
class AlumnosCheckboxForm(DynamicForm):
    tipo = forms.CharField(initial='alumnos', required=True, 
                           show_hidden_initial=False, widget=forms.HiddenInput)
    legend = 'Seleccione al menos un alumno'
    
    def __init__(self, *args, **kwargs):
        if kwargs.has_key('lista_alumnos'):
            lista_alumnos = kwargs['lista_alumnos']            
            del kwargs['lista_alumnos']
        
        if kwargs.has_key('legend'):
            self.legend = kwargs['legend']
            del kwargs['legend']
        
        super(DynamicForm, self).__init__(*args, **kwargs)        
        if lista_alumnos:
            self.set_alumnos_from_lista_alumnos(lista_alumnos)    
            
    def set_alumnos_from_lista_alumnos(self, lista_alumnos):
        kwargs = {}
        for alumno in lista_alumnos.order_by('persona__apellidos', 'persona__nombre'):
            label = '<span class="nombre">' +  alumno.persona.nombre + '</span> <span class="apellido">' + alumno.persona.apellidos + '</span>'
            key = alumno.id
            self.fields[key] = forms.BooleanField(label=label)
            
class BaseCheckboxForm(DynamicForm):
    tipo = forms.CharField(initial='base', required=True, 
                           show_hidden_initial=False, 
                           widget=forms.HiddenInput)
    legend = 'base'
    lista = None
    def __init__(self, *args, **kwargs):
        nuevo_tipo = None
        if kwargs.has_key('lista'):
            self.lista = kwargs['lista']            
            del kwargs['lista']        
        if kwargs.has_key('legend'):
            self.legend = kwargs['legend']
            del kwargs['legend']            
        if kwargs.has_key('tipo'):
            #form.fields['tipo'].initial = kwargs['tipo']
            #self.tipo.initial = kwargs['tipo']
            nuevo_tipo = kwargs['tipo']
            del kwargs['tipo']
        
        super(DynamicForm, self).__init__(*args, **kwargs)
        
        if nuevo_tipo:
            self.fields['tipo'].initial = nuevo_tipo                
        if self.lista:
            self.set_fields_from_lista(self.lista)
            
    def set_fields_from_lista(self, lista):
        for item in lista:
            try:
                label = '<span class="nombre">' + item.persona.nombre + '</span> <span class="apellido">' + item.persona.apellidos + '</span>'
            except AttributeError:
                label = str(item)
            key = item.id
            self.fields[key] = forms.BooleanField(label=label)
            
class LoginForm(forms.Form):
    usuario = forms.CharField(max_length=200)
    password = forms.CharField(max_length=200, widget=forms.PasswordInput)

class MyCheckBoxMultiple(SelectMultiple):
    '''
        
    '''
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = []
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)  
            # Obtenemos el HTML del widget
            rendered_cb = cb.render(name, option_value)
            if str_values.intersection([u'JE']) and option_value != 'JE':
                # Calculamos la subcadena antes del cierre del tag (' >')
                n = len(rendered_cb) - 3
                # Añadimos disabled al tag
                rendered_cb = rendered_cb[:n] + " disabled" + rendered_cb[n:]

            # totales es una lista de enteros con el resumen de las faltas del día
            if len(self.totales) > i:
                cad = u'<td>%s(%d)</td>' % (rendered_cb, self.totales[i])
            else:
                cad = u'<td>%s</td>' % rendered_cb

            output.append(cad)
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)

class FechaMensualAnualForm(forms.Form):
    mes = forms.ChoiceField(choices=OPCIONES_MESES)
    anyo = forms.ChoiceField(choices=choices_anuales())

class SelectFechaWidget(SelectDateWidget):
    def render(self, name, value, attrs=None):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, basestring):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        local_attrs = self.build_attrs(id=self.month_field % id_)


        day_choices = [(i, i) for i in range(1, 32)]
        if not (self.required and value):
            day_choices.insert(0, self.none_value)
        local_attrs['id'] = self.day_field % id_
        s = Select(choices=day_choices)
        select_html = s.render(self.day_field % name, day_val, local_attrs)
        output.append(select_html)

        month_choices = MONTHS.items()
        if not (self.required and value):
            month_choices.append(self.none_value)
        month_choices.sort()
        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        year_choices = [(i, i) for i in self.years]
        if not (self.required and value):
            year_choices.insert(0, self.none_value)
        local_attrs['id'] = self.year_field % id_
        s = Select(choices=year_choices)
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

class RangoFechasForm(forms.Form):
    """
        Representa un formulario con rango de fechas.
        Fecha de inicio y fecha de fin.
    """
    previous_month, today = getFechaRange()
    years = range(today.year -2, today.year + 2)
    fechaInicio = forms.DateField(widget=SelectFechaWidget(years=years), 
                                  initial=previous_month.strftime("%Y-%m-%d"),
                                  label="Fecha inicial" )
    fechaFin = forms.DateField(widget=SelectFechaWidget(years=years), 
                               initial=today.strftime("%Y-%m-%d"),
                               label="Fecha final" )

    def clean(self):
        data = self.cleaned_data
        if 'fechaFin' in data and 'fechaInicio' in data and data['fechaFin'] < data['fechaInicio']:
            raise forms.ValidationError("La fecha inicial no puede ser mayor que la final")
        return data

class GrupoForm(forms.Form):
    
    grupo = forms.ModelChoiceField(queryset = GrupoAula.objects.filter(tutor__isnull = False).exclude(seccion = "Pendientes"), empty_label = None)

    def __init__(self, *args, **kwargs):
        nivel = None
        if 'nivel' in kwargs:
            nivel = kwargs['nivel']
            del kwargs['nivel']
        super(forms.Form, self).__init__(*args, **kwargs)
        if nivel:
            self.fields['grupo'].queryset = GrupoAula.objects.filter(tutor__isnull = False, curso__ciclo__nivel = nivel).exclude(seccion = "Pendientes")

class SelectGrupoForm(GrupoForm):
   
    tipo = forms.ChoiceField(choices = OPCIONES_ORIENTADOR) 

class SpecialDaysForm(forms.Form):
    
    day = forms.DateField(widget=SelectFechaWidget(years = range(get_today().year, get_today().year + 1)),
                    initial = get_today(), label = u"Día especial", required = True)
    motivo = forms.CharField(label = u"Motivo", max_length = 20, required = True)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs['user']
        del kwargs['user']
        super(forms.Form, self).__init__(*args, **kwargs)
        if not isDirector(self.user):
            try:
                profesor = checkIsProfesor(self.user)
                if isJefeEstudios(profesor):
                    nivel = profesor.jefeestudios_set.all()[0].nivel
                    self.fields['grupo'] = forms.ModelMultipleChoiceField(queryset = GrupoAula.objects.filter(curso__ciclo__nivel = nivel).exclude(seccion = "Pendientes"))
                elif isCoordinador(profesor):
                    ciclo = profesor.coordinadorciclo_set.all()[0].ciclo
                    self.fields['grupo'] = forms.ModelMultipleChoiceField(queryset = GrupoAula.objects.filter(curso__ciclo = ciclo).exclude(seccion = "Pendientes"))
                else:
                    raise UnauthorizedAccess() 
            except UnauthorizedAccess:
                return
        else:
            self.fields['grupo'] = forms.ModelMultipleChoiceField(queryset = GrupoAula.objects.all().exclude(seccion = "Pendientes"))

class ResponsablesForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        self.grupo = kwargs['grupo']
        del kwargs['grupo']
        super(forms.Form, self).__init__(*args, **kwargs)
        id_list = []
        key = 'res_'
        for grupo in self.grupo:
            id_list += [h.profesor.id for h in grupo.horario_set.all() if h.profesor.id not in id_list]
            id_list += [c.profesor.id for c in CoordinadorCiclo.objects.filter(ciclo = grupo.curso.ciclo) if c.profesor.id not in id_list]
            id_list += [j.profesor.id for j in JefeEstudios.objects.filter(nivel = grupo.curso.ciclo.nivel) if j.profesor.id not in id_list]
            key += str(grupo.id) + '_'
        key = key[:len(key)-1]
        self.fields[key] = forms.ModelMultipleChoiceField(label = "Responsables",
            queryset = Profesor.objects.filter(id__in = id_list))
        
class DiaEspecialForm(forms.ModelForm):
    
    class Meta:
        model = DiaEspecial
        exclude = ['id', ]
    
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['grupo'] = forms.ModelMultipleChoiceField(queryset = self.instance.grupo.all()) 
        self.fields['responsables'] = forms.ModelMultipleChoiceField(queryset = self.instance.responsables.all())     
   
class FileAttachForm(forms.ModelForm):

    class Meta:
        model = FileAttach
        exclude = ['id', 'visto']

    def __init__(self, *args, **kwargs):
        self.profesor = kwargs['profesor']
        del kwargs['profesor']
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields['alumno'] = forms.ModelChoiceField(queryset = self.profesor.get_alumnos())

    def clean_file(self):
        data = self.cleaned_data
        file = data['file']
        if not file:
            raise forms.ValidationError('Se necesita un fichero')
        if not file.name.split('.')[-1] in FILE_EXT:
            raise forms.ValidationError('Tipo de fichero incorrecto')
        return file
        
