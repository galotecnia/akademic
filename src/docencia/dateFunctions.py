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

import datetime

def normalizarFecha(anyo, mes, dia):
    """
        Intenta generar un objeto datetime para cualquier fecha que
        se le pase. Si lo logra, lo devuelve, sino, normaliza la fecha
        a la anterior más próxima.

        Lo único malo con esta aproximación es que no tenemos constancia
        de la normalización.
    """
    try:
        fecha = datetime.datetime(anyo, mes, dia)
    except ValueError:
        # Primero resolvemos cuestiones relacionadas con los meses.
        if mes < 1:
            mes = 1
        if mes > 12:
            mes = 12
        # Ahora pasamos a intentar resolver lo que surja relacionado
        # con los días.
        salir = False
        while not salir:
            try:
                fecha = datetime.datetime(anyo, mes, dia)
                salir = True
            except ValueError:
                dia -= 1
    return fecha
    
