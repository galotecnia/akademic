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
from django.conf.urls.defaults import *
from recursos.models import *
from django.db.models import Q

urlpatterns = patterns('recursos.views',
    url(r'^$',                                      'index',        name="recursos_raiz"),
    url(r'^lista/(?P<tipo_recurso>\w+)/',           'listatipo',    name="lista_recursos"),
    url(r'^lista/',                                 'listatipo',    name="lista_recursos"),
    url(r'^reservas/eliminar/(?P<reserva_id>\w+)/', 'eliminarReserva', name="eliminar_reserva"),
    url(r'^reservas/(?P<tipo_recurso>\w+)/',        'reservas',     name="lista_reservas"),
    url(r'^reservas/',                              'reservas',     name="lista_reservas"),
    url(r'^nuevareserva/(?P<recurso_id>\w+)/',      'nuevaReserva', name="nueva_reserva"),
    url(r'^nuevo_recurso/',                         'nuevo_recurso', name="nuevo_recurso"),
)
