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
from django.db.models import Q
import time, calendar, datetime, os, sys
from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings
from xlwt import *

from auxmodels import *

from akademicLog import *
from docencia.dateFunctions import *
from pincel.models import *
from addressbook.models import Persona, PersonaPerfil
from notificacion.constants import ESTADO_NOTIFICACION
from notificacion.models import Comentario
from docencia.auxmodels import FECHA_INICIO_CURSO, FECHAS_EVALUACIONES 
from docencia.faltas.models import Falta, Ausencia, Parte, Uniforme
from docencia.horarios.models import Hora, Horario
from docencia.notas.models import Competencia, Evaluacion, CalificacionCompetencia, Calificacion

from docencia.constants import *

import datetime
import time
import calendar

logger = AkademicLog().logger

# Factor de ponderacion de faltas
POND_FACTOR = {'ESO': 6, 'PRI': 5, 'INF': 1}

diccionario = {
    'faltas' : (
               ('falta', FALTA_ASISTENCIA),
               ('retraso', RETRASO),
               ),
    'comportamiento': (
                       ('comportamiento', FALTA_COMPORTAMIENTO),
                       ('tarea', FALTA_TAREA), 
                       ('material', FALTA_MATERIAL),
                       ),
}  

tipos_faltas = {'falta': FALTA_ASISTENCIA,
                'retraso': RETRASO,
                'comportamiento': FALTA_COMPORTAMIENTO,
                'tarea': FALTA_TAREA,
                'material': FALTA_MATERIAL,
               } 

class Alumno(models.Model):
    """
        Define los datos relativos a un alumno.
    """
    # Características particulares de los alumnos    
    cial = models.CharField(max_length=14, blank=True, null=True) # Este lo vamos a dejar porque lo usamos en los boletines
    padre = models.ForeignKey('padres.Padre', blank = True, null = True, related_name = "padre_hijos")
    madre = models.ForeignKey('padres.Padre', blank = True, null = True, related_name = "madre_hijos")
    potestadPadre = models.BooleanField('Patria potestad del padre')
    potestadMadre = models.BooleanField('Patria potestad de la madre')
    persona = models.OneToOneField(Persona)
    posicion = models.IntegerField(null=True, blank = True)

    def __unicode__(self):
        return u"%s %s" % (self.persona.nombre, self.persona.apellidos)

    class Meta:
        ordering = ['persona',]        
        verbose_name = 'Alumno'

    @staticmethod
    def filter(**kwargs):
        filtro = Q()
        for k,v in kwargs.items():
            filtro = filtro & Q(**{k:v})
        if settings.ORDENAR_POR_NUMERO_LISTA:
            return Alumno.objects.filter(filtro).order_by('posicion', 'persona__apellidos', 'persona__nombre')
        return Alumno.objects.filter(filtro).order_by('persona__apellidos', 'persona__nombre')

    def getAusencia (self):
        """
            Si el alumno está ausente devuelv la ausencia, si no devuelve None
        """
        try:
            return Ausencia.objects.get (alumno = self, fin__isnull = True)
        except Ausencia.DoesNotExist:
            return None

    def getUniforme(self, fecha = None):
        """
            Si el alumno tiene falta de uniforme devuelve la falta, si no None
        """
        if not fecha:
            fecha = datetime.date.today()
        try:
            return Uniforme.objects.get(alumno = self, dia = fecha)
        except Uniforme.DoesNotExist:
            return None

    def estadoAusencia (self):
        """
            Devuelve True si el alumno está ausente (sea la por lo que sea) y False
            si no lo está
        """
        return self.getAusencia() is not None

    def estadoUniforme(self, fecha = None):
        return self.getUniforme(fecha) is not None

    def setAusencia(self, ausentar = True, fecha = None):
        """
            setea o no una ausencia si estado es True pone el alumno ausente.
            Si está a False lo saca.
        """
        if not fecha:
            fecha = datetime.datetime.now()
        ausente = self.getAusencia ()
        if ausentar and not ausente:
                ausencia, created = Ausencia.objects.get_or_create(alumno = self, inicio = fecha)
                ausencia.fin = None
                ausencia.save()
        if not ausentar and ausente:
            ausente.finaliza ()
    
    def setUniforme(self, fecha = None):
        """
            Setea una falta por uniforme
        """
        if not fecha:
            fecha = datetime.date.today()
        if not self.estadoUniforme(fecha):
            falta = Uniforme.objects.create(alumno = self, dia = fecha)
    
    def delUniforme(self, fecha = None):
        """
            Elimina una falta por uniforme
        """
        if not fecha:
            fecha = datetime.date.today()
        try:
            u = Uniforme.objects.get(alumno = self, dia = fecha)
            u.delete()
        except Uniforme.DoesNotExist:
            # No deberia de ocurrir, no se puede quitar una falta de uniforme que no exista
            pass

    def horario_tutorias(self):
        """
            Permite a los padres consultar el horario de tutorias de sus hijos
        """
        from docencia.tutoria.models import Tutoria, Cita
        tutor = self.getTutor()
        dict = {}
        dict['hijo'] = self
        dict['tutor'] = tutor

        # Obtenemos las posibles tutorias para el tutor
        tut = Tutoria.objects.filter(tutor = tutor).order_by('diaSemana')
        if len(tut) == 0:
            # Si no tiene tutorias definidas se trata en el template
            return dict

        # Rellenamos el diccionario de fechas con posibles tutorías hasta un máximo de
        # settings.MAXIMO_NUMERO_CITAS_PARA_TUTORIA
        aux_date = datetime.datetime.now()
        dict['fechas'] = []
        while len(dict['fechas']) < settings.MAXIMO_NUMERO_CITAS_PARA_TUTORIA:
            for t in tut:
                # Comprobamos si para esta semana todavía podemos elegir alguna cita. Para la 2ª y siguientes
                # iteraciones las comprobaciones son superfluas porque siempre estamos en lunes por lo 
                # que siempre podremos utilizar cualquier tutoría independientemente del día de la semana y 
                # hora
                if t.diaSemana > aux_date.weekday()+1 or (t.diaSemana == aux_date.weekday()+1 and t.hora > aux_date.time()):
                    fecha = datetime.datetime(aux_date.year, aux_date.month, aux_date.day, t.hora.hour, t.hora.minute, 0)
                    fecha += datetime.timedelta(t.diaSemana - aux_date.weekday() - 1)
                    try:
                        c = Cita.objects.get(tutoria = t, fecha = fecha, alumno = self)
                        continue
                    except Cita.DoesNotExist:
                        dict['fechas'].append( {
                            'fecha': fecha,
                            'tutoria': t,
                            'full': t.full(fecha),
                            'fechaHuman': fecha.strftime("%a %d"),
                        })
            # Nos movemos al lunes de la siguiente semana a medianoche
            aux_date += datetime.timedelta(7 - aux_date.weekday())
            aux_date = aux_date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        return dict

    def getFaltas(self, tipo=FALTA_ASISTENCIA):
        return Falta.objects.filter(alumno=self, tipo=tipo)

    def getFaltasAsignatura(self, asignatura, fechaini=None, fechafin=None, 
                            totales=None, tipo=FALTA_ASISTENCIA):    
        """
            Devuelve todas las faltas de asistencia que ha tenido un
            alumno en una asignatura. El rango de fechas es opcional.
            Si se especifica deben especificarse los dos límites.
            El último parámetro indica si queremos la lista detallada o solo los
            totales de faltas en esa asignatura. La primera opción sería la indicada
            para hacer un informe y la segunda para un resumen

            IMPORTANTE 18/01/2009: Dados unos errores relativos a excepciones 
            al crear el objeto datetime, hemos añadido una etapa 
            de normalización de las fechas.
        """
        # Obtenemos todas las faltas del alumno filtradas por asignatura
        faltas = self.getFaltas(tipo).filter(asignatura = asignatura)
        # Si hemos especificado los dos límites del rango de fechas filtramos.
        if fechaini and fechafin:
            faltas = faltas.filter(fecha__gte = fechaini, fecha__lte = fechafin)
        if totales:
            return len(faltas)
        return faltas
    
    def getTotalDiarioFaltas(self, fechaInicio, fechaFin, tipo = FALTA_ASISTENCIA):
        """
            Devuelve el total diario de faltas de asistencia que ha tenido un alumno en
            todas las clases a las que debe asistir, para el mes seleccionado.
            Devuelve un diccionario con el total de faltas de asistencia que se ha
            protagonizado el alumno cada día del rango de fechas, el alumno en
            cuestión y el total mensual.
        """
        (anyoI, mesI, diaI) = fechaInicio.split('-')
        (anyoF, mesF, diaF) = fechaFin.split('-')
        fechaI = normalizarFecha(int(anyoI), int(mesI), int(diaI))
        fechaF = normalizarFecha(int(anyoF), int(mesF), int(diaF))
        faltas = self.getFaltas(tipo)
        dias = []
        total = 0
        while fechaI <= fechaF:
            dia = faltas.filter(fecha = fechaI).count()
            dias.append(dia)
            total += dia
            fechaI += datetime.timedelta(days = 1)
        return dict(alumno = self, faltas = dias, total = total)

    def getAsignaturas(self, tipo = 'N'):
        """
            Devuelve un listado de las asignaturas en las que está matriculado
            el alumno.
        """
        return Asignatura.objects.filter(
            matricula__grupo_aula_alumno__alumno = self, 
            matricula__grupo_aula_alumno__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL,
            matricula__tipo = tipo
        ).distinct()

    def getNotaAsignaturaPendiente(self, asignatura, curso):
        """
            Devuelve la nota de la asignatura pendiente
        """
        try:
            m = Matricula.objects.get(grupo_aula_alumno__alumno = self, 
                grupo_aula_alumno__grupo__curso = curso,
                tipo = 'P', 
                asignatura = asignatura)
        except Matricula.DoesNotExist:
            return '?'
        for nombre in [u'U', u'O', u'2', u'1']:
            c = m.calificacion_set.filter(evaluacion__nombre = nombre)
            if c:
                return c[0].nota
        return '?'

    def getCursoAsignaturaPendiente(self, asignatura):
        """
            Devuelve los cursos de la asignatura pendiente    
        """
        return Curso.objects.filter(
                grupoaula__grupoaulaalumno__alumno = self,
                grupoaula__grupoaulaalumno__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL,
                grupoaula__grupoaulaalumno__matricula__tipo = 'P',
                grupoaula__grupoaulaalumno__matricula__asignatura = asignatura
            )
