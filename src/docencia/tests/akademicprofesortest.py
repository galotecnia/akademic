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
from akademic2.docencia.models import *
from akademic2.docencia.auxFunctions import *
import pickle


class AkademicProfesorTest (AkademicBaseTest):
    fixtures = ['test_inicial']

    def setUp(self):
        self.profesor = Client ()

    def test_GetHorario (self):
        # Profesor con horario de una hora por sesión
        profe = UsuarioProfesor.objects.get (usuario__username = 'prof4').profesor
        self.pickleAssert ('prof4_horariowebconTicks.pckl', repr(profe.getHorarioWeb(46)))

        # Profesor con un horario con desdoble
        profe = UsuarioProfesor.objects.get (usuario__username = 'prof14').profesor
        self.pickleAssert ('prof14_horariowebconTicks.pckl', repr(profe.getHorarioWeb(46)))

        # Profesor con horario de una sesión por día
        profe = UsuarioProfesor.objects.get (usuario__username = 'prof20').profesor
        self.pickleAssert ('prof20_horariowebconTicks.pckl', repr(profe.getHorarioWeb(46)))

    def test_GetListaAlumnos (self):
        # Desdoble
        profe = UsuarioProfesor.objects.get (usuario__username = 'prof4').profesor
        dia = 17
        mes = 11
        anyo = 2008
        hora = 6
        #self.WRITE = True
        self.pickleAssert ('alumnos_prof4_desdoble_lunes_primera.pckl', repr(profe.getFaltasFecha(dia, mes, anyo, hora)))
        #self.WRITE = False
        # Normal
        hora = 7
        self.pickleAssert ('alumnos_prof4_desdoble_lunes_segunda.pckl', repr(profe.getFaltasFecha(dia, mes, anyo, hora)))
        # Testeamos que cuando solicitamos faltas de un instante de tiempo en el que
        # hay clase de más de una asignatura, nos lo indica y nos sugiere que visitemos el horario
        # para que el profesor quién dirima el problema.
        profe = UsuarioProfesor.objects.get (usuario__username = 'prof20').profesor
        hora = 8
        self.assertEqual (u'No tiene clase a esta hora', profe.getFaltasFecha(dia, mes, anyo, hora))
        hora = [12, 1]
        self.assertEqual (u'Usted tiene clase actualmente de más de una asignatura, Seleccione una de ellas en en el horario.', profe.getFaltasFecha(dia, mes, anyo, hora))

    def test_LoginProfesor (self):
        ''' Testeamos que se necesita una contraseña correcta para hacer login como profesor.'''
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof14', 'password': '1234'})
        self.assertEqual (response.status_code, 200)
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof14', 'password': '123'})
        self.assertRedirects (response, 'http://testserver/akademic/akademic/faltasActual/')
        # Si ya estás autenticado te lleva a faltas actual directamente
        response = self.profesor.get('%s/' % settings.SITE_LOCATION)
        self.assertRedirects (response, 'http://testserver/akademic/akademic/faltasActual/')

    def test_ComportamientoFaltasActual (self):
        '''
            Verifica que la vista de comportamiento y faltas actual si no estás logueado o lo estás como un usuario
            que no es profesor te envien al login y no peten.
        '''
        url = '%s/akademic/faltasActual/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects ( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url),
            302, 301)

        url = '%s/akademic/comportamientoActual/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects ( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url),
            302, 301)

        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'rene', 'password': '123'})
        response = self.profesor.get (url)
        self.assertContains (response, 'Acceso no autorizado', 1, 403)

        url = '%s/akademic/faltasActual/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertContains (response, 'Acceso no autorizado', 1, 403)

    def test_InsertaFalta (self):
        '''
            Hay que probar que funciona tanto el método de insertar faltas como la vista para hacerlo.
            Además, hay que verificar la inserción en una sesión con más de un grupo y en una sesión con un solo grupo.
        '''

        # Intento de pirula
        url = '%s/akademic/insertafalta/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects ( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url),
            302, 301)
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof4', 'password': '123'})
        # Este test es fruto de uno de los errores que el sistema de logging nos está reportando.
        # Hay usuarios que no se sabe muy bien por qué, intentan hacer gets a esta URL.
        response = self.profesor.get (url)
        self.assertRedirects (response, 'http://testserver%s/akademic/faltasActual/' % settings.SITE_LOCATION)
        response = self.profesor.get ('%s/akademic/faltas/17-11-2008/6/' % settings.SITE_LOCATION)
        self.assertEqual (response.status_code, 200)
        #self.WRITE = True
        self.pickleAssert ('contexto_faltas_prof4_desdoble_lunes_primera.pckl', repr(response.content))
        #self.WRITE = False
        post_dict = {
            "asignatura": "827",
            "fecha":"2008-11-17",
            "hora": u"6",
            "next" : u"/akademic/akademic/faltas/17-11-2008/6/",
            "faltas" : (u"683", u"1471", u"1814"),
            "retrasos" : (u"683", u"1471", u"1814"),
            "ausencias" : (u"683", u"1471", u"1814"),
            "Validar parte" : True,
        }
        response = self.profesor.post ('%s/akademic/insertafalta/' % settings.SITE_LOCATION, post_dict)
        self.assertRedirects (response, 'http://testserver%s/akademic/faltas/17-11-2008/6/' % settings.SITE_LOCATION)
        response = self.profesor.get ('%s/akademic/faltas/17-11-2008/6/' % settings.SITE_LOCATION)
        self.pickleAssert ('contexto_faltas_prof4_desdoble_lunes_primera_con_faltas.pckl', repr(response.content))
        post_dict["hora"] = "7"
        post_dict["next"] = "/akademic/akademic/faltas/17-11-2008/7/"
        post_dict["faltas"] = (u"854", u"1421", u"696")
        post_dict["retrasos"] = (u"854", u"1421", u"696")
        post_dict["ausencias"] = (u"854", u"1421", u"696")
        response = self.profesor.post ('%s/akademic/insertafalta/' % settings.SITE_LOCATION, post_dict)
        self.assertRedirects (response, 'http://testserver%s/akademic/faltas/17-11-2008/7/' % settings.SITE_LOCATION)
        response = self.profesor.get ('%s/akademic/faltas/17-11-2008/6/' % settings.SITE_LOCATION)
        #self.WRITE = True
        self.pickleAssert ('contexto_faltas_prof4_desdoble_lunes_segunda_con_faltas.pckl', repr(response.content))
        #self.WRITE = False

    def test_InsertaComportamiento (self):
        '''
            Hay que probar que funciona tanto el método de insertar comportamiento como la vista para hacerlo.
            Además, hay que verificar la inserción en una sesión con más de un grupo y en una sesión con un solo grupo.
        '''

        # Intento de pirula
        url = '%s/akademic/insertacomportamiento/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url), 302, 301)
        # Login
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof4', 'password': '123'})
        # Este test es fruto de uno de los errores que el sistema de logging nos está reportando.
        # Hay usuarios que no se sabe muy bien por qué, intentan hacer gets a esta URL.
        response = self.profesor.get (url)
        self.assertRedirects (response, 'http://testserver%s/akademic/comportamientoActual/' % settings.SITE_LOCATION)
        response = self.profesor.get ('%s/akademic/comportamiento/17-11-2008/6/' % settings.SITE_LOCATION)
        self.assertEqual (response.status_code, 200)
        #self.WRITE = True
        self.pickleAssert ('contexto_comportamiento_prof4_desdoble_lunes_primera.pckl', repr(response.content))
        post_dict = {
            "asignatura": "827",
            "fecha":"2008-11-17",
            "hora":"6",
            "next" :"/akademic/akademic/17-11-2008/6/",
            "comportamiento" : (u"683", u"1471", u"1814"),
            "tarea" : (u"683", u"1471", u"1814"),
            "material" : (u"683", u"1471", u"1814"),
            "Enviar" : True,
        }
        response = self.profesor.post ('%s/akademic/insertacomportamiento/' % settings.SITE_LOCATION, post_dict)
        self.assertEqual (response.status_code, 200)
        response = self.profesor.get ('%s/akademic/comportamiento/17-11-2008/6/' % settings.SITE_LOCATION)
        self.pickleAssert ('contexto_comportamiento_prof4_desdoble_lunes_primera_con_faltas.pckl', repr(response.content))
        post_dict["hora"] = "7"
        post_dict["next"] = "/akademic/akademic/17-11-2008/7/"
        post_dict["comportamiento"] = (u"854", u"1421", u"696")
        post_dict["tarea"] = (u"854", u"1421", u"696")
        post_dict["material"] = (u"854", u"1421", u"696")
        response = self.profesor.post ('%s/akademic/insertacomportamiento/' % settings.SITE_LOCATION, post_dict)
        self.assertEqual (response.status_code, 200)
        response = self.profesor.get ('%s/akademic/comportamiento/17-11-2008/6/' % settings.SITE_LOCATION)
        self.pickleAssert ('contexto_comportamiento_prof4_desdoble_lunes_segunda_con_faltas.pckl', repr(response.content))
        #self.WRITE = False

    def test_ListadosProfesor (self):
        '''
            Testeamos la generación de listados de profesor.
        '''

        # Intento de pirula
        url = '%s/akademic/listadosProfesor/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url), 302, 301)

        # Login
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof4', 'password': '123'})

        response = self.profesor.get (url)
        self.assertEqual (response.status_code, 200)

        post_dict = {
            "fechames": "10", # Octubre
            "fechanyo":"2008",
            "asignaturas" : (u"249@301", u"2685@301", u"827@268", u"827@269", u"1598@268"),
        }
        #self.WRITE = True
        for tipo in ('asistencia', 'retraso', 'comportamiento', 'tareas', 'material'):
            post_dict['tipoListado'] = tipo
            response = self.profesor.post (url, post_dict)
            self.pickleAssert ('listados_profesor_prof4_%s.pckl' % tipo, repr(response.content))
        #self.WRITE = False

    def test_ListadosTotalesTutor(self):
        '''
            Testeamos la generación de listados totales del tutor.
        '''

        # Intento de pirula
        url = '%s/akademic/resumenTutor/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url), 302, 301)

        # Login
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof4', 'password': '123'})

        response = self.profesor.get (url)
        self.assertEqual (response.status_code, 200)

        post_dict = {
            "fechaidia": "1",
            "fechaimes": "9", # Septiembre
            "fechaianyo":"2008",
            "fechafdia": "1",
            "fechafmes": "10", # Octubre
            "fechafanyo":"2008",
        }
        #self.WRITE = True
        response = self.profesor.post (url, post_dict)
        self.pickleAssert ('listados_totales_profesor_prof4.pckl', repr(response.content))
        #self.WRITE = False

    def test_admin (self):
        ''' Testeando la interfaz de administración ... '''

        username = 'rene'
        password = '123'
        urls = []

        admin.autodiscover()
        for model, model_admin in admin.site._registry.items():
            app_label = model._meta.app_label
            if app_label == 'akademic':
                model_url = '%s/admin/%s/%s/' % (settings.SITE_LOCATION, app_label, model.__name__.lower())
                urls.append (model_url)
                for obj in model.objects.all()[:10]:
                    urls.append ('%s%s/' % (model_url, obj.id))

        c = Client()
        if not c.login(username=username, password=password):
            self.fail ("No pude logearme")
        else:
            for url in urls:
                response = c.get(url)
                self.assertEqual (response.status_code, 200,'url="%s", response=%d' % (url, response.status_code))

    def test_NotificacionSMSProfesor (self):
        ''' Hay que verificar que cuando se intenta enviar un mensaje mayor de lo normal pete '''

        # Intento de pirula
        url = '%s/akademic/notificacionSmsProfesor/' % settings.SITE_LOCATION
        response = self.profesor.get (url)
        self.assertRedirects( response,
            'http://testserver%s/accounts/login?next=%s' % (settings.SITE_LOCATION, url), 302, 301)

        # Login
        response = self.profesor.post('%s/' % settings.SITE_LOCATION, {'usuario': 'prof4', 'password': '123'})

        post_dict = {
            'alumnos': '852,828,1709',
            'textoCustom': 'Un mensaje de texto perfectamente válido'
        }
        response = self.profesor.post(url, post_dict)
        self.assertContains (response, 'Se han generado 6 sms', 1, 200)

        post_dict['textoCustom'] =  u'este mensaje debería tener 160 caracteres, ni uno más ni uno menos..............................................................................................'
        response = self.profesor.post(url, post_dict)
        self.assertContains (response, 'Se han generado 6 sms', 1, 200)

        post_dict['textoCustom'] =  u'este texto que escribo tiene claramente bastantes más de 160 caracteres, en teoría un sms no puede sobrepasar este límite. Si además de esto el sms esta escrito en unicode el tema es más grave porque se reduce a la mitad lo que soporta. Esto deberíamos tenerlo en cuenta para o bien partir el mensaje o bien eliminar todo lo que no sea ascii de los mensajes.'
        response = self.profesor.post(url, post_dict)
        # Aquí hay que poner el mensaje correcto del tema.
        self.assertContains (response, 'El mensaje es demasiado largo', 1, 200)
