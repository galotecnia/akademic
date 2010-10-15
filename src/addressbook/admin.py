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
from models import Persona, Contacto, Direccion, PersonaPerfil
from docencia.admin import BaseAdmin

class ContactoInline(admin.options.TabularInline):
    model = Contacto
    extra = 1
    
class DireccionInline(admin.options.TabularInline):
    model = Direccion
    extra = 1

class PersonaAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'documento_identificacion', 'fecha_nacimiento')
    search_fields = ['nombre', 'apellidos']
    inlines = [ContactoInline,DireccionInline]

admin.site.register(Persona, PersonaAdmin)

class ContactoAdmin(BaseAdmin):
    list_display = ('dato', 'tipo', 'persona')
    related_search_fields = {
        'persona': ('nombre', 'apellidos',),
    }

admin.site.register(Contacto, ContactoAdmin)

class DireccionAdmin(BaseAdmin):
    list_display = ('__unicode__', 'tipo', 'persona')
    related_search_fields = {
        'persona': ('nombre', 'apellidos',),
    }

class PersonaPerfilAdmin(BaseAdmin):
    list_display = ('__unicode__', 'documento_identificacion', 'fecha_nacimiento')
    related_search_fields = {
        'user': ('username', 'email'),
    }
    search_fields = ['nombre', 'apellidos', 'user__username']

admin.site.register(Direccion, DireccionAdmin)
admin.site.register(PersonaPerfil, PersonaPerfilAdmin)