#        try:
#            m = Matricula.objects.get(grupo_aula_alumno__alumno = self, 
#                grupo_aula_alumno__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL,
#                tipo = 'P', 
#                asignatura = asignatura)
#        except Matricula.DoesNotExist:
#            return ''
#        cursos = m.asignaturaspendientes_set.all()
#        if cursos:
#            return cursos[0].curso
#        return ''

    def getAsignaturasPendientes(self):
        """
            Devuelve un listado de las asignaturas pendientes del alumno.
        """
        return self.getAsignaturas(tipo = 'P')


    def getResumenTutor(self, fechaini = None, fechafin = None, generarResumen = True):
        """
        Devuelve el resumen de incidencias que ha cometido este alumno
        en el intervalo de fechas que se indica. Si no se indicase
        generaría el resumen de todas las incidencias protagonizadas
        por el alumno.
        
        El último argumento se ha añadido porque un resumen de tutor
        solicita prácticamente la misma información que un informe de tutor
        y no tiene sentido duplicar código. De esta manera si el valor
        del argumento es True, se generará un resumen de tutor, mientras
        que si el argumento es False, se generará un informe de tutor.
        
        El formato de salida de este método será un diccionario
        con el siguiente contenido:
        {
            "asignaturas": [
                {'asignatura': asignatura,
                'faltas': faltas,
                'retrasos': retrasos,
                .
                .
                .
                }
            ]
            "totalFaltas": 1000,
            "totalRetrasos": 2459,
            .
            .
            .
        }
        En cada diccionario tambien obtendremos el total de faltas de cada tipo
        con claves en este formato: "totalFaltas", "totalRetrasos", ...
        """
    # FIXME: Esto debe estar en el modelo tutor.
        resumen = {}
        asignaturas = []
        total = {'faltas': 0, 'retrasos': 0, 'comportamiento': 0, 'tarea': 0, 'material': 0}
        indices = {'faltas': FALTA_ASISTENCIA, 'retrasos': RETRASO, 'comportamiento': FALTA_COMPORTAMIENTO, 'tarea': FALTA_TAREA, 'material': FALTA_MATERIAL}
        for asig in self.getAsignaturas():
            aux = {}
            aux['asignatura'] = asig
            for k,v in indices.items():
                aux[k] = self.getFaltasAsignatura(asig, fechaini, fechafin, generarResumen, v)
                if generarResumen:
                    total[k] += aux[k]
                else:
                    total[k] += len(aux[k])
            asignaturas.append(aux)
        resumen['asignaturas'] = asignaturas
        resumen['totalFaltas'] = total['faltas']
        resumen['totalRetrasos'] = total['retrasos']
        resumen['totalComportamiento'] = total['comportamiento']
        resumen['totalTarea'] = total['tarea']
        resumen['totalMaterial'] = total['material']
        return resumen

    def getGrupo (self):
        """
            Devuelve el grupo del curso actual del alumno
        """
        return self.grupoaulaalumno_set.get(
                Q(grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL) &
                ~Q(grupo__seccion = 'Pendientes')
            )

    def getTutor(self):
        """
            Devuelve el tutor del alumno del curso actual
        """
        from docencia.tutoria.models import Tutor
        try:
            return Tutor.objects.get(grupo = self.getGrupo().grupo)
        except Tutor.DoesNotExist:
            logger.error('El alumno %s no tiene tutor', self)
            return None
        except MultipleObjectsReturned:
            logger.error('El alumno %s tiene mas de un tutor', self)
            return Tutor.objects.filter(grupo = self.getGrupo().grupo)[0]

    def getComentarios(self):
        """
            Devuelve una lista de comentarios para este alumno
        """
        return Comentario.objects.filter(alumno = self.id)
    
    def getCalificaciones(self, evaluacion=None, padres=False):
        """
            Devuelve las calificaciones para un alumno dado.
        """
        # FIXME: Mover esto a calificaciones.
        out = []
        asignaturas = self.getAsignaturas(tipo = 'N')
        if evaluacion is None:
            evaluaciones = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
        else:
            evaluaciones = Evaluacion.objects.filter(pk = evaluacion)
        for i in evaluaciones:
            if i.is_apta():
                if not padres or (padres and i.is_apta_padres()):
                    boletin = {}
                    try:
                        boletin['evaluacion'] = i
                        # FIXME
                        # Como se devuelve una lista no se contempla los casos en los que haya asignaturas
                        # sin notas. En estos casos los boletines se generan erróneamente, asignándose notas
                        # en filas incorrectas.
                        #boletin['calificaciones'] = self.calificacion_set.filter(evaluacion = i, asignatura__in = asignaturas).order_by("asignatura__nombreCorto")
                        boletin['calificaciones'] = Calificacion.objects.filter(
                                matricula__asignatura__in = asignaturas,
                                evaluacion = i,
                                matricula__in = Matricula.objects.filter(
                                    grupo_aula_alumno__in = self.grupoaulaalumno_set.exclude(grupo__seccion = "Pendientes"),
                                    tipo = 'N'
                                )
                            ).order_by("matricula__asignatura__nombreCorto")
                        if i.nombre == 'U':
                            calificaciones = boletin['calificaciones']
                            boletin['calificaciones'] = []
                            for a in asignaturas:
                                nota = None
                                for c in calificaciones:
                                    if c.matricula.asignatura == a:
                                        nota = c
                                        break
                                boletin['calificaciones'].append(nota)
                                        

                        boletin['informe'] = self.calificacioncompetencia_set.get(evaluacion = i)
                    except Calificacion.DoesNotExist:
                        logger.error("No hay calificacion")
                        boletin['calificaciones'] = None
                    except CalificacionCompetencia.DoesNotExist:
                        logger.error("No hay calificacion de competencia")
                        boletin['informe'] = None
                    out.append(boletin)
        if evaluacion == None or not out:
            return out
        return out[0]

    def getCalificacionAsignatura(self, evaluacion, asignatura):
        """
           Devuelve la calificación del alumno para una evaluación
           y una asignatura concretas.
           Si aún no ha sido calificado, devuelve None.
        """
        try:
            return self.grupoaulaalumno_set.exclude(grupo__seccion = "Pendientes")[0].matricula_set.get(asignatura = asignatura).calificacion_set.get(evaluacion = evaluacion)
        except (Calificacion.DoesNotExist, Matricula.DoesNotExist, IndexError):
            return None

    def setCalificacionAsignatura(self, evaluacion, asignatura, nota):
        """
            Establece una nueva calificación para un alumno, evaluación
            y asignatura dadas. Si la calificación existía, simplemente
            cambia el valor de la nota, si no es así, la crea.
            Originalmente permitíamos la inserción de procedimientos, conceptos
            y actitud, pero esto ha caído en desuso.
            Estos tres campos estaban establecidos como obligatorios, para no
            modificar la base de datos a posteriori, simplemente asignamos una
            cadena vacía a cada uno.
        """

        calificacion = self.getCalificacionAsignatura(evaluacion, asignatura)
        if not calificacion:
            calificacion = Calificacion(evaluacion = evaluacion, matricula = self.grupoaulalaumno_set.exclude(
                grupo__seccion = "Pendientes")[0].matricula_set.get(asignatura = asignatura))
        calificacion.nota = nota
        calificacion.conceptos = ""
        calificacion.procedimientos = ""
        calificacion.actitud = ""
        calificacion.save()
        return calificacion

    def generaBoletin(self, writer, page = None):
        """
            Genera un boletin para el alumno con la informacion de todas las evaluaciones
            hasta la actualidad.
        """
        CalificacionCompetencia.generaBoletin(writer, self, page)


    def getDatosBoletinWebKit(self):
        """
            Devuelve los datos necesarios para rellenar un boletin de un alumno que
            se convertirá a PDF utilizando webkit.
        """
        return CalificacionCompetencia.getDatosBoletinWebKit(self)

    def getFaltasEvaluacion(self, evaluacion):
        """
           Obtiene el numero total de faltas de asistencia
           de este alumno en la evaluacion designada.
           La fecha de final de evaluacion asi como la de comienzo
           de curso, debe estar definida en el archivo de configuracion
           de akademic. Si no fuera asi, se devolveria un None
        """
        numEv = CalificacionCompetencia._getEvaluacionNumerica(evaluacion)
        fechaInicio = None
        fechaFin = None
        claves = {'F': FALTA_ASISTENCIA, 'R': RETRASO, 'C': FALTA_COMPORTAMIENTO, 'T': FALTA_TAREA, 'M': FALTA_MATERIAL}
        if numEv == 1:
            if not FECHA_INICIO_CURSO:
                logger.error("No se ha definido la fecha de inicio del curso")
                return None
            fechaInicio = FECHA_INICIO_CURSO
        else:
            try:
                if not FECHAS_EVALUACIONES[numEv - 2]:
                    logger.error("Las fechas de evaluacion no estan correctamente definidas")
                    return None
                fechaInicio = FECHAS_EVALUACIONES[numEv - 2]
            except KeyError:
                logger.error("Las fechas de evaluacion no se han definido")
        try:
            if not FECHAS_EVALUACIONES[numEv-1]:
                logger.error("Las fechas de evaluacion no estan correctamente definidas")
                return None
            fechaFin = FECHAS_EVALUACIONES[numEv-1]
        except KeyError:
            logger.error("Las fechas de evaluacion no se han definido")
            return None

        out = {}
        for k,v in claves.items():
            out[k] = self.falta_set.filter(fecha__gte = fechaInicio, fecha__lte = fechaFin, tipo = v).count()
        return out


