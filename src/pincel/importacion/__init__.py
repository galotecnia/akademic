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

IMPORT_FILES = [
        'alumnos.cdx', 'alumnos.dbf', 'area_alu.cdx', 'area_alu.dbf', 'aulas.cdx', 'aulas.dbf', 'docentes.cdx',
        'docentes.dbf', 'evaluaci.cdx', 'evaluaci.dbf', 'faltalum.cdx', 'faltalum.dbf', 'faltalum.fpt',
        'faltas.cdx', 'faltas.dbf', 'faltas.fpt', 'grupos.cdx', 'grupos.dbf', 'horario.cdx', 'horario.dbf',
        'matri.cdx', 'matri.dbf', 'matri.fpt', 'niveles.cdx', 'niveles.dbf', 'padres.cdx', 'padres.dbf',
        'tutorias.cdx', 'tutorias.dbf', 'notas.dbf', 'notas.cdx', 'notas.fpt', 'informes.cdx', 'informes.dbf',
        'informes.fpt', 'datos_extra.xls', 'islas.dbf', 'islas.cdx', 'provncia.cdx', 'provncia.dbf',
        'estpadre.dbf', 'estpadre.cdx', 'paises.cdx', 'paises.dbf', 'profsion.dbf', 'profsion.cdx',
        'autoriza.dbf', 'autoriza.cdx', 'espacio1.dbf', 'espacio1.cdx', 'espacio2.dbf', 'espacio2.cdx',
        'espacio3.dbf', 'espacio3.cdx', 'ubica.cdx', 'ubica.dbf', 'conciert.cdx', 'conciert.dbf', 'minusval.dbf',
        'minusval.cdx', 'estcivil.cdx', 'estcivil.dbf', 'asignas.dbf', 'asignas.cdx', 'turnos.cdx', 'turnos.dbf',
        'muncipio.cdx', 'muncipio.dbf', 'clasfica.dbf', 'clasfica.cdx', 'centros.cdx', 'centros.dbf'
    ]

def start_import(data_dir, dry_run = False, tabular = True, variable = True, excel = True, delete = True):
    """
        Comienza el proceso de importación propiamende dicho. Hasta ahora todo eran preparaciones para
        tener los datos organizados y disponibles.
    """
    from importer import Importer
    importer = Importer(data_dir)

    if tabular:
        print u"Realizando la importacion tabular" 
        if not dry_run:
            importer.import_tabular_data()
    if variable:
        print u"Realizando la importacion variable"
        if not dry_run:
            importer.import_variable_data()
    if excel:
        print u"Realizando la importacion del datos_extra"
        if not dry_run:
            importer.import_excel(variable)
    print u"Eliminando los datos no marcados"
    # TODO: Crear gestionar_jornadas_continuas que meta las matriculas de 
    # los alumnos de los grupos en las asignaturas T.[INF|PRI]
    # de forma automatica, ahora mismo esto se hace si se importa del excel,
    # y si este no ha variado no se importa y elimina las matriculas
    # importer.gestionar_jornadas_continuas()
    importer.delete_non_used_data(not dry_run and delete)
    return importer.log_result

