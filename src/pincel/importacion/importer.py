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

import logging
import re
import datetime

from dbfpy.dbf_optimizado import Dbf
from dbfmemoreader import readDbf

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from conector.data_repo import DataRepo
from pincel.models import *
from docencia.models import Asignatura, Alumno, Profesor, Nivel, GrupoAula, JefeEstudios, CoordinadorCiclo
from docencia.models import Ciclo, Curso, Matricula, GrupoAulaAlumno, AsignaturasPendientes
from docencia.tutoria.models import Tutor, Tutoria
from docencia.horarios.models import Hora, Horario, OPCIONES_DIAS
from docencia.notas.models import Evaluacion, CalificacionCompetencia, Calificacion
from addressbook.models import Persona, PersonaPerfil, DNI, EM_PERSONAL, D_PERSONAL
from addressbook.models import Direccion, Contacto
from addressbook.models import M_PERSONAL
from padres.models import Padre
from docencia.auxFunctions import isPadre, getCiclosJornadaContinua

import gxls

# Logging configuration and functions
log = logging.getLogger('galotecnia')

GRUPO_DATOS_SIMPLES = {
    'Islas': { 'tablapincel': 'islas', 'modelo': Isla },
    'Provincia': { 'tablapincel': 'provncia', 'modelo': Provincia },
    'Estudios del padre': { 'tablapincel': 'estpadre', 'modelo': EstudiosPadre },
    'Paises': { 'tablapincel': 'paises', 'modelo': Pais },
    'Profesion': { 'tablapincel': 'profsion', 'modelo': Profesion },
    'Autorizacionn': { 'tablapincel': 'autoriza', 'modelo': Autorizacion },
    'Clasificacion': { 'tablapincel': 'clasfica', 'modelo': Clasificacion },
    'Tipo de Espacio': { 'tablapincel': 'espacio1', 'modelo': TipoEspacio },
    'Tipo de Construccion': { 'tablapincel': 'espacio2', 'modelo': TipoConstruccion },
    'Tipo de Uso': { 'tablapincel': 'espacio3', 'modelo': TipoUso },
    'Ubicacion': { 'tablapincel': 'ubica', 'modelo': Ubicacion },
    'Concierto': { 'tablapincel': 'conciert', 'modelo': Concierto, 'codigo': 1 },
    'Minusvalia': { 'tablapincel': 'minusval', 'modelo': Minusvalia, 'codigo': 1 },
    'Estado Civil': { 'tablapincel': 'estcivil', 'modelo': EstadoCivil, 'codigo': 1 },
    'Municipio': { 'tablapincel': 'muncipio', 'modelo': Municipio }
}

MUNICIPIO_TRANSLATOR = {
    'VALSEQUILLO': 'Valsequillo de Gran Canaria',
    'SAN NICOLáS DE TOLENTINO': 'LA ALDEA DE SAN NICOLáS',
    'FUENCALIENTE DE LA PALMA': 'Fuencaliente',
    'SANTA MARíA DE GUíA': 'Santa María de Guía de Gran Canaria',
    'SANTA LUCíA DE TIRAJANA': 'Santa lucía',
    'VILLA DE MAZO': 'Mazo',
    'SANTA úRSULA': 'SANTA ÚRSULA',
    'VALVERDE DEL HIERRO': 'VALVERDE',
    'LAS PALMAS DE G.C.': 'LAS PALMAS DE GRAN CANARIA',
    'VECINDARIO': 'Santa lucía',
    'LA LAGUNA': 'San Cristobal de La Laguna',
    'SAN MIGUEL': 'San Miguel de Abona',
    'CORRALEJO': 'La Oliva',
    'PUERTO DEL CARMEN': 'Tías',
    'LOS CRISTIANOS': 'Arona',
    'EL MéDANO': 'Granadilla de Abona',
    'CHO': 'Arona',
}

ISLA_TRANSLATOR = {
    'GOMERA, LA': 'LA GOMERA',
    'PALMA': 'LA PALMA',
    'PALMA, LA': 'LA PALMA',
    'HIERRO, EL': 'EL HIERRO',
}

NO_CAPITALIZE = [u'de', u'la', u'los', u'las', u'el', u'y',]

def pincel_capitalize(cadena):
    cadena = cadena.strip()
    if type(cadena) is not unicode:
        cadena = cadena.decode('utf-8')
    cad = ""
    cadenas = [c.lower() for c in cadena.split(' ')]
    cadenas = [c in NO_CAPITALIZE and c or c.capitalize() for c in cadenas]
    return u" ".join(cadenas)
            
def parser_msg(msg):
    """
        Despliega la format string
    """
    res = msg[0] % msg[1:]
    if type(res) is str:
        return res.decode('utf-8')
    elif type(res) is unicode:
        return res
    else:
        #log.warn("Presentando %s de tipo %s", msg, type(res))
        return res
    #result = msg[0]
    #for m in msg[1:]:
    #    result = result.replace('%s',str(m),1)
    #return str(result)

def binary_search_curso_escolar_actual(rows, curso_escolar_actual):

    def binary_search(a, x, lo=0, hi=None):
        if hi is None:
            hi = len(a)
        while lo < hi:
            mid = (lo+hi)//2
            midval = int(a[mid]['CURSO_ESCO'])
            if midval == x:
                if mid - 1 < 0 or int(a[mid-1]['CURSO_ESCO']) < x:
                    return mid
            if midval < x:
                lo = mid+1
            else: 
                hi = mid
        return -1

    return binary_search(rows, int(curso_escolar_actual))

