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
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from models import Incidencia
import datetime

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['comment',]

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)

    def save(self, request, instance):
        item = super(CommentForm, self).save(commit = False)
        item.site = Site.objects.all()[0]
        item.content_object = instance
        now = datetime.datetime.now()
        item.submit_date = datetime.datetime.today()
        item.user = request.user
        # Salvamos la IP. Ver utilidad 
        item.ip_address = request.META['REMOTE_ADDR']
        item.save()

class IncidenciaForm(forms.ModelForm):
    
    class Meta:
        model = Incidencia
        exclude = ['id','informador', 'fecha',]

    def save(self, user):
        item = super(IncidenciaForm, self).save(commit = False)
        item.informador = user
        item.fecha = datetime.date.today()
        item.save()
        

class UpdateIncidenciaForm(forms.ModelForm):
        
    class Meta:
        model = Incidencia
        fields = ['tipoIncidencia', 'estado', 'prioridad',]
