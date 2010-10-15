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
from django.contrib.auth import authenticate


class UploadFileForm (forms.Form):
    username = forms.CharField(required = True)
    password = forms.CharField(required = True)
    md5 = forms.CharField(required = True)
    file = forms.FileField (required = True)
    file_date = forms.DateTimeField (required = True)

    def clean(self):
        cleaned_data = self.cleaned_data
        user = authenticate(username=cleaned_data.get('username'), password=cleaned_data.get('password'))
        if user is not None:
            if user.has_perm('addressbook.import_data'):
                return cleaned_data
            else:
                raise forms.ValidationError("No tiene privilegios para hacer una importacion.")
        raise forms.ValidationError("Nombre de usuario o contraseña incorrecto.")

class EndUploadForm (forms.Form):
    username = forms.CharField(required = True)
    password = forms.CharField(required = True)
    date = forms.DateTimeField (required = True)
