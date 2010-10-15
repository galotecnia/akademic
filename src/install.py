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
# En este fichero deberemos colocar todos los datos iniciales que necesita
# akademic para funcionar correctamente.
#
# http://code.djangoproject.com/wiki/InitialSQLDataDiangoORMWay

# Para que este script funcione como dios manda hay que hacer un enlace
# en el directorio del proyecto tal que así:
# 
#                       ln -s ./ akademic2
#
# Cosa que me parece una burrada como un templo intentaré resolverlo de otra manera

from os import environ
from django.contrib.auth.models import Group, Permission
from django.conf import settings

environ['DJANGO_SETTINGS_MODULE'] = 'settings'



# Grupo en el que introduciremos al usuario de Cándido cuando esté
g = Group(name='porteria')
g.save()