class Importer:

    def __init__(self, data_dir, database = None, repository=None):
        self.data_path = data_dir
        self.repo = repository or DataRepo()
        self.db = database or Dbf()
        dates = self.repo.find_data_dates()
        self.actualizaciones = 0
        self.errores = 0
        self.novedades = 0
        self.ticker_models = []
        self.log_result = self.log_warn = self.log_debug = self.log_error = u""
        try:
            self.last_date = dates[0]
        except IndexError:
            return        
        try:
            self.previous_date = dates[1]
        except IndexError:
            self.previous_date = None
            
    def debug(self, *msg):
        m = parser_msg(msg)
        if type(m) is str: m = m.decode('utf-8')
        log.debug(m)
        self.log_debug += u'%s\n' % m

    def warn(self, *msg):
        m = parser_msg(msg)
        if type(m) is str: m = m.decode('utf-8')
        log.warn(m)
        self.log_warn += u'%s\n' % m        
        self.log_result += u'%s\n' % m

    def info(self, *msg):
        m = parser_msg(msg)
        if type(m) is str: m = m.decode('utf-8')
        log.info(m)
        self.log_result += u'%s\n' % m

    def error(self, *msg):
        m = parser_msg(msg)
        if type(m) is str: m = m.decode('utf-8')
        log.error(m)
        self.log_error += u'%s\n' % m        
        self.log_result += u'%s\n' % m
        
    def _recode_tildes (self, s):
        """
            Controla particularidades de la codificación de strings
        """
        try:
            s = s.replace('É', 'é').replace('Í', 'í').replace('Ó', 'ó').replace('Ú', 'ú')
            s = s.replace('Ü', 'ü').replace('Ñ', 'ñ').replace('Á', 'á')
        except AttributeError:
            pass
        return s

    def _recode_string(self, s):
        """
            Controla particularidades de la codificación de strings
        """
        try:
            s = s.decode('latin-1').encode('utf-8')
            s = self._recode_tildes(s)
        except AttributeError, e:
            self.error(u"Error en recode_string: %s %s" % (type(s), repr(s)))
            raise(e)
        return s
    
    def _getPrettyName(self, list, row):
        """
            Dada una lista de keys asociadas, devuelve un string concatenando
            el contenido de ambas.
        """
        row_str = ''
        for field in list:
            try:
                row_str += '%s ' % self._recode_string(row[field])
            except TypeError:
                row_str += '%s ' % (row[field],)
        return row_str.strip()

    def _checkMovil(self, movil):
        #TODO: Revisar esto con calma
        if not movil:
            return ""
        if re.compile("^6[0-9]{8}$").match(str(movil)) is None:
            self.debug("%s no es un teléfono móvil válido", str(movil))
            return ""
        else:
            return movil
        
    def _process_needded(self, table, excel = False, curso_escolar_actual = False):
        """
            Por un lado carga el fichero asociado a la tabla requerida. Por otro
            hace las averiguaciones para confirmar si se tiene que procesar esta tabla o no.
        """
        template = '%s.dbf'
        if excel:
            template = '%s.xls'
        table_filename = template % table.lower()
        if not self.repo.file_is_modified(self.previous_date, self.last_date, table_filename):
            self.info("* El fichero no ha cambiado desde la última vez: %s", table_filename)
            return False
        if excel:
            self.db = gxls.getDict(self.repo.build_data_path(self.last_date, table_filename))
        else:
            self.db = readDbf(self.repo.build_data_path(self.last_date, table_filename))
            if curso_escolar_actual:
                "Solo retornamos las filas que se ajustan al curso escolar actual"
                frontera = binary_search_curso_escolar_actual(self.db, settings.CURSO_ESCOLAR_ACTUAL)
                self.db = self.db[frontera:]
            
        if not len(self.db):
            self.error("No existen %s en la base de datos", table)
            return False
        return True

    def _import_simple_data(self, table, model, codigo):
        """
            Obtiene los datos de una tabla y los pasa al modelo correspondiente.
            La clave primaria de la tabla se espera que sea CODIGO_INT, de
            no ser así utilizar el argumento nombreid para especificarlo.
        """
        if not self._process_needded(table): return
        self.info(" * Procesando datos de la tabla: %s", table)
        for row in self.db:
            self.debug("=> Procesando: %s", self._getPrettyName((codigo, 'DEN_CORTA', 'DEN_LARGA'), row))
            obj, created = self.get_or_create(model, idPincel=self._recode_string(row[codigo]))
            obj.nombreCorto = self._recode_string(row['DEN_CORTA'])
            obj.nombreLargo = self._recode_string(row['DEN_LARGA'])
            obj.save()
            if created:
                self.novedades += 1
                self.debug("...creado")
            else:
                self.actualizaciones += 1
                self.debug("...actualizado")
        self._print_stats()

    def _get_pais(self, pais):
        try:
            return Pais.objects.get(idPincel = pais).nombreLargo
        except Pais.DoesNotExist:
            return None

    def _import_personal_data(self, obj, row, tr_map):
        """
            Crea los modelos con los datos asociadas a personas.
        """
        if obj.id:
            p = obj.persona
        else:
            if tr_map.has_key('perfil'):
                p = PersonaPerfil()            
            else:
                p = Persona()
        if tr_map.has_key('nombre'):
            p.nombre = pincel_capitalize(self._recode_string(row[tr_map['nombre']]))
        if tr_map.has_key('apellidos'):
            p.apellidos = pincel_capitalize(self._recode_string(row[tr_map['apellidos']]))
        if tr_map.has_key('sexo'):
            p.sexo = row[tr_map['sexo']] == 'T'
        if tr_map.has_key('documento_identificacion'):
            p.documento_identificacion = row[tr_map['documento_identificacion']].strip()
        if tr_map.has_key('fecha_nacimiento'):
            fecha = row[tr_map['fecha_nacimiento']]
            if not fecha:
                p.fecha_nacimiento = None
            else:
                p.fecha_nacimiento = datetime.datetime(int(fecha[:4]), int(fecha[4:6]), int(fecha[6:]))
        if tr_map.has_key('lugar_nacimiento'):
            p.lugar_nacimiento = self._get_pais(row[tr_map['lugar_nacimiento']])
        if tr_map.has_key('nacionalidad'):
            p.nacionalidad = self._get_pais(row[tr_map['nacionalidad']])
        p.tipo_documento_identificacion = DNI
        #TODO: comprobar si hay una excepción
        p.save()

        d, created = self.get_or_create(Direccion, persona=p, tipo=D_PERSONAL)
        if tr_map.has_key('pais'):
            d.pais = self._get_pais(row[tr_map['pais']])
        if tr_map.has_key('provincia'):
            try:
                d.provincia = Provincia.objects.get(idPincel = row[tr_map['provincia']]).nombreLargo
            except Provincia.DoesNotExist:
                d.provincia = None
        if tr_map.has_key('poblacion'):
            d.poblacion = self._recode_string(row[tr_map['poblacion']])
        if tr_map.has_key('codPostal'):
            d.codPostal = self._recode_string(row[tr_map['codPostal']])
        if tr_map.has_key('direccion'):
            d.direccion = self._recode_string(row[tr_map['direccion']])
        d.save()
        if tr_map.has_key('telefono'):
            movil = self._checkMovil(row[tr_map['telefono']])
            if movil:
                contacto, created = self.get_or_create(Contacto, persona=p, tipo=M_PERSONAL)
                padre = isPadre(p)
                if padre and contacto.dato != movil and padre.verificado:
                    self.info(u"Cambio de teléfono móvil validado: %s (%s -> %s). Eliminando la validación" %
                        (padre, contacto.dato, movil))
                    padre.verificado = None
                    padre.save()
                contacto.dato = movil
                contacto.save()
        if tr_map.has_key('email'):
            #FIXME: check email.
            if row[tr_map['email']]:
                contacto, created = self.get_or_create(Contacto, persona=p, tipo=EM_PERSONAL)
                contacto.dato = self._recode_string(row[tr_map['email']])
                contacto.save()
        obj.persona = p

    def _update_stats(self, error_datos, created, fullPrettyName):
        if error_datos:
            self.error('Faltaron datos críticos, o eran incorrectos, para: %s' % fullPrettyName)
            self.errores += 1
            return
        if created:
            self.novedades += 1
            self.debug("...creado")
        else:
            self.actualizaciones += 1
            self.debug("...actualizado")

    def _print_stats(self):
        self.info("    Errores: %d" % self.errores)
        self.info("    Nuevos elementos: %d" % self.novedades)
        self.info("    Actualizaciones: %d" % self.actualizaciones)

    def solo_curso_escolar_actual(func):
        def solo_curso_escolar_actual(self, row):
            if int(row['CURSO_ESCO']) == settings.CURSO_ESCOLAR_ACTUAL:
                return func(self, row)
            return False
        return solo_curso_escolar_actual

    def process_table(table, data_display, translator = None, excel = False, curso_escolar_actual = False):
        def wrap(f):
            def check(self, *args):
                #if translator and translator not in self.ticker_models:
                #    self.ticker_models.append(translator)
                if self._process_needded(table, curso_escolar_actual = curso_escolar_actual):
                    if translator and translator not in self.ticker_models:
                        self.ticker_models.append(translator)
                    self.info(" * Procesando datos de la tabla: %s" % table)
                    self.errores = self.actualizaciones = self.novedades = 0
                    for row in self.db:
                        fullPrettyName = self._getPrettyName(data_display, row)
                        self.debug("=> Procesando %s: %s", table, fullPrettyName)
                        try:
                            objetos = f(self, row)
                            if translator and objetos:
                                for obj in objetos:
                                    translator.set_processed(translator, obj) 
                        except Http404, e:
                            self.errores += 1
                            self.error("No existe alguno de los datos necesarios para la importacion de %s de la tabla %s [%s]" % (fullPrettyName, table, e))
                    self._print_stats()
            return check
        return wrap

    def get_or_create(self, model, **kwargs):
        try:
            obj = model.objects.get(**kwargs)
            created = False
            self.actualizaciones += 1
        except model.DoesNotExist:
            # Los argumentos con __ sólo son válidos para búsquedas
            for key in kwargs.keys():
                if key.find('__') != -1:
                    del kwargs[key]
            obj = model(**kwargs)
            created = True
            self.novedades += 1
        return obj, created

    def get_or_create_or(self, model, **kwargs):
        """
            Hace una búsqueda con un or de todos los kwargs. Si no está lo crea.
        """
        q = Q()
        for k,v in kwargs.items():
            d = dict(((k, v),))
            # FIXME:
            # NO ENTIENDO POR QUE ES UN OR, ESTO
            # DA COMO RESULTADO EL TUTOR ANTIGUO
            # q |= Q(**d)
            q &= Q(**d)
        try:
            obj = model.objects.get(q)
            created = False
            self.actualizaciones += 1
        except model.DoesNotExist:
            # Los argumentos con __ sólo son válidos para búsquedas
            for key in kwargs.keys():
                if key.find('__') != -1:
                    del kwargs[key]
            obj = model(**kwargs)
            created = True
            self.novedades += 1
        except model.MultipleObjectsReturned:
            obj = model.objects.filter(q)
            self.warn("Multiple: %s, %s" % (repr(obj), kwargs))
            created = False
        return obj, created

    def get_from_translate_model(self, model, raise404=True, **kwargs):
        try:
            obj = model.objects.get(**kwargs).akademic
            return obj
        except model.DoesNotExist:
            if raise404:
                raise Http404
            return None

    @process_table('asignas', ('CODIGO', 'DEN_CORTA','DEN_LARGA'))
    def _import_asignaturas(self, row):
        """
            Importa las asignaturas.
        """
        asigna, created = self.get_or_create(Asignatura, metaAsignatura=False,
                abreviatura=self._recode_string(row['CODIGO']),
                nombreCorto=self._recode_string(row['DEN_CORTA']),
                nombreLargo=self._recode_string(row['DEN_LARGA'])
            )
        asigna.save()
        return (asigna,)

    @process_table('niveles', ('NIVEL', 'CURSO_ESCO'), curso_escolar_actual = True)
    def _import_niveles(self, row):
        """
            Importa los niveles.
        """
        nivel, created = self.get_or_create(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        nivel.save()
        return (nivel,)

    @process_table('grupos', ('NIVEL','CICLO', 'CURSO_ESCO'), curso_escolar_actual = True)
    def _import_ciclos(self, row):
        """
            Importa los ciclos de la tabla grupos.
        """
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo, created = self.get_or_create(Ciclo, nombre=row['CICLO'], nivel = nivel)
        ciclo.save()
        return (ciclo,)

    @process_table('grupos', ('NIVEL', 'CICLO', 'CURSO', 'CURSO_ESCO'), curso_escolar_actual = True)
    def _import_cursos(self, row):
        """
            Importa los cursos de la tabla grupos.
        """
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo = get_object_or_404(Ciclo, nombre=row['CICLO'], nivel=nivel)
        nombre = row['CURSO']
        if row['NIVEL'] == 'INF':
            nombre = str(int(nombre) - 1)
        curso, created = self.get_or_create(Curso, nombre=nombre, ciclo=ciclo)
        curso.save()
        if created:
            pdc, created = GrupoAula.objects.get_or_create(curso=curso, seccion='PDC')
            return (curso, pdc)
        return (curso,)

    @process_table('grupos', ('NIVEL', 'CICLO', 'CURSO', 'GRUPO', 'CURSO_ESCO'), curso_escolar_actual = True)
    def _import_grupo_aula(self, row):
        """
            Importa los grupo_aula de la tabla grupos.
        """
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo = get_object_or_404(Ciclo, nombre=row['CICLO'], nivel=nivel)
        nombre = row['CURSO']
        if row['NIVEL'] == 'INF':
            nombre = str(int(nombre) - 1)
        curso = get_object_or_404(Curso, nombre=nombre, ciclo=ciclo)
        grupo_aula, created = self.get_or_create(GrupoAula, seccion=row['GRUPO'], curso=curso)
        grupo_aula.save()
        return (grupo_aula,)

    @process_table('evaluaci', ('CURSO_ESCO', 'EVALUACION', 'FECHA'), curso_escolar_actual = True)
    def _import_evaluaciones(self, row):
        """
            Importa las evaluaciones.
        """
        evaluacion, created = self.get_or_create(Evaluacion, cursoEscolar=row['CURSO_ESCO'], nombre=row['EVALUACION'])
        evaluacion.save()
        return (evaluacion,)

    @process_table('matri', ('REGISTRO', 'CURSO_ESCO', 'NIVEL', 'CICLO', 'CURSO', 'GRUPO'), GrupoAulaAlumnoTicker, curso_escolar_actual = True)
    def _import_grupo_aula_alumno(self, row):
        """
            Importa las los grupoaula de los alumnos desde la tabla matri
        """
        alumno = get_object_or_404(TraductorAlumno, registro=row['REGISTRO']).akademic
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo = get_object_or_404(Ciclo, nombre=row['CICLO'], nivel=nivel)
        nombre = row['CURSO']
        if row['NIVEL'] == 'INF':
            nombre = str(int(nombre) - 1)
        curso = get_object_or_404(Curso, nombre=nombre, ciclo=ciclo)
        if row['COMEDOR'] == 'T':
            seccion = 'PDC'
            self.debug("**Es PDC")
        else:
            seccion = row['GRUPO']
        grupo_aula = get_object_or_404(GrupoAula, seccion=seccion, curso=curso)
        # No se crea directamente el GrupoAulaAlumno porque hay ocasiones en los que los datos
        # de Pincel se actualizan. En caso de cambios de Grupo, el GrupoAulaAlumno anterior
        # no se elimina hasta que finaliza la importación. Esto genera duplicados y hace
        # que fallen los GruposAulaAlumno.objects.get().
        grupo_aula_alumno, created = self.get_or_create(
                GrupoAulaAlumno, 
                alumno=alumno, 
                grupo__curso__ciclo__nivel__cursoEscolar = row['CURSO_ESCO'],
                grupo__seccion__in = ['A', 'B', 'C', 'PDC' ]
            )
        grupo_aula_alumno.grupo = grupo_aula
        grupo_aula_alumno.save()
        if row['NUM_LISTA']:    
            num_lista = int(row['NUM_LISTA'])
            if alumno.posicion != num_lista:
                alumno.posicion = num_lista    
                alumno.save()
        return (grupo_aula_alumno,)

    @process_table('tutorias', ('CURSO_ESCO', 'NIVEL', 'CICLO', 'CURSO', 'GRUPO', 'DNI'), TutorTicker, curso_escolar_actual = True)
    def _import_tutores(self, row):
        """
            Importa los tutores. Esta información no se encuentra en Pincel sino
            en la hoja de cálculo
        """
        self.error("Importando tutores de Pincel, esto no deberia pasar!!!")
        profesor = self.get_from_translate_model(TraductorProfesor, dni=row['DNI'].strip())
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo = get_object_or_404(Ciclo, nombre=row['CICLO'], nivel=nivel)
        nombre = row['CURSO']
        if row['NIVEL'] == 'INF':
            nombre = str(int(nombre) - 1)
        curso = get_object_or_404(Curso, nombre=nombre, ciclo=ciclo)
        tutor, created = self.get_or_create(Tutor, profesor=profesor)
        tutor.grupo = get_object_or_404(GrupoAula, seccion=row['GRUPO'], curso=curso)
        tutor.save()
        return (tutor,)

    def _import_excel_tutores(self, tutores, nivel):
        self.info(" * Importando tutores de nivel %s", nivel)
        if TutorTicker not in self.ticker_models:
            self.ticker_models.append(TutorTicker)
        for i in tutores:
            try:
                profesor = get_object_or_404(TraductorProfesor, dni = i[0].strip()).akademic
                self.debug("**Tutor: %s", profesor)
                #FIXME: Añadir el ciclo en el excel. 
                #ciclo = get_object_or_404(Ciclo, nombre = cilo?, nivel = nivel)
                nombre = str(i[2]).strip()
                if not nombre:
                    self.warn("El tutor no tiene tutorias definidas")
                    continue
                if nombre.endswith(".0"): # esto es 4.0 5.0 a veces
                    nombre = nombre[:-2]
                curso = get_object_or_404(Curso, nombre = nombre, ciclo__nivel = nivel)
                grupo = get_object_or_404(GrupoAula, curso = curso, seccion = i[3])
                tutor, created = self.get_or_create_or(Tutor, profesor = profesor, grupo = grupo)
                tutor.save()
                self.debug("*********************SE HA %s EL TUTOR %s del grupo %s y curso %s", "CREADO" if created else "USADO", profesor, grupo, curso)
                TutorTicker.set_processed(TutorTicker, tutor)
            except Http404, e:
                self.error("Importando tutor: %s (info = %s)" % (e, i))
                continue
                
    def _import_excel_coordinadores(self, coordinadores):
        self.info(" * Importanto Coordinadores de ciclo")
        if CoordinadorTicker not in self.ticker_models:
            self.ticker_models.append(CoordinadorTicker)
        for i in coordinadores:
            try:
                profesor = get_object_or_404(TraductorProfesor, dni = i[0].strip()).akademic
                self.debug("**Coordinador Ciclo: %s", profesor)
                nivel_name = str(i[2]).strip()
                ciclo_name = str(i[3]).strip()
                nivel = get_object_or_404(Nivel, nombre = nivel_name, cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL) 
                ciclo = get_object_or_404(Ciclo, nombre = ciclo_name, nivel = nivel)
                coordinador, created = self.get_or_create(CoordinadorCiclo, profesor = profesor, ciclo = ciclo)
                coordinador.save()
                CoordinadorTicker.set_processed(CoordinadorTicker, coordinador)
            except Http404, e:
                self.error("Importando coordinador de ciclo: %s (info = %s)" % (e, i))
                continue
                
    def _import_excel_jefes_estudios(self, jefes_estudios):
        self.info(" * Importanto Jefes de Estudio")
        if JefeEstudiosTicker not in self.ticker_models:
            self.ticker_models.append(JefeEstudiosTicker)
        for i in jefes_estudios:
            try:
                profesor = get_object_or_404(TraductorProfesor, dni = i[0].strip()).akademic
                self.debug("**Jefe Estudios: %s", profesor)
                nivel_name = str(i[2]).strip()
                nivel = get_object_or_404(Nivel, nombre = nivel_name, cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL) 
                jefe_estudios, created = self.get_or_create(JefeEstudios, profesor = profesor, nivel = nivel)
                jefe_estudios.save()
                JefeEstudiosTicker.set_processed(JefeEstudiosTicker, jefe_estudios)
            except Http404, e:
                self.error("Importando jefe de estudios: %s (info = %s)" % (e, i))
                continue

    @process_table('tutorias', ('CURSO_ESCO', 'NIVEL', 'CICLO', 'CURSO', 'GRUPO', 'DNI', 'DIA_1', 'HI_1'), TutoriaTicker, curso_escolar_actual = True)
    def _import_horario_tutorias(self, row):
        """
            Importa los horarios de tutorías.
        """
        profesor = self.get_from_translate_model(TraductorProfesor, dni=row['DNI'].strip())
        tutor = get_object_or_404(Tutor, profesor=profesor)
        hora = datetime.time(hour=int(row['HI_1'][:2]),minute=int(row['HI_1'][2:])) 
        tutoria, created = self.get_or_create(Tutoria, tutor=tutor, diaSemana=row['DIA_1'], maxCitas=3)
        tutoria.hora = hora
        tutoria.save()
        return (tutoria,)

    def _import_horas(self):
        self.info("Inicializando horas")
        HORAS = (
            {"inicio": datetime.time(8, 30), "fin": datetime.time(9, 30), "nivel": "PRI", "denom": "Prim.", "pincel": '1'},
            {"inicio": datetime.time(9,30), "fin": datetime.time(10,30), "nivel": "PRI", "denom": "Seg.", "pincel": '2'},
            {"inicio": datetime.time(10,30), "fin": datetime.time(11,30), "nivel": "PRI", "denom": "Terc.", "pincel": '3'},
            {"inicio": datetime.time(12,0), "fin": datetime.time(13,0), "nivel": "PRI", "denom": "Cuart.", "pincel": '4'},
            {"inicio": datetime.time(13,0), "fin": datetime.time(14,0), "nivel": "PRI", "denom": "Quint.", "pincel": '5'},
            {"inicio": datetime.time(8,0), "fin": datetime.time(8,55), "nivel": "ESO", "denom": "Prim.", "pincel": '1'},
            {"inicio": datetime.time(8,55), "fin": datetime.time(9,50), "nivel": "ESO", "denom": "Seg.", "pincel": '2'},
            {"inicio": datetime.time(9,50), "fin": datetime.time(10,45), "nivel": "ESO", "denom": "Terc.", "pincel": '3'},
            {"inicio": datetime.time(11,15), "fin": datetime.time(12,10), "nivel": "ESO", "denom": "Cuart.", "pincel": '4'},
            {"inicio": datetime.time(12,10), "fin": datetime.time(13,5), "nivel": "ESO", "denom": "Quint.", "pincel": '5'},
            {"inicio": datetime.time(13,5), "fin": datetime.time(14,0), "nivel": "ESO", "denom": "Sext.", "pincel": '6'},
            {"inicio": datetime.time(8,30), "fin": datetime.time(14,0), "nivel": "INF", "denom": "TINF", "pincel": '1'},
            {"inicio": datetime.time(8,30), "fin": datetime.time(14,0), "nivel": "PRI", "denom": "TPRI", "pincel": '1'},
        )

        for hora in HORAS:
            nivel = get_object_or_404(Nivel, nombre = hora['nivel'], cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
            hora_obj, created = Hora.objects.get_or_create(
                    horaInicio = hora['inicio'], horaFin = hora['fin'],
                    nivel = nivel, denominacion = hora['denom']
                )
            TraductorHora.objects.get_or_create( denominacion = hora['pincel'], nivel = nivel, akademic = hora_obj)

    @process_table('horario', ('CURSO_ESCO', 'NIVEL', 'CICLO', 'CURSO', 'GRUPO', 'HORA', 'DIA_SEMANA', 'AREA'),
        HorarioTicker, curso_escolar_actual = True)
    def _import_horario(self, row):
        """
            Importa los horarios de clase.
        """
        profesor = self.get_from_translate_model(TraductorProfesor, dni=row['DNI'].strip())
        nivel = get_object_or_404(Nivel, nombre=row['NIVEL'], cursoEscolar=row['CURSO_ESCO'])
        ciclo = get_object_or_404(Ciclo, nombre=row['CICLO'], nivel=nivel)
        nombre = row['CURSO']
        if row['NIVEL'] == 'INF':
            nombre = str(int(nombre) - 1)
        curso = get_object_or_404(Curso, nombre=nombre, ciclo=ciclo)
        grupo_aula = get_object_or_404(GrupoAula, seccion=row['GRUPO'], curso=curso)
        asignatura = get_object_or_404(Asignatura, abreviatura=row['AREA'])
        hora = self.get_from_translate_model(TraductorHora, denominacion=row['HORA'], nivel=nivel)
        horario, created = self.get_or_create(Horario,
            profesor = profesor,
            diaSemana = row['DIA_SEMANA'],
            hora= hora,
            asignatura = asignatura,
            grupo = grupo_aula)
        horario.save()
        return (horario,)

    def _getHora(self, cadena, nivel):
        values = cadena.split("-")
        try:
            horaInicio = datetime.time (* map(int, values[0].strip().split (":")))
            horaFin = datetime.time (* map(int, values[1].strip().split (":")))
        except ValueError, e:
            self.error('Error procesando la hora: %s (%s, %s)' % (e, cadena, nivel))
            raise Http404
        return get_object_or_404(Hora, horaInicio = horaInicio, horaFin = horaFin, nivel = nivel)

    def _gestionar_jornadas_continuas(self, grupos, variable=True):
        """
            En este caso profesor es un objeto.
            Esta función dará de alta el horario de los tutores de grupos con
            jornadas contínuas.
        """
        self.debug("Gestionando jornadas continuas para el grupo: %s", grupos)
        if len(grupos) != 1:
            return False
        grupo = grupos[0]
        nivel = grupo.curso.ciclo.nivel
        if grupo.curso.ciclo not in getCiclosJornadaContinua():
            return False
        try:
            profesor = Tutor.objects.get(grupo = grupo).profesor
        except Tutor.DoesNotExist:
            self.error("No existe tutor para el grupo %s." % grupo)
            return False
        except Tutor.MultipleObjectsReturned:
            self.error("Existen varios tutores para el grupo %s." % grupo)
            return False
        if HorarioTicker not in self.ticker_models:
            self.ticker_models.append(HorarioTicker)
        
        if variable and MatriculaTicker not in self.ticker_models:
            self.ticker_models.append(MatriculaTicker)
        nombreAsignatura = u"T.%s" % nivel.nombre
        abreviatura = nombreAsignatura[:3] # esto es asi
        asigna, created = Asignatura.objects.get_or_create( abreviatura = abreviatura,
                nombreCorto = nombreAsignatura, nombreLargo = nombreAsignatura)
        for gaa in GrupoAulaAlumno.objects.filter(grupo = grupo):
            matricula, created = Matricula.objects.get_or_create(grupo_aula_alumno = gaa, tipo = 'N', asignatura = asigna)
            if variable:
                MatriculaTicker.set_processed(MatriculaTicker, matricula)
        hora = get_object_or_404(Hora, denominacion = "T%s" % nivel.nombre, nivel = nivel)
        for dia in range(1,6):
            horario, created = Horario.objects.get_or_create(
                    hora = hora, diaSemana = dia, profesor = profesor,
                    asignatura = asigna, grupo = grupo
                )
            HorarioTicker.set_processed(HorarioTicker, horario)
        return True

    def _import_excel_horario(self, horarios, nivel, variable=True):
        """
            Nivel debe ser una cadena de entre "INF", "PRI" y "ESO"
        """
        self.info(" * Importando el horario para: %s..." % repr(horarios)[:50])
        if HorarioTicker not in self.ticker_models:
            self.ticker_models.append(HorarioTicker)
        DIAS = {}
        for i in OPCIONES_DIAS:
            DIAS[i[1].encode('utf-8')] = i[0]
        for i in horarios:
            try:
                if i[4].strip() == '':
                    self.debug("No se pudo crear el horario. Faltan datos en linea: '%s'" % i)
                    continue
                secciones = [s.strip() for s in i[6].upper().split("Y")]
                nombre = int(i[5])
                curso = get_object_or_404(Curso, nombre = str(nombre), ciclo__nivel = nivel)
                grupos = GrupoAula.objects.filter(curso = curso, seccion__in = secciones).order_by("seccion")
                if self._gestionar_jornadas_continuas(grupos, variable):
                    continue
                profesor = get_object_or_404(TraductorProfesor, dni = i[0]).akademic
                self.info("No se trata de un grupo de jornada continua")
                dia = DIAS[self._recode_tildes(i[2].encode('utf-8')).capitalize()]
                hora = self._getHora(i[3], nivel)
                asignatura = get_object_or_404(Asignatura, abreviatura = i[4].strip())
                for g in grupos:
                    horario, created = Horario.objects.get_or_create( hora = hora, diaSemana = dia,
                            profesor = profesor, asignatura = asignatura, grupo = g
                        )
                    HorarioTicker.set_processed(HorarioTicker, horario)
            except Http404, e:
                self.warn("No se pudo crear el horario en linea '%s'. Razon: %s" % (i, e))

    @process_table('area_alu', ('REGISTRO', 'NIVEL', 'CICLO', 'CURSO', 'CURSO_ESCO', 'AREA'), MatriculaTicker, curso_escolar_actual = True)
    def _import_matricula(self, row):
        """
            Importa las matriculas de los alumnos.
        """
        alumno = get_object_or_404(TraductorAlumno, registro=row['REGISTRO']).akademic
        if row['TIPO'] == 'P': # Asignatura pendiente de otro grupoaula
            curso = get_object_or_404(Curso,nombre=row['CURSO'], ciclo__nombre=row['CICLO'], ciclo__nivel__cursoEscolar = row['CURSO_ESCO'])
            grupo_pendiente, created = GrupoAula.objects.get_or_create(curso=curso, seccion='Pendientes')
            if created:
                grupo_pendiente.save()
            grupo_aula_alumno, created = self.get_or_create(
                    GrupoAulaAlumno,
                    alumno=alumno,
                    grupo__curso__ciclo__nivel__cursoEscolar = row['CURSO_ESCO'],
                    grupo=grupo_pendiente
                )
            if created:
                grupo_aula_alumno.save()
        else:
            grupo_aula_alumno = get_object_or_404(
                    GrupoAulaAlumno,
                    Q(alumno=alumno) &
                    Q(grupo__curso__ciclo__nivel__cursoEscolar=row['CURSO_ESCO']) &
                    ~Q(grupo__seccion = 'Pendientes')
                )

        asignatura = get_object_or_404(Asignatura, abreviatura=row['AREA'])
        matricula, created = self.get_or_create(Matricula,
                grupo_aula_alumno=grupo_aula_alumno, asignatura=asignatura, tipo=row['TIPO'])
        matricula.save()
        return (matricula,)

    @process_table('centros', ('CODIGO', 'DEN_LARGA'))
    def _import_centros(self, row):
        """
            Importa los centros escolares de toda canarias ?¿?¿?
        """
        row['LISLA'] = self._recode_string(row['LISLA'])
        if ISLA_TRANSLATOR.has_key(row['LISLA']):
            row['LISLA'] = ISLA_TRANSLATOR[row['LISLA']]
        isla = get_object_or_404(Isla, nombreLargo__iexact=row['LISLA'])
        row['LMUNICI'] = self._recode_string(row['LMUNICI'])
        if MUNICIPIO_TRANSLATOR.has_key(row['LMUNICI']):
            row['LMUNICI'] = MUNICIPIO_TRANSLATOR[row['LMUNICI']]
        municipio = get_object_or_404(Municipio, nombreLargo__iexact=row['LMUNICI'])
        centro, created = self.get_or_create(Centro,
                idPincel = row['CODIGO'],
                isla = isla, 
                nombre = self._recode_string(row['DEN_LARGA']),
                domicilio = self._recode_string(row['DOMICILIO']),
                localidad = self._recode_string(row['LOCALIDAD']),
                municipio = municipio
            )
        centro.save()
        return (centro,)


    @process_table('alumnos', ('NOMBRE', 'APELLIDOS', 'REGISTRO'), TraductorAlumno)
    def _import_alumnos(self, row):
        try:
            alumno = self.get_from_translate_model(TraductorAlumno, registro=row['REGISTRO'])
            store_translate = False
            self.actualizaciones += 1
        except Http404:
            alumno = Alumno()
            store_translate = True
            self.novedades += 1
        alumno.padre = self.get_from_translate_model(TraductorPadre, False, dni=row['DNI_PADRE'].strip())
        alumno.madre = self.get_from_translate_model(TraductorPadre, False, dni=row['DNI_MADRE'].strip())
        alumno.cial = row['CIAL']
        alumno.potestadMadre = row['MADREPOTES'] == 'T'
        alumno.potestadPadre = row['PADREPOTES'] == 'T'
        persona_manager = { 
                'atributo':'persona', 'nombre': 'NOMBRE', 'apellidos': 'APELLIDOS',
                'sexo': 'SEXO', 'documento_identificacion': 'DNI', 'fecha_nacimiento': 'FECHA_NAC',
                'lugar_nacimiento': 'PAIS', 'nacionalidad': 'NACIONALID', 'direccion': 'DOMICILIO',
                'codPostal': 'COD_POSTAL', 'poblacion': 'LOCALIDAD', 'provincia': 'PROVINCIA',
                'pais': 'PAIS', 'telefono': 'TELEFONO', 'email': 'E_MAIL',
            }
        self._import_personal_data(alumno, row, persona_manager)
        alumno.save()
        if store_translate:
            TraductorAlumno(registro=row['REGISTRO'], akademic=alumno).save()
        return (alumno,)

    @process_table('docentes', ('NOMBRE', 'APELLIDOS', 'DNI'), TraductorProfesor)
    def _import_profesores(self, row):
        try:
            profesor = self.get_from_translate_model(TraductorProfesor, dni=row['DNI'].strip())
            store_translate = False
            self.actualizaciones += 1
        except Http404:
            profesor = Profesor()
            store_translate = True
            self.novedades += 1
        persona_manager = { 
            'atributo':'persona', 'perfil': True, 'nombre': 'NOMBRE', 'apellidos': 'APELLIDOS', 'sexo': 'SEXO',
            'documento_identificacion': 'DNI', 'fecha_nacimiento': 'FECHA_NAC', 'domicilio': 'DOMICILIO',
            'provincia': 'PROVINCIA', 'poblacion': 'LOCALIDAD', 'codPostal': 'COD_POSTAL', 'telefono': 'TELEFONO',
            'email': 'E_MAIL',
            }
        self._import_personal_data(profesor, row, persona_manager)
        profesor.save()
        if store_translate:
            TraductorProfesor(dni=row['DNI'].strip(), akademic=profesor).save()
        return (profesor,)

    @process_table('padres', ('NOMBRE', 'APELLIDOS', 'DNI'), TraductorPadre)
    def _import_padres(self, row):
        try:
            padre = self.get_from_translate_model(TraductorPadre, dni=row['DNI'].strip())
            store_translate = False
            self.actualizaciones += 1
        except Http404:
            padre = Padre()
            store_translate = True
            self.novedades += 1
        padre.notificarSms = padre.notificarEmail = True
        if not padre.verificado:
            padre.verificado = None
        padre.difunto = row['DIFUNTO'] == 'T'
        persona_manager = { 
            'atributo':'persona', 'perfil': True, 'nombre': 'NOMBRE', 'apellidos': 'APELLIDOS', 'sexo': 'SEXO',
            'documento_identificacion': 'DNI', 'telefono': 'TELEFONO', 'email': 'E_MAIL',
            }
        self._import_personal_data(padre, row, persona_manager)
        padre.save()
        if store_translate:
            TraductorPadre(dni=row['DNI'], akademic=padre).save()
        return (padre,)

    @process_table('notas', ('CURSO_ESCO', 'REGISTRO', 'AREA', 'EVALUACION', 'NOTA', 'CURSO'), CalificacionTicker, curso_escolar_actual = True)
    def _import_calificaciones(self, row):
        """
            Importa las notas de los alumnos.
        """
        alumno = get_object_or_404(TraductorAlumno, registro=row['REGISTRO']).akademic
        asignatura = get_object_or_404(Asignatura, abreviatura = row['AREA'])
        grupo_aula_alumno = get_object_or_404(
                GrupoAulaAlumno,
                Q(alumno=alumno) &
                Q(grupo__curso__ciclo__nivel__cursoEscolar=row['CURSO_ESCO']) &
                ~Q(grupo__seccion = 'Pendientes')
            )
        evaluacion = get_object_or_404(Evaluacion, cursoEscolar = row['CURSO_ESCO'], nombre = row['EVALUACION'])
        if grupo_aula_alumno.grupo.curso.nombre == row['CURSO']:
            # Si el curso de la calificación es = al que está matriculado el alumno es una matrícula ordinaria
            matricula = get_object_or_404(Matricula, grupo_aula_alumno=grupo_aula_alumno, asignatura=asignatura, tipo='N')
#        elif str(row['NOTA']) != str('Pte.'):
        else:
            # Si no, es una nota de una asignatura pendiente
            grupo_aula_alumno = get_object_or_404(
                    GrupoAulaAlumno,
                    Q(alumno=alumno) &
                    Q(grupo__curso__ciclo__nivel__cursoEscolar=row['CURSO_ESCO']) &
                    Q(grupo__seccion = 'Pendientes') &
                    Q(grupo__curso__nombre = row['CURSO'])
                )
            matricula = get_object_or_404(Matricula, grupo_aula_alumno=grupo_aula_alumno, asignatura=asignatura, tipo='P')
            # FIXME: No se si esto sigue siendo necesario
            asignatura_pendiente, created = AsignaturasPendientes.objects.get_or_create(matricula = matricula)
            asignatura_pendiente.curso = "%s %s" % (row['CURSO'], grupo_aula_alumno.grupo.curso.ciclo.nivel.nombre)
            asignatura_pendiente.save()
#        else:
#            # Es una nota del intervalo 1º ESO: 3 -> [ [2|3]º ESO: Pte. ]+ -> [3|4]º ESO: ? ### La descartamos
#            return ()
        calificacion, created = self.get_or_create(Calificacion, matricula=matricula, evaluacion=evaluacion)
        calificacion.conceptos = self._recode_string(row['ITEM1'])
        calificacion.procedimientos = self._recode_string(row['ITEM2'])
        calificacion.actitud = self._recode_string(row['ITEM3'])
        calificacion.adaptacion = self._recode_string(row['ADAPTACION'])
        calificacion.nota = self._recode_string(row['NOTA'])
        calificacion.comentario = self._recode_string(row['OBSERVA'])
        calificacion.save()
        return (calificacion,)

    @process_table('informes', ('CURSO_ESCO', 'REGISTRO', 'EVALUACION'), CalificacionCompetenciaTicker, curso_escolar_actual = True)
    def _import_informe_competencias(self, row):
        """
            Importa las notas de los alumnos.
        """
        alumno = get_object_or_404(TraductorAlumno, registro=row['REGISTRO']).akademic
        evaluacion = get_object_or_404(Evaluacion, cursoEscolar = row['CURSO_ESCO'], nombre = row['EVALUACION'])
        competencia, created = self.get_or_create(CalificacionCompetencia, alumno=alumno, evaluacion=evaluacion)
        competencia.informeCompetencias = self._recode_string(row['INFORME'])
        competencia.promociona = self._recode_string(row['PROMOCIONA']) == 'T'
        competencia.codigo_promocion = self._recode_string(row['CODPROMO'])
        competencia.save()
        return (competencia,)

    def _import_excel_usuarios(self, usuarios):
        """
            Importa los usuarios desde el archivo Excel.
        """
        # No queremos borrar todavía a los usuarios que no existen en el excel...
        #if UsuarioTicker not in self.ticker_models:
        #    self.ticker_models.append(UsuarioTicker)
        for usuario in usuarios:
            try:
                profesor = get_object_or_404(TraductorProfesor, dni = usuario[0].strip()).akademic
                if profesor.persona.user:
                    user = profesor.persona.user
                else:
                    self.info(u"El usuario %s no existía, creando", usuario[2].decode('utf-8'))
                    user = User()
                user.username = usuario[2]
                user.set_password(usuario[3])
                user.is_staff = user.is_superuser = False
                user.is_active = True
                user.save()
                profesor.persona.user = user
                profesor.persona.save()
                UsuarioTicker.set_processed(UsuarioTicker, user)
            except Http404, e:
                self.info('%s: %s' % (usuario, e))

    def import_tabular_data(self):
        """
            Itera todas las tablas con datos tabulados estáticos y realiza el procesamiento
            adecuado para cada una de ellas.
        """
        for datos in GRUPO_DATOS_SIMPLES.values():            
            codigo = 'CODIGO_INT'
            if datos.has_key('codigo'):
                codigo = 'CODIGO'
            self._import_simple_data(datos['tablapincel'], datos['modelo'], codigo)
        #self._import_centros()
        
    def import_variable_data(self):
        self._import_niveles()
        self._import_ciclos()
        self._import_cursos()
        self._import_grupo_aula()
        self._import_asignaturas()
        self._import_profesores()
        #self._import_tutores()
        self._import_horario_tutorias()
        self._import_horas() # Información tabulada, hardcoded en el metodo.
        #self._import_horario()
        self._import_padres()
        self._import_alumnos()
        self._import_grupo_aula_alumno()
        self._import_matricula()
        self._import_evaluaciones()
        self._import_calificaciones()
        self._import_informe_competencias()

    def import_excel(self, variable=True):
        """
            Importa todos los datos del fichero excel con datos extra.
        """
        if self._process_needded ('datos_extra', excel = True):
            for nivel_str in ('ESO', 'PRI', 'INF'):
                try:
                    nivel = get_object_or_404(Nivel, nombre = nivel_str, cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
                except Http404, e:
                    continue
                self._import_excel_tutores(self.db["Tutores %s" % nivel_str], nivel)
                self._import_excel_horario(self.db[nivel_str], nivel, variable)
            self._import_excel_coordinadores(self.db["Coordinadores"])
            self._import_excel_jefes_estudios(self.db["Jefes Estudio"])
            self._import_excel_usuarios(self.db["Usuarios"])

    def delete_non_used_data(self, really_sure = False):
        """
            Eliminamos todo lo que no se ha importado.
        """
        for ticker in self.ticker_models:
            Traductor.clean_not_processed(ticker, really_sure)

