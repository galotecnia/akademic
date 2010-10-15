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

import datetime
import time
import calendar
import sys

from django.db import models
from django.db.models import Q
from django.conf import settings

from docencia.horarios.models import OPCIONES_DIAS
from docencia.models import Asignatura, Matricula, GrupoAula
from docencia.constants import *

class Tutor(models.Model):
    """
        Define un tutor, asignando un profesor
        a un grupo, el cual sería su tutor.
    """
    profesor = models.ForeignKey('docencia.Profesor')
    grupo = models.ForeignKey('docencia.GrupoAula')
    
    def __unicode__(self):
        #return "%s %s" % (self.profesor.nombre, self.profesor.apellidos)
        return u"%s" % self.profesor
    
    def getResumenTutor(self, fechaini = None, fechafin = None):
        """
            Obtiene el resumen de todas las incidencias ocurridas entre los
            alumnos de la tutoría en el rango de fechas consignado.
        """
        salida = {}
        resAlumn = []
        totalFalt = totalRet = totalComp = totalTar = totalMat = 0
        for alu in self.grupo.getAlumnos():
            resumen = alu.getResumenTutor(fechaini, fechafin, generarResumen = True)
            totalFalt += resumen['totalFaltas']
            totalRet += resumen['totalRetrasos']
            totalComp += resumen['totalComportamiento']
            totalTar += resumen['totalTarea']
            totalMat += resumen['totalMaterial']
            aux = {"alumno": alu, "resumen": resumen}
            resAlumn.append(aux)
        salida['resumenes'] = resAlumn
        
        totales = {}
        totales['totalFaltas'] = totalFalt
        totales['totalRetrasos'] = totalRet
        totales['totalComportamiento'] = totalComp
        totales['totalTarea'] = totalTar
        totales['totalMaterial'] = totalMat
        salida['totales'] = totales
        return salida
    
    def getInformeTutor(self, fechaini = None, fechafin = None):
        """
            Obtiene el informe de todas las incidencias ocurridas entre los
            alumnos de la tutoría en el rango de fechas consignado.
        """
        salida = []
        for alu in self.grupo.getAlumnos():
            resumen = alu.getResumenTutor(fechaini, fechafin, generarResumen = False)
            salida.append({"alumno": alu, "resumen": resumen})
        return salida

    def getAsignaturasTutoria(self):
        """
            Obtiene la lista de todas las asignaturas que se imparten
            en la tutoría.
        """
        # Esto se añade porque puede tener grupos desdoblados en la tutoría.
        grupos = GrupoAula.objects.filter(curso__ciclo__nivel = self.grupo.curso.ciclo.nivel, 
            curso = self.grupo.curso, seccion__icontains = self.grupo.seccion).exclude(seccion = "Pendientes")
        out = []
        for g in grupos:
            for asignatura in Asignatura.objects.filter(pk__in = Matricula.objects.filter(grupo_aula_alumno__grupo = g).values('asignatura')):
                out.append({'grupo': g, 'asignatura': asignatura, })
        return out

    def procesaListados(self, tipoListado, listadoFaltas, fechaInicio, fechaFin):
        """
            Devuelve una matriz con las faltas de tarea que han tenido lugar en el mes
            seleccionado.
        """
        salida = []
        for asig in listadoFaltas:
            aux = {}
            aux['asignatura'] = asig['asignatura']
            aux['grupo'] = asig['grupo']
            fanyo, fmes, fdia = fechaInicio.split("-")
            aux['fechaInicio'] = "-".join([fdia, fmes, fanyo])
            fanyo, fmes, fdia = fechaFin.split("-")
            aux['fechaFin'] = "-".join([fdia, fmes, fanyo])
            aux['tipoListado'] = tipoListado
            diaInicio = fechaInicio.split("-")[2]
            anyo, mes, diaFin = fechaFin.split("-")
            aux['dias'] = range(int(diaInicio), int(diaFin) + 1)
            alumnos = []
            for alu in asig['faltas']:
                aux2 = {}
                aux2['alumno'] = alu['alumno']
                aux2['faltas'] = []
                if alu['totalFaltas'] == 0:
                    for dia in range(int(diaInicio), int(diaFin) + 1):
                        #aux2[str(dia)] = None
                        aux2['faltas'].append(None)
                else:
                    for dia in range(int(diaInicio), int(diaFin) + 1):
                        #aux2[str(dia)] = None
                        aux2['faltas'].append(None)
                        for falta in alu['faltas']:
                            fechaTest = datetime.datetime(int(anyo), int(mes), int(dia))
                            if str(falta.fecha) == fechaTest.strftime('%Y-%m-%d'):
                                if tipoListado == 'asistencia':
                                    aux2['faltas'][-1] = 'F'
                                    break
                                elif tipoListado == 'retraso':
                                    aux2['faltas'][-1] = 'R'
                                    break
                                elif tipoListado == 'comportamiento':
                                    aux2['faltas'][-1] = 'C'
                                    break
                                elif tipoListado == 'tareas':
                                    aux2['faltas'][-1] = 'T'
                                    break
                                elif tipoListado == 'material':
                                    aux2['faltas'][-1] = 'M'
                                    break
                aux2['total'] = alu['totalFaltas']
                alumnos.append(aux2)
            aux['alumnos'] = alumnos
            salida.append(aux)
        return salida

    def getListados(self, tipoListado, listaAsignaturas, fechaInicio, fechaFin):
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
                    }

                ]
            }
        ]
        """
        d = {'asistencia': FALTA_ASISTENCIA, 'retraso': RETRASO, 'comportamiento': FALTA_COMPORTAMIENTO,
             'tareas': FALTA_TAREA, 'material': FALTA_MATERIAL }
        # Obtenemos el listado de alumnos de la tutoría
        alumnos = self.grupo.getAlumnos()
        # Para cada asignatura seleccionada, calculamos las faltas de cada alumno.
        listados = []
        if not listaAsignaturas:
            listaAsignaturas = [item['asignatura'] for item in self.getAsignaturasTutoria()]
            print listaAsignaturas
        for asignatura in listaAsignaturas:
            aux = {}
            aux['asignatura'] = asignatura
            aux['grupo'] = self.grupo
            aux2 = []
            for alu in alumnos:
                datos = {}
                faltas = alu.getFaltasAsignatura(asignatura, fechaInicio, fechaFin, None, d[tipoListado])
                datos['alumno'] = alu
                datos['faltas'] = faltas
                datos['totalFaltas'] = len(faltas)
                aux2.append(datos)
            aux['faltas'] = aux2
            listados.append(aux)

        # Una vez tenemos los datos los procesamos dependiendo del tipo de listado
        # del que se trate.
        return self.procesaListados(tipoListado, listados, fechaInicio, fechaFin)

    def getListadosTotales(self, tipoListado, fechaInicio, fechaFin):
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
                        }

                    ]
                }
            ]
        """
        d = {'asistencia': FALTA_ASISTENCIA, 'retraso': RETRASO, 'comportamiento': FALTA_COMPORTAMIENTO,
             'tareas': FALTA_TAREA, 'material': FALTA_MATERIAL }
        # Obtenemos el listado de alumnos de la tutoría
        alumnos = self.grupo.getAlumnos()
        # Para cada asignatura seleccionada, calculamos las faltas de cada alumno.
        listaAlumnos = []
        listados = []
        for alu in alumnos:
            datos = {}
            faltas = alu.getTotalDiarioFaltas(fechaInicio, fechaFin, d[tipoListado])
            listaAlumnos.append(faltas)
        #salida = self.procesaListados(tipoListado, listados, fechaInicio, fechaFin)
        diaInicio = 1
        diaFin = fechaFin.split('-')[2]
        salida = {}
        salida['fechaInicio'] = fechaInicio
        salida['fechaFin'] = fechaFin
        salida['alumnos'] = listaAlumnos
        salida['tipoListado'] = tipoListado
        salida['dias'] = range(diaInicio, int(diaFin) + 1)
        salida['grupo'] = self.grupo
        
        listados = [salida]
        return listados

    def hasTutoria(self):
        return self.tutoria_set.count() != 0
 
