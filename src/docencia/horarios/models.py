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
from docencia.constants import OPCIONES_DIAS, DEN_HORAS

class Hora(models.Model):
    """
        Define una hora lectiva.
        
        La idea ahora es poder definir horarios por niveles Infantil, primaria y
        secundaria 
        
        Del mismo modo poder asignar horas por días.
    """
    denominacion = models.CharField(max_length = 10)
    horaInicio = models.TimeField('Hora de inicio')
    horaFin = models.TimeField('Hora de fin')
    nivel = models.ForeignKey('docencia.Nivel', blank = True, null = True)

    def __unicode__(self):
        return u"%s (%s)" % (self.denominacion, self.intervalo())
    
    def intervalo(self):
        return (self.horaInicio.strftime ('%H:%M - ') + self.horaFin.strftime ('%H:%M'))

    def duracion (self):
        horas = self.horaFin.hour - self.horaInicio.hour
        minutos = self.horaFin.minute - self.horaInicio.minute
        return horas * 60 + minutos

    class Meta:
        ordering = ['horaInicio',]

class Horario(models.Model):
    """
        Representa el horario de un profesor con las distintas horas lectivas
        que imparte a distintos grupos con distintas asignaturas.
    """
    
    hora = models.ForeignKey(Hora)
    diaSemana = models.IntegerField(u'Día de la semana', choices = OPCIONES_DIAS)
    asignatura = models.ForeignKey('docencia.Asignatura')
    profesor = models.ForeignKey('docencia.Profesor')
    grupo = models.ForeignKey('docencia.GrupoAula')
    
    def __unicode__(self):
        return u"Dia: %s Hora: %s Profesor: %s" % (self.diaSemana, self.hora.denominacion, self.profesor.persona.nombre)

    @staticmethod
    def getClases(diaSemana, horas, profesor):
        return Horario.objects.filter(
                diaSemana = diaSemana,
                hora__in = horas,
                profesor = profesor,
                grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL
            )

    @staticmethod
    def getClasesAbsoluto(momento, profesor):
        horas = Hora.objects.filter (horaInicio__lte = hora, horaFin__gte = hora)
        dia_semana = momento.weekday() + 1 
        return Horario.getClases(dia_semana, horas, profesor)
    
    class Meta:
        ordering = ['hora', 'diaSemana', 'grupo']
