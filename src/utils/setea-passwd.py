#!/usr/bin/python
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

from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.contrib.auth.models import User

print u"Cambiando contraseñas de los usuarios"
i = 0
for u in User.objects.all():
    u.password = u'sha1$8b337$c5d145845c8b6b438d6bdfe2bca629efba21822f'
    u.save()
    i += 1
print u"%d contraseñas cambiadas" % i
