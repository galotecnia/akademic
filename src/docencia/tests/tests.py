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
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib import admin
from akademic2.docencia.models import *
from akademic2.docencia.auxFunctions import *
import pickle

class AkademicBaseTest (TestCase):
    WRITE = False

    def pickleAssert (self, string, data):
        if self.WRITE:
            pickle.dump (data,open ('%s/akademic/test-data/%s' % (settings.PROJECT_ROOT , string), 'w'))
        else:
            static_data = pickle.load (open ('%s/akademic/test-data/%s' % (settings.PROJECT_ROOT , string), 'r'))
            self.assertEqual (data, static_data)