class Asignatura(models.Model):
    """
        Define una asignatura
    """
    abreviatura = models.CharField(max_length = 3)
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    # Define si esta asignatura proviene de Pincel o la hemos definido nosotros
    # por alguna necesidad (asignaturas "virtuales" de infantil y primeros ciclos
    # de primaria, etc.)
    metaAsignatura = models.BooleanField(blank = False, default = False)
    
    def __unicode__(self):
        return self.nombreCorto
    
    class Meta:
        ordering = ['nombreCorto']

class Ciclo(models.Model):
    """
        Representa un ciclo (1er ciclo, 2º ciclo, etc) de un nivel escolar
    """
    nombre = models.CharField(max_length = 15)
    # Si el ciclo es de jornada continua hay que matricular a los alumnos en una asignatura especial
    # que ocupa todo el día.
    jornada_continua = models.BooleanField(default = False)
    nivel = models.ForeignKey('Nivel')

    def __unicode__(self):
        return u"%s Nivel: %s" % (self.nombre, self.nivel)

    class Meta:
        ordering = ['nombre', 'nivel']

class Curso(models.Model):
    """
        Representa un curso (1º, 2º, etc) de un ciclo escolar
    """
    nombre = models.CharField(max_length = 15)
    ciclo = models.ForeignKey(Ciclo)

    def __unicode__(self):
        return u"%s Ciclo: %s" % (self.nombre, self.ciclo)

    class Meta:
        ordering = ['ciclo', 'nombre']


