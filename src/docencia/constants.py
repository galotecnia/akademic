# -*- encoding: utf-8 -*-
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

NOMBRES_DIAS = ('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')

FALTA_ASISTENCIA=1
FALTA_COMPORTAMIENTO=2
FALTA_MATERIAL=3
RETRASO=4
FALTA_TAREA=5

# Duracion de las tutorias
DURACION_TUTORIAS = 60

TIPO_FALTAS = (
    (FALTA_ASISTENCIA, u'Asistencia'),
    (FALTA_COMPORTAMIENTO, u'Comportamiento'),
    (FALTA_MATERIAL, u'Material'),
    (RETRASO, u'Retraso'),
    (FALTA_TAREA, u'Tarea'),
)

OPCIONES_DIAS = (
    (1, u'Lunes'),
    (2, u'Martes'),
    (3, u'Miércoles'),
    (4, u'Jueves'),
    (5, u'Viernes'),
    (6, u'Sábado'),
    (7, u'Domingo')
)

# Algunas abreviaturas para las denominaciones de horas.
DEN_HORAS = ('Prim.', 'Seg.', 'Terc.', 'Cuart.', 'Quint.', 'Sext.', 'Sept.', 'Oct.', 'Dec.')

# Constantes para la selección del tipo de informe en orientador
GRUPO  = 100
AREA   = 101
ALUMNO = 102

OPCIONES_ORIENTADOR = (
    (GRUPO,  u'Informe de grupo'),
    (AREA,   u'Informe de área'),
    (ALUMNO, u'Informe de alumno'),
)
