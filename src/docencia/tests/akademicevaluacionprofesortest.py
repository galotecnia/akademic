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


class AkademicEvaluacionProfesorTest(AkademicBaseTest):
    fixtures = ["evaluacion"]

    def setUp(self):
        self.profesor = Client ()
        self.WRITE = False
        self.url = "%s/akademic/evaluacionProfesor/" % settings.SITE_LOCATION

    def test_AccesoNoLogeado(self):
        """
            Controla que no puede acceder un usuario anónimo.
        """
        response = self.profesor.get(self.url)
        self.assertRedirects( response,
                'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, self.url),
                302, 301)

    def test_AccesoProfesor(self):
        """
            Controla que un coordinador de ciclo pueda, efectivamente disponer de la
            opción de llevar a cabo posesiones.
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Profesor >> Evaluación")

    def test_AsignaturasProfesor1(self):
        """
           Controla que el profesor1 sólo pueda evaluar aquellas
           asignaturas en las que da clase.
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.get(self.url)
        self.assertContains(response, "Asignat1 - 11")
        self.assertContains(response, "Asignat2 - 12B")

    def test_AsignaturasProfesor2(self):
        """
           Comprueba que el profesor2 no tenga en su lista de asignaturas
           la Asignat2
        """
        self.profesor.login(username = "profe2", password = "profe2")
        response = self.profesor.get(self.url)
        self.assertNotContains(response, "Asignat2 - 11")

    def test_CalificacionesEv1(self):
        """
           En la primera evaluación, el alumno1 en la asignatura 1 debe tener un 10
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.post(self.url, {'evaluacion': ['1'], 'asignaturas': ['1@1']})
        self.assertContains(response, "10")
        self.pickleAssert("calificacion1ev_profesor1.pckl", repr(response.content))

    def test_CalificacionCorrecta(self):
        """
           Cambia la nota del alumno1, en la asignatura 1, pasa de tener un 10
           a tener un 9
        """
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.post(self.url, {'evaluacion': ['1'], '1@1': ['9']})
        self.assertContains(response, "Sus calificaciones se han almacenado correctamente.")
        evaluacion = Evaluacion.objects.get(nombre = "1", cursoEscolar = "2008")
        asignatura = Asignatura.objects.get(nombreCorto = "Asignat1")
        alumno = Alumno.objects.get(pk = 1)
        calificacion = Calificacion.objects.get(
                            evaluacion = evaluacion,
                            asignatura = asignatura,
                            alumno = alumno
                        )
        self.assertEqual(calificacion.nota, "9")

    def test_CalificacionMenorCero(self):
        """
           Cambia la nota del alumno1, en la asignatura 1, pasa de tener un 10
           a tener un -1, esto debe hacer que se muestre un mensaje de error.
           Además la calificación no debe cambiar.
        """
        msg = """Ha introducido una nota menor que 0 para el alumno"""
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.post(self.url, {'evaluacion': ['1'], '1@1': ['-1']})
        self.assertContains(response, msg)
        evaluacion = Evaluacion.objects.get(nombre = "1", cursoEscolar = "2008")
        asignatura = Asignatura.objects.get(nombreCorto = "Asignat1")
        alumno = Alumno.objects.get(pk = 1)
        calificacion = Calificacion.objects.get(
                            evaluacion = evaluacion,
                            asignatura = asignatura,
                            alumno = alumno
                        )
        self.assertEqual(calificacion.nota, "10")

    def test_CalificacionMayorDiez(self):
        """
           Cambia la nota del alumno1, en la asignatura 1, pasa de tener un 10
           a tener un 11, esto debe hacer que se muestre un mensaje de error.
           Además la calificación no debe cambiar.
        """
        msg = """Ha introducido una nota mayor que 10 para el alumno"""
        self.profesor.login(username = "profe1", password = "profe1")
        response = self.profesor.post(self.url, {'evaluacion': ['1'], '1@1': ['11']})
        self.assertContains(response, msg)
        evaluacion = Evaluacion.objects.get(nombre = "1", cursoEscolar = "2008")
        asignatura = Asignatura.objects.get(nombreCorto = "Asignat1")
        alumno = Alumno.objects.get(pk = 1)
        calificacion = Calificacion.objects.get(
                            evaluacion = evaluacion,
                            asignatura = asignatura,
                            alumno = alumno
                        )
        self.assertEqual(calificacion.nota, "10")