class Tutoria(models.Model):
    """
        REPRESENTA una tutoría: un periodo de tiempo donde un determinado profesor
        ofrece la posibilidad de que sus alumnos o padres de los mismos lo visiten
        fuera del horario lectivo.

        NO REPRESENTA: las citas solicitadas por los padres
    """
    tutor = models.ForeignKey(Tutor)
    hora = models.TimeField()
    diaSemana = models.IntegerField('Día de la semana', choices = OPCIONES_DIAS)
    maxCitas = models.IntegerField('Número máximo de citas')

    def __unicode__(self):
        return u"%s - %s - %s" % (self.tutor, self.diaSemana, self.hora)

    def horaFinalTutoria(self):
        delta = datetime.timedelta(minutes = DURACION_TUTORIAS)
        aux = datetime.datetime(*(time.strptime(self.hora.strftime("%H:%M"), "%H:%M"))[0:6])
        aux = aux + delta
        return aux

    def full(self, fecha):
        """
            Devuelve si una tutoría está llena o no
        """
        return self.maxCitas <= Cita.objects.filter(tutoria = self, fecha = fecha).count()
    
    def obten_fecha_para_proxima_tutoria_desde_hoy(self):
        fecha_de_hoy = datetime.date.today()        
        diferencia_dias = 0 
        if fecha_de_hoy.isoweekday() >= self.diaSemana:
            diferencia_dias = 7 - self.diaSemana
        if fecha_de_hoy.isoweekday() < self.diaSemana:
            diferencia_dias = self.diaSemana - iterador_fecha.isoweekday()
            
        diferencia_dias = datetime.timedelta(days=diferencia_dias)
        return fecha_de_hoy + diferencia_dias

    def proximasFechas(self, alumno):
        """
            Calcula las próximas fechas de tutoría en función de si ya se han
            agotado las plazas, si la cita ya ha sido reservada por el alumno,
            etc...
        """
        #Obtenemos la primera fecha posible de cita
        fecha = self.obten_fecha_para_proxima_tutoria_desde_hoy()
        fechas_citas = []
        fechas_citas.append(fecha)
        #Obtenemos el resto de fechas
        una_semana = datetime.timedelta(weeks=1)        
        while len(fechas_citas) < self.maxCitas:
            fecha = fecha + una_semana
            fechas_citas.append(fecha)
                  
        salida = []
        for i in fechas_citas:
            aux = {}
            citas = Cita.objects.filter(
                Q(tutoria=self) &
                Q(fecha="%s-%s-%s" % (i.year, i.month, i.day) ) )
            aux['fecha'] = "%s-%s-%s" % (i.day, i.month, i.year)
            if not citas:
                aux['disponible'] = 'Disponible'
                aux['numCitas'] = self.maxCitas
            elif len(citas) >= self.maxCitas:
                aux['disponible'] = 'Lleno'
            elif citas.filter(alumno=alumno):
                aux['disponible'] = 'Reservada'
            else:                    
                aux['disponible'] = 'Disponible'
                aux['numCitas'] = self.maxCitas - len(citas)                        
            salida.append(aux)
        return salida        
    
