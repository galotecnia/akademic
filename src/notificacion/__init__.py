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
from models import Notificacion
from constants import *

def enviar_notificacion_a_alumnos(lista_alumnos, kwargs):
    """
        lista_alumnos: Lista de ids del modelo Alumno
    """
    contador = 0;
    lista_errores_alumnos = {
        PADRE_SIN_MOVIL: {
            'nombre_completo': 'No tiene registrado un número de móvil',
            'datos': [] },
        PADRE_MOVIL_NO_VERIFICADO: {
            'nombre_completo': 'No ha verificado su número de móvil',
            'datos': [] }, }
    
    for alumno in lista_alumnos:
        kwargs['alumno'] = alumno
        if alumno.padre:
            kwargs['padre'] = alumno.padre
            if manejador_envio_notificaciones(lista_errores_alumnos, kwargs):
                contador += 1
        if alumno.madre:
            kwargs['padre'] = alumno.madre
            if manejador_envio_notificaciones(lista_errores_alumnos, kwargs):
                contador += 1
    #Comprobamos que el número de padres con problemas al enviar no supere cierto valor,
    #y en dicho caso formateamos la salida.
    for tipo, lista in lista_errores_alumnos.iteritems():        
        cuenta = len(lista['datos'])
        if cuenta > NUMERO_MAXIMO_INCIDENCIAS_MOVIL:
            lista_errores_alumnos[tipo]['datos'] = ['Número de personas: ' + str(cuenta), ]
    
    return contador, lista_errores_alumnos
    
def manejador_envio_notificaciones(lista_errores, kwargs):
    """
        Se espera una lista como la siguiente:
        
        lista_tipo = {
            'padre_no_verificado': {
                'nombre_completo': 'El número de móvil del padre no ha sido verificado aún',
                'datos': [<padre_1>, <padre_2>, ...]
             }
        }                
    """
    try:
        Notificacion.envia_notificacion(**kwargs)        
    except RuntimeError, detail:
        info = detail.args[0]
        lista_errores[info]['datos'].append(kwargs['padre'])
        return None
    return True
