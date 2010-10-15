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
from addressbook.models import Persona

class SearchTests (TestCase):

    fixtures = ["search_fixtures"]
    
    def test_SearchName(self):
        personas = Persona.search ('profesor1')
        self.assertEqual (personas[0], Persona.objects.get (pk = 1))
        self.assertEqual (1, len (personas))

    def test_SearchSurname(self):
        personas = Persona.search ('apellido')
        self.assertEqual (personas[0], Persona.objects.get (pk = 1))
        self.assertEqual (personas[1], Persona.objects.get (pk = 2))
        self.assertEqual (2, len (personas))

    def test_SearchIDDocument(self):
        personas = Persona.search ('123123123J')
        self.assertEqual (personas[0], Persona.objects.get (pk = 1))
        self.assertEqual (1, len (personas))

    def test_SearchNation(self):
        personas = Persona.search ('Espa')
        self.assertEqual (personas[0], Persona.objects.get (pk = 1))
        self.assertEqual (personas[1], Persona.objects.get (pk = 2))
        self.assertEqual (2, len (personas))

    def test_SearchPlaceOfBirth(self):
        personas = Persona.search ('Tenerife')
        self.assertEqual (personas[0], Persona.objects.get (pk = 2))
        self.assertEqual (1, len (personas))

    def test_SearchTwoFields(self):
        personas = Persona.search ('Espa Tene')
        self.assertEqual (personas[0], Persona.objects.get (pk = 2))
        self.assertEqual (1, len (personas))

    def test_SearchTel(self):
        personas = Persona.search ('922123456')
        self.assertEqual (personas[0], Persona.objects.get (pk = 1))
        self.assertEqual (1, len (personas))
