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

from addressbook.models import PersonaPerfil
from addressbook.models import M_PERSONAL

from docencia.models import Alumno

from padres.models import Padre

from notificacion.models import *

class NotificacionesTests(TestCase):
    """
        TODO:
        -Comprobar padres sin verificar, sin moviles, etc
    """    
    fixtures = ["tests_data"]
    padre = None
    hijo = None
    
    def setUp(self):
        self.padre = Padre.objects.get(pk=1)
        self.hijo = self.padre.get_hijos()[0]
    
        
    def test_envia_notificacion(self):
        valor_retorno = Notificacion.envia_notificacion(self.padre, self.hijo, 
                                                        texto_string='prueba',
                                                        force=True)
        self.assertEqual (True, valor_retorno)
        
    def test_no_aceptar_2_textos_al_mismo_tiempo(self):
        texto_notificacion = TextoNotificacion.objects.all()[0]
        try: 
            valor_retorno = Notificacion.envia_notificacion(self.padre, self.hijo, 
                            texto_string='prueba', texto_notificacion=texto_notificacion, 
                            force=True)
        except Exception:
            pass
        else:   
            self.assertFail('Se enviaron 2 mensajes al mismo tiempo')