class GrupoAula(models.Model):
    """
        Representa las asignaciones de grupos de los distintos niveles escolares a
        un aula concreta. 
    """
    # 1º de primer ciclo de Primaria de 2009, 2º de segundo ciclo de Secundaria de 2009, etc.
    curso = models.ForeignKey(Curso)

    # Es el grupo para Pincel, por ejemplo, A, B, C
    seccion = models.CharField(max_length = 10, blank=True)

    def __unicode__(self):
        return u"%s %s %s" % (self.curso.nombre, self.curso.ciclo.nivel.nombre, self.seccion)

    def display_boletin(self):
        return u"%s_%s_%s" % (self.curso.nombre, self.curso.ciclo.nivel.nombre, self.seccion)

    def hasTutor(self):
        return self.tutor_set.count() != 0
    
    def getTutor(self):
        """
           Devuelve el tutor de este grupo, si se hubiera dado de alta
           mas de un tutor se devuelve el primero de los definidos.
        """
        from docencia.tutoria.models import Tutor
        try:
            return self.tutor_set.get()
        except Tutor.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            logger.warning("El grupo %s tiene definido mas de un tutor" % self)
            return self.tutor_set.all()[0]

    def getAlumnos(self):
        """
            Devuelve el listado de alumnos ordenados por apellidos.
            Los alumnos deberan estar matriculados en este grupo y la matricula
            debera tener caracter normal (no deben tener la asignatura pendiente
            ni convalidada)
        """
        #FIXME: Solo devuelve alumnos que esten en ese grupo (no se sabe si matriculados o no
        #       ni el tipo de matricula!!!
        return Alumno.filter(grupoaulaalumno__grupo=self)
    
    def getBoletinesAlumnos(self):
        """
            Devuelve los boletines  de los alumnos ordenados por apellidos.
        """
        return [i.getDatosBoletinWebKit() for i in self.getAlumnos()]

    def getAlumnosAsignatura(self, asignatura, tipo='N'):
        """
            Devuelve los alumnos de un grupo que deben asistir a una de las
            asignaturas que imparte el profesor.
        """        
        return Alumno.filter(grupoaulaalumno__grupo=self, grupoaulaalumno__matricula__asignatura=asignatura, grupoaulaalumno__matricula__tipo=tipo)

    def get_faltas_alumnos_fechas(self, inicial, final):
        """
            Devuelve las faltas de asistencia totales que tuvo el grupo
            entre las fechas inicial (inclusive) y final
        """
        return Falta.objects.filter(tipo = FALTA_ASISTENCIA, fecha__gte = inicial.date(), fecha__lt = final.date(), 
                alumno__grupoaulaalumno__grupo = self).count()
        
    class Meta:
        ordering = ['curso',]

