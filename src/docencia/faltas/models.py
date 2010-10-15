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

from docencia.horarios.models import Hora
from notificacion.constants import ESTADO_NOTIFICACION
from docencia.constants import *

import datetime

class Ausencia(models.Model):
    """
        Representa una ausencia de un alumno (castigo o lo que sea)
    """
    alumno = models.ForeignKey('docencia.Alumno')
    inicio = models.DateTimeField()
    fin = models.DateTimeField(null = True)
    motivo = models.TextField('Motivo de la ausencia', blank = True, null = True)
    notificadoSMS = models.IntegerField('Estado notificacion SMS', choices = ESTADO_NOTIFICACION, default = 3)

    def finaliza (self):
        self.fin = datetime.datetime.now()
        self.save ()
    
    def __unicode__(self):
        return u"%s %s" % (self.alumno.persona.nombre,  self.alumno.persona.apellidos)

    def fechaBonita (self):
        return (self.fecha.strftime ('%a dia %d de %b de %Y'))

class Uniforme(models.Model):
    """
        Representa una falta de uniforme por parte del alumno
    """
    alumno = models.ForeignKey('docencia.Alumno', unique_for_date = 'dia') #Igual que poner unique_together = ['alumno', dia'])
    dia = models.DateField()
 
class Falta(models.Model):
    """
        Representa una falta de asistencia de un alumno.
    """
    alumno = models.ForeignKey('docencia.Alumno')
    fecha = models.DateField()
    hora = models.ForeignKey(Hora)
    asignatura = models.ForeignKey('docencia.Asignatura')
    tipo = models.IntegerField(u'Tipo de falta', choices=TIPO_FALTAS)
    notificadoSMS = models.BooleanField('Falta notificada por SMS')
    textoIncidencia = models.TextField('Texto de la incidencia', blank = True, null = True)
    
    def __unicode__(self):
        return u"%s [%s %s]" % (self.alumno.persona, self.hora, self.asignatura)
    
class Parte(models.Model):
    """
        Almacena cada uno de los envíos de faltas que realiza un determinado
        profesor.
    """
    profesor = models.ForeignKey('docencia.Profesor')
    asignatura = models.ForeignKey('docencia.Asignatura')
    # Fecha de la asignatura
    fecha = models.DateTimeField('Fecha', blank = False)

    def __unicode__(self):
        return u"%s %s %s" % (self.fecha, self.asignatura, self.profesor)

    class Meta:
        ordering = ['-fecha']

class EnviosFaltas(models.Model):
    """
        Almacena la fecha de cada uno de los envíos de faltas que realiza un
        determinado profesor para una asignatura dada.
    """
    parte = models.ForeignKey(Parte)
    # Fecha del envío
    fecha = models.DateTimeField('Fecha', blank = False)
    ip = models.IPAddressField(blank = True, null = True)
    # UserAgent
    user_agent = models.CharField(max_length = 255, blank = True, null = True)

    def __unicode__(self):
        return u"%s %s %s" % (self.fecha, self.ip, self.user_agent)

    class Meta:
        ordering = ['-fecha']

