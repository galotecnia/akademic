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

PADRE_MOVIL_NO_VERIFICADO = 'padre_no_verificado'
PADRE_SIN_MOVIL = 'movil_no_validado'
PADRE_NO_RESPONDE = 'padre_return_validador_en_blanco'
NUMERO_MAXIMO_INCIDENCIAS_MOVIL = 10

NOTIFICACION_PENDIENTE = 0
NOTIFICACION_ENVIADA = 1
NOTIFICACION_ERROR = 2
NOTIFICACION_CANCELADA = 3

ESTADO_NOTIFICACION = (
	(NOTIFICACION_PENDIENTE, 'Pendiente'),
	(NOTIFICACION_ENVIADA, 'Notificado'),
	(NOTIFICACION_ERROR, 'Error'),
	(NOTIFICACION_CANCELADA, 'No notificar'), )

CHAR_CHANGES = { '&': '', ';': '', '<': '', '>': '', }