class Profesor(models.Model):
    """
        Define los datos relativos a un Profesor del centro
    """
    persona = models.OneToOneField(PersonaPerfil)

    def __unicode__(self):
        return u"%s %s" % (self.persona.nombre, self.persona.apellidos)

    def get_alumnos(self):
        return Alumno.filter(grupoaulaalumno__grupo__in = self.get_grupos())
    
    def ver_boletines(self):
        if Calificacion.objects.filter(evaluacion__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL).count():
            return True
        return False

    def getHorario(self, curso_escolar = None, dia = None):
        """
            Devuelve el horario del profesor ordenado por día de la semana
            y luego por identificador de hora.
        """
        #filter = Q()
        #if curso_escolar:
        #    filter = Q(grupo__curso__ciclo__nivel__cursoEscolar = curso_escolar)
        #horarioProf = self.horario_set.filter(filter).order_by('hora', 'diaSemana')
        return self.check_dias_especiales(curso_escolar, dia)
    
    def get_grupos(self, curso_escolar = None):
        if not curso_escolar:
            curso_escolar = settings.CURSO_ESCOLAR_ACTUAL
        return GrupoAula.objects.filter(horario__profesor = self, horario__grupo__curso__ciclo__nivel__cursoEscolar = 
            curso_escolar).exclude(seccion = "Pendientes").distinct()
    
    def check_dias_especiales(self, curso_escolar = None, dia = None):
        today = dia or datetime.datetime.now()
        inicio = today - datetime.timedelta(today.weekday())
        final = today + datetime.timedelta(6 - today.weekday())
        dias = self.diaespecial_set.filter(dia__lte = final, dia__gte = inicio).distinct()
        grupo_dia = [(g, d) for g in self.get_grupos() for d in g.diaespecial_set.filter(dia__lte = final, dia__gte = inicio)]   
        filter = Q()
        if curso_escolar:
            filter = Q(grupo__curso__ciclo__nivel__cursoEscolar = curso_escolar)
        horario = self.horario_set.filter(filter)
        exclude = Q()
        # Eliminamos todas las horas especiales existentes en el horario actual asociadas al profesor
        horas_especiales = []
        for h in horario:
            # Eliminamos del horario las clases con los grupos que estén en dias especiales
            for g,d in grupo_dia:
                weekday = d.dia.weekday()+1
                if h.grupo == g and h.diaSemana == weekday:
                    exclude = exclude | Q(id = h.id) 
            # Eliminamos del horario las horas en conflicto con el dia especial
            for d in dias:
                weekday = d.dia.weekday()+1
                if h.diaSemana == weekday:
                    exclude = exclude | Q(id = h.id)
                g_l = ''
                for g in d.grupo.all():
                    g_l += str(g.id) + '_'
                horas_especiales.append((g_l[:len(g_l)-1], d.dia, d.motivo, self.id))
        return self.horario_set.filter(filter).exclude(exclude), horas_especiales 

    def getHorarioWeb(self, semana = None, anyo = None):
        """
            Devuelve el horario del profesor con todos los metadatos necesarios
            para crear la vista web.
        """
        # Primero calculamos las fechas que se nos solicitan realmente:
        if not anyo:
            anyo = time.strftime("%Y")
        if not semana:
            semana = time.strftime("%W")

        anyoNuevo = datetime.datetime(int(anyo), 1, 1)

        # Cuando establecemos un timedelta con el número de semanas
        # nos devuelve el domingo de la semana actual.
        # Para posicionarnos en el lunes le tendremos que restar 6 días.
        # Esta es la misma operación que hacíamos en akademic 1.0
        # debido a algunas conversiones que hacen los objetos timedelta.
        diasAnyo = datetime.timedelta(weeks = int(semana))
        # ojo, se ha producido un error al pasar del 2006 al 2007, el código
        # original se conserva comentado en la línea de debajo de esta.
        #lunes = datetime.timedelta(days = 6)
        #lunes = datetime.timedelta(days = 7)
        anyoNuevoWD = datetime.timedelta(days = anyoNuevo.weekday())

        fecha = anyoNuevo + diasAnyo - anyoNuevoWD

        dias_semana = []
        for i in range(5):
            dias_semana.append(fecha.strftime('%d-%m-%Y'))
            delta = datetime.timedelta(days = 1)
            fecha = fecha + delta
        horario, horas_especiales = self.getHorario(settings.CURSO_ESCOLAR_ACTUAL, fecha)

        horas_continua = []
        horas_normales = []
        for i in horario:
            if i.hora not in horas_continua and i.hora not in horas_normales:
                if i.hora.duracion() > 120: # Estas sesiones son las de jornada continua.
                    horas_continua.append(i.hora.id)
                else:
                    horas_normales.append (i.hora.id)
        horas_continua.sort()
        horas_normales.sort()
        
        horariosweb = []
        for horasid in (horas_continua, horas_normales):
            horas = Hora.objects.filter(id__in = horasid)
            horarioweb = []
            for i in horas:
                aux = { 'hora' : i , 'dias' : []}
                for j in range(5):
                    hora = []
                    for h in horario:
                        if h.hora == i and h.diaSemana == j + 1:
                            hora.append(h)
                    pdm = { 'fecha':dias_semana[j], 'clases':None, 'parte': None}
                    if hora:
                        fecha_obj = time.strptime(dias_semana[j], "%d-%m-%Y")
                        fechadt = datetime.datetime(fecha_obj[0], fecha_obj[1], fecha_obj[2], hora[0].hora.horaInicio.hour, hora[0].hora.horaInicio.minute) 
                        asignaturas = []
                        for asig in hora:
                            asignaturas.append(asig.asignatura)
                        parte = Parte.objects.filter(fecha = fechadt, profesor = self, asignatura__in = asignaturas)

                        if parte:
                            pdm["parte"] = parte
                        else:
                            pdm["parte"] = None

                        pdm["clases"] = hora
                        pdm["nombre"] = u"%s %sº %s %s" % (hora[0].asignatura.nombreCorto,
                                                        str(hora[0].grupo)[0], 
                                                        hora[0].grupo.curso.ciclo.nivel.nombre,
                                                        hora[0].grupo.seccion)
                        if len(hora) > 1:
                            pdm['nombre'] += " (Desdoble)"
                    else:
                        for item in horas_especiales:
                            if j == item[1].weekday():
                                pdm['clases'] = ('especial', item[2])
                                break
                    if not pdm['clases']:
                        for h in Horario.objects.filter(profesor = self, diaSemana = j+1, hora = i).exclude(pk__in = [p.id for p in horario.filter(diaSemana = j+1)]):
                            date = fecha - datetime.timedelta(5-j)
                            dia = DiaEspecial.objects.filter(dia = date, grupo = h.grupo)
                            pdm['clases'] = ('ocupada', 'Clase en ' + dia[0].motivo)
                             
                    pdm['dia'] = NOMBRES_DIAS[j] 
                    aux['dias'].append(pdm)
                horarioweb.append(aux)
            if horarioweb:
                horariosweb.append (horarioweb)
        salida = {'horario' : horario, 'horarioweb': horariosweb, 
            'horas': horas, 'semana': semana, 'semanaAnterior' : int(semana) - 1,
            'semanaSiguiente': int(semana) + 1, 'dias_semana': dias_semana}
        return salida

    def getFaltasFecha(self, dia = None, horas = None, tipo = 'faltas'):
        """
            Devuelve la hora lectiva en la que debe encontrarse el profesor
            en el instante en el que se realiza la consulta.
            Devuelve un diccionario con una clave "claseActual" que indexa un
            QuerySet con la clase en cuestión o una lista vacía, una clave
            "fecha" que indexa la fecha a la que corresponde la clase actual.
            Una última clave "alumnos" que indexa la lista con todos los alumnos
            de la clase actual.
        """
        dia = dia or datetime.datetime.now()
        if horas:
            horas = [horas] 
        else:
            horas = [str(h.id) for h in Hora.objects.filter (horaInicio__lte = dia.time(), horaFin__gte = dia.time())]
        horario, horas_especiales = self.getHorario(settings.CURSO_ESCOLAR_ACTUAL, dia)
        for d in horas_especiales:
            if d[1].weekday() == dia.weekday():
                grupos = [g for g in GrupoAula.objects.filter(pk__in = d[0].split('_'))]
                datos = self.get_faltas_especiales(tipo, dia, grupos)
                return dict(grupos=datos, fecha=dia.date(), hora='Todo el dia', asignatura={'nombreLargo':'Dia Especial', 'id':None})
        clasesact = []
        if horas:
            for h in horario:
                if h.diaSemana == dia.weekday()+1 and str(h.hora.id) in horas and h.grupo.curso.ciclo.nivel.cursoEscolar == settings.CURSO_ESCOLAR_ACTUAL:
                    clasesact.append(h)
        if not clasesact:
            return u"No hay clase a esta hora"
        if tipo == 'faltas':
            if len (clasesact) > 1:
                for c in clasesact[1:]:
                    if c.asignatura != clasesact[0].asignatura:
                        return u'Usted tiene clase actualmente de más de una asignatura, Seleccione una de ellas en en el horario.'
        grupos = []
        for c in clasesact:
            aux = {}
            aux['alumnos'] = self.getFaltasAlumnos(c.grupo, c.asignatura, dia, c.hora, tipo)
            aux['clase'] = c.grupo
            grupos.append (aux)
        return dict(grupos=grupos, fecha=dia.date(), hora=clasesact[0].hora, 
                    asignatura=clasesact[0].asignatura)

    def get_faltas_especiales(self, tipo = 'faltas', dia = None, grupos = None):
        if not dia:
            dia = datetime.date.today()
        datos = [] 
        for g in grupos:
            aux = {'clase': g, 'alumnos': [], }
            for a in g.getAlumnos():
                alu = {'alumno': a}
                if tipo == 'faltas': 
                    alu['ausencia'] = a.estadoAusencia()
                    alu['uniforme'] = a.estadoUniforme(dia)
                    alu['total'] = a.falta_set.filter(fecha = dia, tipo = FALTA_ASISTENCIA).count()
                else:
                    alu['total'] = a.falta_set.filter(fecha = dia, tipo = FALTA_COMPORTAMIENTO).count()
                for k,v in diccionario[tipo]:
                    alu[k] = a.falta_set.filter(fecha = dia, tipo = v).count()
                aux['alumnos'].append(alu)
            datos.append(aux)
        return datos
    
    def getFaltasAlumnos(self, grupo, asignatura, fecha, hora, tipo='faltas'):
        """
            Devuelve, ordenados alfabéticamente, los alumnos de un grupo dado que están
            matriculados en una asignatura. Y si tienen faltas a esta hora o no.
        """
        # Ahora tenemos que recorrer la lista de alumnos matriculados e ir marcando los que tienen
        # falta para mostrarlo correctamente en la vista.
        salida = []
        for alumno in grupo.getAlumnosAsignatura(asignatura).distinct():
            aux = {}
            if tipo is 'faltas':
                aux['ausencia'] = alumno.estadoAusencia()
                aux['uniforme'] = alumno.estadoUniforme(fecha)
                aux['total'] = [alumno.falta_set.filter(fecha = fecha, tipo = FALTA_ASISTENCIA).count(), alumno.falta_set.filter(fecha = fecha, tipo = RETRASO).count()]
                
            else:
                aux['total'] = [alumno.falta_set.filter(fecha = fecha, tipo = FALTA_COMPORTAMIENTO).count(), 
                    alumno.falta_set.filter(fecha = fecha, tipo = FALTA_TAREA).count(), alumno.falta_set.filter(fecha = fecha, tipo = FALTA_MATERIAL).count()]
            for k,v in diccionario[tipo]:
                aux[k] = alumno in self.getFaltas(asignatura, fecha, hora, tipo = v)
            aux['alumno'] = alumno
            salida.append(aux)
        return salida

    def getGruposHora(self, asignatura, fecha, hora):
        """
           Devuelve los grupos a los que este profesor da clase,
           a la hora que se especifica, de la asignatura que se especifica.
        """
        diaSemana = fecha.weekday() + 1
        return GrupoAula.objects.filter(horario__profesor = self, horario__diaSemana = diaSemana,
                        horario__hora = hora, horario__asignatura = asignatura,
                        horario__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL
                    ).exclude(seccion = "Pendientes")

    def getFaltas(self, asignatura, fecha, hora, tipo = FALTA_ASISTENCIA):
        """
            Devuelve las faltas que existen en la base de datos para una
            fecha y hora concretas.
        """
        #FIXME: getGruposHora en profesor no mola. Horario.getGruposHoraProfesor(asignatura, fecha, hora, profesor) si
        if asignatura:
            return Alumno.filter(falta__fecha=fecha, falta__asignatura=asignatura, falta__hora=hora,
                falta__tipo = tipo, grupoaulaalumno__grupo__in = self.getGruposHora(asignatura, fecha, hora))
        return Alumno.filter(falta__fecha=fecha, falta__tipo=tipo, grupoaulaalumno__grupo__in=hora)
    
    def getUniformes(self, asignatura, fecha, hora):
        """
            Devuelve las faltas por uniforme que tengan sus alumnos para una fecha y hora concretas
        """
        if asignatura:
            return Alumno.objects.filter(uniforme__dia = fecha, grupoaulaalumno__grupo__in = self.getGruposHora(asignatura, fecha, hora))
        return Alumno.objects.filter(uniforme__dia = fecha, grupoaulaalumno__grupo__in=hora)
    
    def getAsignaturas(self):
        """
            Devuelve el listado de asignaturas del profesor y 
            los grupos en los que las imparte.
        """
        listaAsignaturas = Horario.objects.filter(
                profesor=self,
                grupo__curso__ciclo__nivel__cursoEscolar=settings.CURSO_ESCOLAR_ACTUAL
            ).values('asignatura', 'grupo').distinct().order_by('asignatura')        
        salida = []        
        for i in listaAsignaturas:
            aux = { 'asignatura': Asignatura.objects.get(pk=i['asignatura']),
                    'grupo': GrupoAula.objects.get(pk=i['grupo']) }
            salida.append(aux)
            
        return salida

    def getListados(self, tipo_listado, listaAsignaturas, fechaInicio, fechaFin, fecha=None):
        """
            Devuelve el listado de faltas de material correspondiente a la lista de asignaturas
            entre las fechas que se pasan como argumentos.
            A la salida se obtiene una lista de diccionarios con el siguiente
            formato.
            listado = [
                {
                    'asignatura':<<un objeto asignatura>>, 
                    'faltas': [
                        {'alumno': <<el alumno>>, 'totalFaltas':<< el total faltas>>,
                            'faltas' = [
                                ...
                            ]
        """
        def get_lista_faltas_dia(faltas_totales_alumno, lista_dias_totales):
            lista = []
            for dia in lista_dias_totales:
                fecha = fecha_inicial.replace(day=dia)
                query = faltas_totales_alumno.filter(fecha=fecha)
                if query:
                    lista.append('F')
                else:
                    lista.append(None)
            
            return lista
        #DEBUG: para saber si la fecha se envia como parametro antiguo(mix de strings),
        #o un datetime.        
        if not fecha:
            fanyo, fmes, fdia = fechaInicio.split("-")
            fecha = datetime.date(int(fanyo), int(fmes), int(fdia) )
            
        ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
        fecha_inicial = fecha.replace(day=1) # El dia de la fecha enviado correspondería al día 1
        fecha_final = fecha.replace(day=ultimo_dia)        
        lista_dias_totales = range(1, ultimo_dia + 1)        
        # Para cada asignatura seleccionada, calculamos las faltas de cada alumno.
        listados_finales = []
        for asig in listaAsignaturas:
            (asignaId, grupoId) = asig.split('@')
            asignatura = Asignatura.objects.get(pk=asignaId)
            grupo_aula = GrupoAula.objects.get(pk=grupoId)
            alumnos = grupo_aula.getAlumnosAsignatura(
                asignatura)
                                                                     
            faltas_por_alumno = []
            for alu in alumnos:
                datos = {}
                faltas_totales_alumno_mes = Falta.objects.filter(alumno=alu, 
                            tipo=tipo_listado, fecha__gte=fecha_inicial, 
                            fecha__lte=fecha_final, asignatura__id = asignaId)
                numero_faltas = faltas_totales_alumno_mes.count()
                #Una lista de tipo: [None, None, 'F', None...
                faltas = get_lista_faltas_dia(faltas_totales_alumno_mes, lista_dias_totales)
                datos = { 'alumno': alu,
                          'faltas': faltas,
                          'totalFaltas': numero_faltas }
                faltas_por_alumno.append(datos)
            listado_por_asignatura = { 
                                      'asignatura': asignatura,
                                      'alumnos': faltas_por_alumno,
                                      'grupo': grupo_aula,
                                      'tipoListado': getNameFromTuple(TIPO_FALTAS, tipo_listado),
                                      'fechaInicio': fecha_inicial,            
                                      'fechaFin': fecha_final, 
                                      'dias': lista_dias_totales
                                      }
            listados_finales.append(listado_por_asignatura)
            
        return listados_finales    
    
    def getResumenEvaluacion(self, listaAsignaturas, fechaInicio, fechaFin):
        """
            Devuelven los datos que necesita el motor de plantillas para generar
            los resúmenes de evaluación.
        """
        listados = []
        claves = {'totalAsistencia': FALTA_ASISTENCIA, 'totalRetrasos': RETRASO, 'totalComportamiento': FALTA_COMPORTAMIENTO,
                  'totalTarea': FALTA_TAREA, 'totalMaterial': FALTA_MATERIAL }  
        for asig in listaAsignaturas:
            (asignaId, grupoId) = asig.split('@')
            asignatura = Asignatura.objects.get(pk = asignaId)
            grupo = GrupoAula.objects.get(pk = grupoId)
            alumnos = grupo.getAlumnosAsignatura(asignatura)
            aux = {}
            aux['asignatura'] = asignatura
            aux['grupo'] = grupo
            aux2 = []
            for alu in alumnos:
                datos = {}
                datos['alumno'] = alu
                for k,v in claves.items():
                    datos[k] = alu.getFaltasAsignatura(asignatura, fechaInicio, fechaFin, True, v)
                aux2.append(datos)
            aux['faltas'] = aux2
            listados.append(aux)

        return listados

    def getInformePartes(self, fechaInicio, fechaFin):
        """
           Devuelve tres valores.
           - Horas lectivas totales en el intervalo de fechas.
           - Partes enviados en el intervalo de fechas.
           - Porcentaje de envíos.
        """
        #FIXME: Esto tendrá que tener en cuenta los días festivos.
        horasDiarias = []
        for i in range(1, 8):
            horas = []
            totales = 0
            for h in self.horario_set.filter(diaSemana = i, grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL):
                if h.hora not in horas:
                    horas.append(h.hora)
                    totales += 1
            horasDiarias.append(totales)
        fechaInicio = datetime.datetime(day = fechaInicio.day, month = fechaInicio.month, year = fechaInicio.year)
        fechaFin = datetime.datetime(day = fechaFin.day, month = fechaFin.month, year = fechaFin.year, hour = 23, minute = 59)
        unDia = datetime.timedelta(days = 1)
        total = 0
        ind = fechaInicio
        while (ind <= fechaFin):
            total += horasDiarias[ind.weekday()]
            ind += unDia
        dias = []
        # Se tienen en cuenta los dias especiales del profesor
        for dia in self.diaespecial_set.filter(dia__lte = fechaFin, dia__gte = fechaInicio).distinct():
            total -= horasDiarias[dia.dia.weekday()]
            dias.append(dia.dia)
        # Asi como las horas en que la clase este en un dia especial pero no el profesor
        for g,d in [(g, d) for g in self.get_grupos() for d in g.diaespecial_set.filter(dia__lte = fechaFin, dia__gte = fechaInicio).exclude(dia__in = dias)]:
            total -= Horario.objects.filter(grupo = g, diaSemana = d.dia.weekday()+1, profesor = self).count()   
        partes = self.parte_set.filter(fecha__gte = fechaInicio, fecha__lte = fechaFin).count()
        try:
            porcentaje = partes * 100 / total
        except ZeroDivisionError:
            porcentaje = 0
        if porcentaje > 100: porcentaje = 100
        return (total, partes, porcentaje)

    class Meta:
        ordering = ['persona',]

