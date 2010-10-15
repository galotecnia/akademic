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
from django.forms import ModelForm
from django import forms
from models import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import AdminDateWidget
from django.conf import settings
import re

from rhetor import decorate_bound_field
decorate_bound_field()

input_formats = ['%Y-%m-%d',  '%m/%d/%y', # '2006-10-25',  '10/25/06'
                                                '%b %d %Y', '%b %d, %Y',            # 'Oct 25 2006', 'Oct 25, 2006'
                                                '%d %b %Y', '%d %b, %Y',            # '25 Oct 2006', '25 Oct, 2006'
                                                '%B %d %Y', '%B %d, %Y',            # 'October 25 2006', 'October 25, 2006'
                                                '%d %B %Y', '%d %B, %Y',            # '25 October 2006', '25 October, 2006'
                                                '%d/%m/%Y',]                       # '25/10/2006'

class PersonaForm(ModelForm):
    fecha_nacimiento = forms.DateField( input_formats = input_formats,
                                        widget = forms.TextInput(attrs={'id':'nacimiento'}), 
                                        label = _(u"Fecha de nacimiento"), required=False)
    
    def clean (self):
        data = self.cleaned_data 
        if not data.has_key ('tipo_documento_identificacion'):
            data['documento_identificacion'] = None
        elif data['documento_identificacion'].strip() == '':
            data['documento_identificacion'] = None
        elif data['tipo_documento_identificacion'] == DNI and \
            data['documento_identificacion']:
            pass
            """
            p = Persona.objects.filter(documento_identificacion = data['documento_identificacion'])
            if p: 
                if p[0].nombre == data['nombre'] and p[0].apellidos == data['apellidos']:
                    raise forms.ValidationError("La persona existe en la BB.DD. ¿Es un caso cliente-profesor? \
                                                 En caso afirmativo, reescriba el DNI")
                else:
                    raise forms.ValidationError("El DNI introducido ya se encuentra en la BB.DD.")
            """
        return data

    class Meta:
        model = Persona
        
    class Media:
        css = {'screen': ("%s/theme/ui.all.css" % settings.MEDIA_URL,)}
        js = ("%s/js/jquery-latest.js" % settings.MEDIA_URL,
              "%s/js/jquery-ui-personalized-1.5.3.js" % settings.MEDIA_URL,
              "%s/js/jquery.datepick-es.js" % settings.MEDIA_URL)  

class PersonaForm2(ModelForm):
    fecha_nacimiento = forms.DateField( input_formats = input_formats,
                                        widget = forms.TextInput(attrs={'id':'nacimiento'}), 
                                        label = _(u"Fecha de nacimiento"), required=False)
    
    class Meta:
        model = Persona
	exclude = ['documento_identificacion', 'tipo_documento_identificacion'] 
        
    class Media:
        css = {'screen': ("%s/theme/ui.all.css" % settings.MEDIA_URL,)}
        js = ("%s/js/jquery-latest.js" % settings.MEDIA_URL,
              "%s/js/jquery-ui-personalized-1.5.3.js" % settings.MEDIA_URL,
              "%s/js/jquery.datepick-es.js" % settings.MEDIA_URL)  

class DireccionForm(ModelForm):
    class Meta:
        model = Direccion
        exclude = ['persona']

####################################
# FUNCIONES DE CHECKEO DE CONTACTO #
####################################

def check_tlf(telefono):
    try:
        a = int(telefono)
    except ValueError:
        return  "Introduzca un número de teléfono válido" 
    if int(telefono) < 0:
        return  "El númmero de teléfono ha de ser positivo" 
    if not telefono.find('+') and (len(telefono) < 10 or len(telefono) > 13):
        return  "El número de dígitos del teléfono es incorrecto"
    if len(telefono) != 9:
        return "El número de dígitos del teléfono es incorrecto"
    return False

def check_email(email):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) == None:
        return "El email introducido no tiene el formato correcto"
    return False

def generic(dato):
    if not str(dato):
        return "Introduzca una dirección válida"
    return False

##### DICCIONARIO CON LAS FUNCIONES DE COMPROBACION #####
###### DEPENDIENTES DEL TIPO DE CAMPO DEL CONTACTO ######
case = {
    T_PERSONAL  : check_tlf,
    T_TRABAJO   : check_tlf,
    EM_PERSONAL : check_email,
    EM_TRABAJO  : check_email,
    104 : check_tlf, # FAX_PERSONAL
    105 : check_tlf, # FAX_TRABAJO
    M_PERSONAL  : check_tlf,
    M_TRABAJO   : check_tlf,
    108 : generic,
    109 : generic,
    110 : generic,
    111 : generic,
    112 : generic,    
}
 
class ContactoForm(ModelForm):
    class Meta:
        model = Contacto
        exclude = ['persona']

    def clean(self):
        data = self.cleaned_data
        # Obtenemos la cadena con el error 
        # de la funcion de checkeo correspondiente
        s = case[data['tipo']](data['dato'])
        if s:
            raise forms.ValidationError( s ) 
        return data



