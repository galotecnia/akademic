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



class AkademicVerificadorTest(AkademicBaseTest):
    fixtures = ['verificador']


   #        - Consultar padres vacíos.
   #        - Consultar padres y que no coincida ninguno.
   #        - Consultar padres y que no exista ninguno con UsuarioPadre.
   #        - Consultar padres y que se genere la notificación correctamente.
   #        - Que intente acceder a la vista un usuario que no es verificador.

    def setUp(self):
        self.profesor = Client ()
        self.WRITE = False


    def test_AccesoNoLogeado(self):
        """
            Controla que no puede acceder un usuario anónimo.
        """
        url = "%s/akademic/reenvioPassword/" % settings.SITE_LOCATION
        response = self.profesor.get(url)
        self.assertRedirects( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url), 302, 301)


    def test_AccesoNoPermitido(self):
        """
           Controla que no puede acceder un usuario que no sea
           verificador.
        """

        # Hacemos login con un usuario que no es verificador..
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'profe1', 'password': 'profe1'})

        url = "%s/akademic/reenvioPassword/" % settings.SITE_LOCATION
        response = self.profesor.get(url)
        self.pickleAssert("reenvio_password_profe1.pckl", repr(response.content))

    def test_SoloUsuariosPadres(self):
        """
           Comprueba que en la vista no aparezca ningún padre que no tenga creado
           su usuario.
        """
        # Hacemos login con un usuario que sí es verificador..
        self.profesor.login(username = "profe2", password = "profe2")
        # Alteramos los settings para que el usuario verificador coincida con el actual.
        settings.VERIFICADOR = 5
        url = "%s/akademic/reenvioPassword/" % settings.SITE_LOCATION
        response = self.profesor.post(url, {'query': 'Goyo'})
        self.assertNotContains(response, "Goyo")

    def test_CambiaPassword(self):
        """
            Comprueba que se genere la notificacion para un padre al que se le cambia
            la contraseña.
            Se combrueba que la contraseña haya cambiado con respecto a la anterior.
        """
        # Obtenemos el usuario del padre al que le vamos a regenerar el password
        rene = UsuarioPadre.objects.get(padre__apellidos__icontains = "rene").usuario
        oldpass = rene.password
        # Obtenemos el número de Notificaciones presentes en el sistema.
        numNotif = Notificacion.objects.filter(confidencial = True).count()
        # Hacemos login con un usuario que sí es verificador..
        self.profesor.login(username = "profe2", password = "profe2")
        # Alteramos los settings para que el usuario verificador coincida con el actual.
        settings.VERIFICADOR = 5
        url = "%s/akademic/reenvioPassword/" % settings.SITE_LOCATION
        response = self.profesor.post(url, {u'padre': [u'2'], u'buscar': [u'Enviar contraseña']})
        rene = UsuarioPadre.objects.get(padre__apellidos__icontains = "rene").usuario
        newpass = rene.password
        newNumNotif = Notificacion.objects.filter(confidencial = True).count()
        # Comprobamos que se ha generado una nueva notificacion.
        self.assertEqual(numNotif + 1, newNumNotif)
        # Comprobamos que el password ha cambiado.
        self.assertNotEqual(oldpass, newpass)
