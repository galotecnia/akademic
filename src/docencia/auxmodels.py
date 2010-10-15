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
from django.db import models
from django.conf import settings

from utils.configUtils import *

from pincel.models import *
import locale
import datetime

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

# Modelos auxiliares para akademic2

# Constantes

FECHA_INICIO_CURSO = datetime.datetime.strptime(settings.INICIO_CURSO, '%d-%m-%Y')

FECHAS_EVALUACIONES = {}
FECHAS_PUBLICACION_BOLETINES = {} 
for i in range(4):
    if settings.EVALUACIONES[i]:
        FECHAS_EVALUACIONES[i] = datetime.datetime.strptime(settings.EVALUACIONES[i], '%d-%m-%Y')
    if settings.PUBLICACIONES[i]:
        FECHAS_PUBLICACION_BOLETINES[i] = datetime.datetime.strptime(settings.PUBLICACIONES[i], '%d-%m-%Y')

FECHA_FIN_CURSO = FECHA_INICIO_CURSO
for i in reversed(range(4)):
    if i in FECHAS_EVALUACIONES and FECHAS_EVALUACIONES[i]:
        FECHA_FIN_CURSO = FECHAS_EVALUACIONES[i]
        break


ERROR_NOTA_NO_NUMERICA = u"""Ha introducido una nota no numérica para el alumno: 
							%s %s la calificación de este alumno no se almacenará"""

ERROR_NOTA_MAYOR = 		u"""Ha introducido una nota mayor que 10 para el alumno: 
							%s %s la calificación de este alumno no se almacenará"""

ERROR_NOTA_MENOR = 		u"""Ha introducido una nota menor que 0 para el alumno: 
							%s %s la calificación de este alumno no se almacenará"""

TEXTO_COMPETENCIAS = (
	('No avanza lo suficiente en su adquisición', 'No avanza lo suficiente en su adquisición'),
	('Avanza lo suficiente en su adquisición', 'Avanza lo suficiente en su adquisición'),
)

NOMBRES_CORTOS_DIAS = ('L', 'M', 'X', 'J', 'V', 'S', 'D')
NOMBRES_LARGOS_DIAS = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')

# Es posible que esta lista esté mal. Quizás haya que cambiar las claves a
# enteros en vez de cadenas.
OPCIONES_MESES = (
	('01', 'Enero'),
	('02', 'Febrero'),
	('03', 'Marzo'),
	('04', 'Abril'),
	('05', 'Mayo'),
	('06', 'Junio'),
	('07', 'Julio'),
	('08', 'Agosto'),
	('09', 'Septiembre'),
	('10', 'Octubre'),
	('11', 'Noviembre'),
	('12', 'Diciembre')
)

OPCIONES_SEXO = (
	(True, 'Masculino'),
	(False, 'Femenino'),
)

#
# Grupos de cursos dentro de niveles. Por ejemplo, en primaria existe el primer
# ciclo de primaria y el segundo ciclo de primaria.
#

OPCIONES_CICLO = (
    ('1', 'Primero'),
    ('2', 'Segundo'),
    ('3', 'Tercero'),
    ('UNI', 'UNI'),
)

#DEPRECATING...
OPCIONES_LISTADOS = (
	('asistencia', 'Asistencia'),
	('retraso', 'Retraso'),
	('comportamiento', 'Comportamiento'),
	('tareas', 'Tareas'),
	('material', 'Material'),
)

OPCIONES_TIPOMATRICULA = (
	('N', 'Normal'),
	('P', 'Pendiente'),
	('C', 'Convalidada'),
	('M', 'Cambio modalidad Bachillerato'),
	('E', 'Exento'),
	('Q', 'Pendiente primaria'),
	('S', 'Pendiente ESO'),
	('R', 'Renuncia Ciclos Formativos')
)

# Horas de finalización de la jornada lectiva para los distintos niveles.
# No son exactas, pero sirven para generar el horario en el caso de las
# asignaturas de jornada completa.
HORA_FIN_INF = "14:00"
HORA_FIN_PRI = "14:00"
HORA_FIN_ESO = "14:00"

# El número de notificaciones que se mostrarán en cada página
# de la vista de estado de notificación.
NOTIFICACIONES_POR_PAGINA = 50

def alusort(x, y):
	"""
		Método para ordenar los alumnos correctamente. Como usa la misma
		implementación del COLLATE para es_ES.UTF-8 (de la libc) que PostgreSQL
		hemos tenido que hacer un truco: sustituimos los espacios por otro
		caracter. El 0 parece funcionar correctamente.
	"""
	alux = x['alumno']
	aluy = y['alumno']
	repl = lambda x: x.replace(u'Á', 'A').replace(u'É', 'E').replace(u'Í', 'I').replace(u'Ó', 'O').replace(u'Ú', 'U').replace(' ', '0')
	res = locale.strcoll(repl(alux.persona.apellidos), repl(aluy.persona.apellidos))
	if res != 0:
		return res
	res = locale.strcoll(repl(alux.persona.nombre), repl(aluy.persona.nombre))
	return res
#
#class Turno(models.Model):
#	"""
#		Define un turno. Un turno puede ser, por ejemplo, de mañana, de tarde,
#		etc.
#	"""
#	nombreCorto = models.CharField(max_length = 25)
#	nombreLargo = models.CharField(max_length = 50, blank = True)
#	
#	def __unicode__(self):
#		return self.nombreCorto
#
#	class Meta:
#		app_label = 'docencia'
#	
#class Aula(models.Model):
#	"""
#		Representa un Aula dentro de un centro escolar.
#	"""
#	nombreCorto = models.CharField(max_length = 25)
#	nombreLargo = models.CharField(max_length = 50, blank = True)
#
#	def __unicode__(self):
#		return self.nombreCorto
#
#	class Meta:
#		app_label = 'docencia'
#
def fechaInicioCursoActual():
	return datetime.date(CURSO_ESCOLAR_ACTUAL,8,15)

def fechaFinCursoActual():
	return datetime.date(CURSO_ESCOLAR_ACTUAL+1,8,14)

def getNameFromTuple(tuple, index):
    """
        Given a number from a list of tuples, get the name associated to such number
        Useful for choice list's tuples.
    """
    for row in tuple:
        if row[0] is int(index):
            return row[1]
    else:
        return None