class Cita(models.Model):
    """
        REPRESENTA: una cita de un padre con un tutor a una hora determinada de un
        día determinado de un año determinado
    """
    tutoria = models.ForeignKey(Tutoria)
    fecha = models.DateField()
    padre = models.BooleanField()
    madre = models.BooleanField()
    alumno = models.ForeignKey('docencia.Alumno')
    avisadoSMS = models.BooleanField()
    avisadoEMAIL = models.BooleanField()

    def __unicode__(self):
        return str(self.alumno) + " - " + str(self.fecha) + " " + str(self.tutoria.hora)

    @staticmethod 
    def nueva_cita(tutoria, fecha, alumno, padre):

        f = time.strptime(fecha, "%Y-%m-%dT%H:%M:%S")
        fecha_dt = datetime.datetime(f.tm_year, f.tm_mon, f.tm_mday, f.tm_hour, f.tm_min, 0) 
        # Comprobamos que no haya pasado ya la fecha de la cita
        if datetime.datetime.now() >= fecha_dt:
            return u"La tutoria seleccionada es anterior en el tiempo"

        # Comprobamos que haya sitio para una nueva cita a esa hora
        if tutoria.full(fecha_dt):
            return u"La tutoria seleccionada esta completa"

        # Comprobamos que no exista otra tutorÃ­a en la misma hora con el mismo
        # tutor y mismo padre
        try:
            
            c = Cita.objects.get(tutoria = tutoria, fecha = fecha_dt, alumno = alumno)
            return u"Ya tiene concertada una cita este dia"
        except Cita.DoesNotExist:
            pass
        p = m = False
        if alumno.padre == padre:
            p = True
        else:
            m = True
        cita = Cita(tutoria = tutoria, fecha = fecha_dt, avisadoSMS = False, avisadoEMAIL = False, alumno = alumno, padre = p, madre = m)
        cita.save()
        return None

