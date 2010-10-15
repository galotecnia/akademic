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
from addressbook.models import PersonaPerfil, Contacto

class PadreInfoForm(forms.Form):

    nombre = forms.CharField(max_length = 50, required = True)
    apellidos = forms.CharField(max_length = 100, required = True)
    
    casa = forms.CharField(label = u'Telefono casa', max_length = 15, required = False)
    movil = forms.CharField(label = u'Telefono movil', max_length = 15, required = False)
    trabajo = forms.CharField(label = u'Telefono trabajo', max_length = 15, required = False)
    fax = forms.CharField(label = u'Numero de fax', max_length = 15, required = False)
    email = forms.EmailField(label = 'Email',  max_length = 50, required = False)

    def __init__(self, *args, **kwargs):
        super(PadreInfoForm, self).__init__(*args, **kwargs)
        for k in self.fields.keys():
            self.fields[k].widget.attrs['readonly'] = True

class PadrePassword(forms.Form):
    
    old_pass = forms.CharField(max_length = 100, widget = forms.PasswordInput, label = u'Password actual')
    new_pass = forms.CharField(max_length = 100, widget = forms.PasswordInput, label= u"Nuevo password:")
    new_pass2 = forms.CharField(max_length = 100, widget = forms.PasswordInput, label= u"Repita password")
    
    def __init__(self, *args, **kwargs):
        super(PadrePassword, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if 'new_pass' in data and 'new_pass2' in data and data['new_pass'] == data['new_pass2']:
            return data
        raise forms.ValidationError(u"Ha repetido la contrasena mal, vuelta a escribirla")