class GrupoAulaAlumno(models.Model):
    """
        Representa la matrícula de un alumno en una asignatura y un grupo.
    """
    alumno = models.ForeignKey(Alumno)
    grupo = models.ForeignKey(GrupoAula)
    
    def __unicode__(self):
        return u"%s %s--> %s" % (self.alumno.persona.nombre, self.alumno.persona.apellidos, self.grupo)


class Matricula(models.Model):
    """
        Representa la matrícula de un alumno en una asignatura y un grupo.
    """
    grupo_aula_alumno = models.ForeignKey(GrupoAulaAlumno)
    asignatura = models.ForeignKey(Asignatura)
    tipo = models.CharField('Tipo de matrícula', max_length = 1, choices = OPCIONES_TIPOMATRICULA)

    @staticmethod
    def matriculadoAlumnoCurso(alumno, curso):
        return Matricula.objects.filter(grupo_aula_alumno__alumno__in = alumno, grupo_aula_alumno__grupo__curso__ciclo__nivel__cursoEscolar = curso)

    # FIXME: Añadir un enlace con el profesor que imparte esta asignatura. Esto es bueno hacerlo porque se da el caso
    # super guapo de que la misma asignatura, para el mismo curso a la misma hora la imparten dos profesores diferentes
    
    def __unicode__(self):
        return u"%s %s--> %s [%s]" % (
                self.grupo_aula_alumno.alumno.persona.nombre, self.grupo_aula_alumno.alumno.persona.apellidos,
                self.grupo_aula_alumno.grupo, self.asignatura.nombreCorto
            )

