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

from akademic2.docencia.models import *
from akademic2.docencia.views import *

class NotificacionesTest(AkademicBaseTest):
    fixtures = ['tests_data.json']
    
    argumentos = {}
    context = {}
    post = {}
    
    def test_vista_seleccion_notificacion(self):        
        def init():
            self.argumentos.clear()
            self.context.clear()
            self.post.clear()
            
        def go():
            return selecciona_tipo_texto_notificacion(self.post, 
                                        self.argumentos, self.context)
        
        def show():
            print "---Volcado de las variables del test:"
            print "Argumentos: ", self.argumentos
            print ", Post: ", self.post,", Context: ", self.context
        
        self.post = { 'textoPredef': '1', 'textoCustom': 'prueba' }        
        if go():
            self.fail('Se aceptaron 2 tipos de notificaciones a la vez')
        
        init()        
        if go():
            self.fail('Se aceptó sin haberse mandado un texto')
        
        init()        
        self.post = { 'textoPredef': '1' }
        if not go():
            show()
            self.fail('No aceptó un texto predefinido')
        if not self.argumentos['texto_notificacion'].id is 1:
            show()
            self.fail('No se escogio el texto predefinido exacto')
        
        init()
        self.post = { 'textoCustom': 'prueba'}
        if not go():
            show()
            self.fail('No se acepto un texto customizado.')
        if not 'prueba' in self.argumentos['texto_string']:
            show()
            self.fail('No se introdujo el texto customizado correctamente')
