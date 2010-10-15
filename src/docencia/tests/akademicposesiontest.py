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


class AkademicPosesionTest(AkademicBaseTest):
    fixtures = ["posesion"]

    def setUp(self):
        self.profesor = Client ()
        self.WRITE = False
        self.url = "%s/akademic/poseer/" % settings.SITE_LOCATION

    def test_AccesoNoLogeado(self):
        """
            Controla que no puede acceder un usuario anónimo.
        """
        response = self.profesor.get(self.url)
        self.assertRedirects( response,
                'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, self.url),
                302, 301)

    def test_AccesoCoordinadorCiclo(self):
        """
            Controla que un coordinador de ciclo pueda, efectivamente disponer de la
            opción de llevar a cabo posesiones.
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Poseer")

    def test_AccesoJefeEstudios(self):
        """
            Controla que un Jefe de estudios pueda, efectivamente, disponer de la
            opción de llevar a cabo posesiones.
        """
        self.profesor.login(username = "jefeestudios", password = "jefeestudios")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Poseer")

    def test_AccesoDirector(self):
        """
            Controla que un Director pueda, efectivamente, disponer de la
            opción de llevar a cabo posesiones.
        """
        self.profesor.login(username = "director", password = "director")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Poseer")

    def test_ListaProfesoresCoordinador(self):
        """
            Comprueba que la lista de profesores que se obtiene en la interfaz
            sólo contiene los profesores que imparten docencia en el ciclo
            del coordinador.
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.pickleAssert("posesion_coordinador.pckl", repr(response.content))

    def test_ListaProfesoresJefeEstudios(self):
        """
            Comprueba que la lista de profesores que se obtiene en la interfaz
            sólo contiene los profesores del nivel del jefe de estudios.
        """
        self.profesor.login(username = "jefeestudios", password = "jefeestudios")
        response = self.profesor.get(self.url)
        self.pickleAssert("posesion_jefeestudios.pckl", repr(response.content))

    def test_ListaProfesoresDirector(self):
        """
            Comprueba que la lista de profesores que se obtiene en la interfaz
            sólo contiene a todos los profesores del centro.
        """
        self.profesor.login(username = "director", password = "director")
        response = self.profesor.get(self.url)
        self.pickleAssert("posesion_director.pckl", repr(response.content))

    def test_ProfesoresCoordinador(self):
        """
            Similar al anterior, pero ahora comprueba directamente los profesores
            que deben estar en la lista.
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Profe3")
        # Lo quitamos porque la cadena sí aparece en el breadcrumbs
        # self.assertNotContains(response, "Profe1")
        self.assertNotContains(response, "Profe2")

    def test_ProfesoresJefeEstudios(self):
        """
            Similar al anterior, pero ahora comprueba directamente los profesores
            que deben estar en la lista.
        """
        self.profesor.login(username = "jefeestudios", password = "jefeestudios")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Profe1")
        self.assertContains(response, "Profe3")
        self.assertNotContains(response, "Profe2")

    def test_ProfesoresDirector(self):
        """
            Similar al anterior, pero ahora comprueba directamente los profesores
            que deben estar en la lista.
        """
        self.profesor.login(username = "director", password = "director")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Profe1")
        self.assertContains(response, "Profe2")
        self.assertContains(response, "Profe3")

    def test_PosesionValida(self):
        """
            Intenta poseer a un usuario válido.
        """
        self.profesor.login(username = "jefeestudios", password = "jefeestudios")
        response = self.profesor.post(self.url, {'profesor': '1'})
        self.pickleAssert("posesionvalida_jefeestudios.pckl", repr(response.content))

    def test_PosesionNoValida(self):
        """
            Intenta poseer a un profesor que no tiene usuario válido en el sistema
        """
        cadenaError = "El profesor seleccionado no dispone de usuario en el sistema, contacte con el administrador."
        self.profesor.login(username = "jefeestudios", password = "jefeestudios")
        response = self.profesor.post(self.url, {'profesor': '3'})
        self.assertContains(response, cadenaError)