class AsignaturasPendientes(models.Model):
    """
        Guarda el curso de la calificacion en que se suspendio por primera vez
    """
    matricula = models.ForeignKey(Matricula)
    curso = models.CharField('Curso', max_length = 6)

class Nivel(models.Model):
    """
        Representa un nivel escolar. Por ejemplo, Infantil, Primaria, etc.
    """
    cursoEscolar = models.IntegerField('Curso escolar', null = False, blank = False)
    nombre = models.CharField(max_length = 25)
    
    def __unicode__(self):
        return u"%s %s" % (self.nombre, self.cursoEscolar)
    
    class Meta:
        ordering = ['cursoEscolar', 'nombre']
        verbose_name_plural = 'Niveles'

class CoordinadorCiclo(models.Model):
    """
        Define un coordinador para un ciclo de un nivel educativo.
    """
    profesor = models.ForeignKey(Profesor)
    ciclo = models.ForeignKey(Ciclo)
        
    def __unicode__(self):
        return u"%s %s" % (self.profesor.persona.nombre, self.profesor.persona.apellidos)
    

class JefeEstudios(models.Model):
    """
        Define un jefe de estudios para un nivel educativo.
    """
    profesor = models.ForeignKey(Profesor)
    nivel = models.ForeignKey(Nivel)
    
    def __unicode__(self):
        return self.profesor.persona.nombre + " " + self.profesor.persona.apellidos

    def get_grupos(self):
        return GrupoAula.objects.filter(curso__ciclo__nivel = self.nivel).exclude(seccion = 'Pendientes').order_by('curso__nombre', 'seccion')

    def get_xls_absentismo(self, ev):
        """
            Devuelve el xls con la informacion de absentismo de la evaluacion
            requerida, ponderada segun el nivel que corresponda
        """
        def get_next_month(date):
            if date.month == 12:
                return datetime.datetime(date.year+1, 1, 1)
            return datetime.datetime(date.year, date.month+1, 1)

        def get_dates_range(ev):
            # Rango de fechas. Dias se calcula asi porque las fechas
            # de las evaluaciones nunca coinciden 
            inicial = final = datetime.datetime.now()
            if ev.nombre == '1':
                inicial = FECHA_INICIO_CURSO
                final = FECHAS_EVALUACIONES[0]
            elif ev.nombre == '2':
                inicial = FECHAS_EVALUACIONES[0]
                final = FECHAS_EVALUACIONES[1]
            else:
                inicial = FECHAS_EVALUACIONES[1]
                final = FECHAS_EVALUACIONES[2]
            mes1 = get_next_month(get_next_month(inicial))
            mes2 = get_next_month(mes1)
            return [inicial, mes1, mes2, final]

        # Iniciamos el xls
        w = Workbook()
        al = Alignment()
        al.horz = Alignment.HORZ_CENTER
        al.vert = Alignment.VERT_CENTER
        style = XFStyle()
        style.alignment = al
        style.font.height = 220
        ws = w.add_sheet(u'Informe %s' % ev)
        # Ancho de columna
        for i in range(10):
            ws.col(i).width = 0x1200
        # Creamos el header
        ponderator = POND_FACTOR[self.nivel.nombre]
        msg = u"ABSENTISMO ESCOLAR: El numero total de faltas de asistencia mensuales (horas totales) esta dividido entre %d" % ponderator
        ws.write_merge(0, 0, 0, 9, msg, style) 
        ws.write_merge(1, 1, 0, 9, u"")
        msg = u"NIVEL: %s\nCURSO: %s\nEVALUACION: %s" % (self.nivel.nombre, settings.CURSO_ESCOLAR_ACTUAL, ev)
        ws.write_merge(2, 4, 0, 1, msg, style)
        dates = get_dates_range(ev)
        # Repetimos 3 veces (una por cada rango de fechas)
        for i in range(3):
            # j son las columnas de MES, DIAS LECTIVOS Y COLUMNA VACIA DE RELLENO
            for j in range(3):
                col = 2 + j + i*3
                if j == 0:
                    ws.write(2, col, u"MES", style)
                    ws.write(3, col, u"%s %s" % (dates[i].strftime('%d/%m'), dates[i+1].strftime("%d/%m")), style) # Fechas
                elif j == 1:
                    ws.write(2, col, u"Nº DIAS LECTIVOS", style)
                    ws.write(3, col, u"???", style) # Dias lectivos, imposible saberlo    
                else:
                    ws.write_merge(4, 4, col-2, col-1, u"FALTAS ASISTENCIA", style)
                    if i < 2:
                        ws.write_merge(2, 4, col, col, "")
        ws.write(5, 0, u"GRUPOS", style)
        # Por cada columna de MES, DIAS LECTIVOS Y VACIA
        for i in range(3):
            ws.write(5, 1+i*3, u"Nº ALUMNOS", style)
            ws.write(5, 2+i*3, u"JUSTIFICADAS", style)
            ws.write(5, 3+i*3, u"INJUSTIFICADAS", style)
        gi = 6
        for g in self.get_grupos():
            ws.write(gi, 0, u"%sº%s" % (g.curso.nombre, g.seccion), style)
            for ind in range(len(dates)-1):
                ws.write(gi, 1+ind*3, u"%d" % g.getAlumnos().count(), style)
                faltas = g.get_faltas_alumnos_fechas(dates[ind], dates[ind+1]) / ponderator
                ws.write(gi, 2+ind*3, u"%d" % faltas, style)
            gi += 1
        # Retornamos la plantilla
        return w

