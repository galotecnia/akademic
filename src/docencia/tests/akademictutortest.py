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
from tests import AkademicBaseTest
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib import admin
from akademic2.akademic.models import *
from akademic2.akademic.auxFunctions import *
import pickle


class AkademicTutorTest(AkademicBaseTest):
    fixtures = ["evaluacion"]

# TODO: Test de que un profesor no tutor no pueda ver la vista.

    def setUp(self):
        self.profesor = Client ()
        self.WRITE = False

    def test_ListasTutorAsignaturaAccesoNoLogeado(self):
        """
            Controla que no puede acceder un usuario anónimo.
        """
        self.url = "%s/akademic/listasTutorAsignaturas/" % settings.SITE_LOCATION
        response = self.profesor.get(self.url)
        self.assertRedirects( response,
                'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, self.url),
                302, 301)

    def test_ListasTutorAsignaturaAccesoTutor(self):
        """
            Controla que un tutor puede acceder a la vista correspondiente
        """
        self.url = "%s/akademic/listasTutorAsignaturas/" % settings.SITE_LOCATION
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Asignat1")
        self.assertContains(response, "Asignat2")
        #self.pickleAssert("listastutorasignaturas_profesor1.pckl", repr(response.content))

    def test_ResumenEvaluacionTutorAccesoNoLogeado(self):
        """
            Controla que no puede acceder un usuario anónimo.
        """
        self.url = "%s/akademic/resumenEvaluacionTutor/" % settings.SITE_LOCATION
        response = self.profesor.get(self.url)
        self.assertRedirects( response,
                'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, self.url),
                302, 301)

    def test_ResumenEvaluacionTutorAccesoTutor(self):
        """
            Controla que un tutor puede acceder a la vista correspondiente.
        """
        self.url = "%s/akademic/resumenEvaluacionTutor/" % settings.SITE_LOCATION
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.post(self.url, {u'fechaianyo': [u'2006'], u'fechaimes': [u'02'], u'fechafmes': [u'03'],u'fechafdia': [u'9'], u'fechaidia': [u'1'], u'fechafanyo': [u'2009']})
        self.pickleAssert("resumenevaluaciontutor_profesor1.pckl", repr(response.content))