class DiaEspecial(models.Model):

    dia = models.DateField('Día')
    grupo = models.ManyToManyField(GrupoAula)
    responsables = models.ManyToManyField(Profesor)
    motivo = models.CharField('Motivo', max_length = 20)
    # TODO: avanzar en los dias especiales para que puedan ser un par de horas solo
    #       y no todo el dia
    # horas = models.ManyToManyField(Hora) 

    def __unicode__(self):
        return self.dia.strftime("%A, %d de %B de %Y").capitalize().decode('utf-8')

    @staticmethod
    def create(dia, motivo, grupo_id, res_list):
        """
            Recibe un diccionario con los siguientes campos
            dia: datetime.date
            nivel: lista de niveles (puede ser null)
            ciclo: lista de ciclos (puede ser null)
            grupo: lista de grupos (puede ser null)
        """
        dia, created = DiaEspecial.objects.get_or_create(dia = dia, motivo = motivo)
        g = GrupoAula.objects.get(pk = grupo_id)
        changes = 0
        if g not in dia.grupo.all():
            dia.grupo.add(g)
        for r in res_list:
            resp = Profesor.objects.get(pk = r)
            if resp not in dia.responsables.all():
                dia.responsables.add(resp)
                changes += 1
        dia.save()    
        return changes

class FileAttach(models.Model):
    
    alumno = models.ForeignKey(Alumno)
    file = models.FileField('Archivo', upload_to='files/%Y/%m/%d')
    visto = models.BooleanField(default = False)

