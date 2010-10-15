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
from django.contrib.auth.models import User
import time, datetime

# Create your models here.

TIPOS_DE_RECURSO = (
        (1, 'Aulas'),
        (2, 'Material deportivo'),
        (3, 'Audiovisuales'),
        (4, 'Otros'),
    )

class Recurso (models.Model):
    """
        Define uno de los recursos que pueden soliticar los profesores
    """
    descripcion = models.CharField ('Descripción', max_length= 255, blank = False, null = False)
    tipo = models.IntegerField ('Tipo', choices = TIPOS_DE_RECURSO, null = False)
    actualmenteDisponible = models.BooleanField ('Disponible', null = False)

    def __unicode__(self):
        return u"%s - %s" % (self.descripcion, self.get_tipo_display())

    @staticmethod
    def getDisponibles (tipo_recurso = None):
            if tipo_recurso is None:
                return Recurso.objects.filter(Q(actualmenteDisponible = True))
            else:
                return Recurso.objects.filter(
                        Q(actualmenteDisponible = True) & 
                        Q(tipo = tipo_recurso)
                    )



class Reserva (models.Model):
    """
        Define la reserva de un recurso por un profesor
    """
    recurso = models.ForeignKey (Recurso, null = False)
    responsable = models.ForeignKey (User, null = False)
    motivo = models.TextField ('Motivo de la reserva', blank = False, null = False)
    inicio = models.DateTimeField (null = False)
    fin = models.DateTimeField (null = False)

    def __unicode__(self):
        return u"%s %s (%s - %s)" % (self.recurso, self.responsable, self.inicio, self.fin)

    @staticmethod
    def getReservas (recurso_id = None, tipo = None, usuarioResponsable = None):
        """
            Devuelve las reservas que hay sobre este en el futuro
        """
        filtro = None
        if tipo is not None:
            filtro = Q(recurso__tipo = tipo)
    
        if usuarioResponsable is not None:
            if filtro is not None:
                filtro &= Q(responsable = usuarioResponsable)
            else:
                filtro = Q(responsable = usuarioResponsable)
    
        if recurso_id is not None:
            if filtro is not None:
                filtro &= Q(recurso = recurso_id)
            else:
                filtro = Q(recurso = recurso_id)
        if filtro is not None:
            filtro &= Q(fin__gte = time.strftime ('%Y-%m-%d %H:%M:%S'))
        else:
            filtro = Q(fin__gte = time.strftime ('%Y-%m-%d %H:%M:%S'))
    
        return Reserva.objects.filter(filtro).order_by ('inicio')

    @staticmethod
    def getCalendario (setDictFunction = None, diccionarioAdicional = None, semana = None, anyo = None):
        """
            devuelve una estructura con la información de las reservas de una semana
        """
        if not anyo:
            anyo = time.strftime("%Y")
        if not semana:
            semana = time.strftime("%W")

        anyoNuevo = datetime.datetime(int(anyo), 1, 1)

        diasAnyo = datetime.timedelta(weeks = int(semana))

        anyoNuevoWD = datetime.timedelta(days = anyoNuevo.weekday())

        #lunes = datetime.timedelta(days = 6)
        aux = fecha = anyoNuevo + diasAnyo - anyoNuevoWD
        dias_semana = []

        #Encabezado de la tabla
        dias_semana.append([{'texto':'Horas', 'class': 'header'}])
        for i in range(5):
            dias_semana.append([{'texto':aux.strftime('%d-%m-%y'), 'class': 'header'}])
            aux = aux + datetime.timedelta(days = 1)

        # Lista de horas, desde las 8 de la mañana a las 8 de la tarde
        aux = datetime.datetime(int(anyo), 1, 1)
        aux = aux + datetime.timedelta (hours = 7, minutes = 30)
        for i in range(24):
            aux = aux + datetime.timedelta (minutes = 30)
            dias_semana[0].append({'texto': aux.strftime ('%H:%M'), 'class' : 'header'})
        for j in range(1, 6):
            # Vamos a sacar el día de hoy.
            aux = fecha + datetime.timedelta (hours = 7, minutes = 30, days = j - 1)
            reserva = None
            for i in range(24):
                aux = aux + datetime.timedelta (minutes = 30)
                if setDictFunction is not None:
                    dias_semana[j].append(setDictFunction (aux, diccionarioAdicional))
                    # el diccionario adicional contiene parámetros que tb se tiene que pasar a este método,
                    # por ejemplo el recurso_id
        #Ahora esta super matriz tendremos que recodificarla porque para poder pintar en html
        #necesitamos la información dispuesta por columnas y no por filas.
        calendario_final = []
        for i in range(25):
            fila = []
            hora = dias_semana[0][i]['texto']
            for j in range(6):
                fila.append (dias_semana[j][i])
#               if dias_semana[j][i]['class'] == 'ocupado':
            calendario_final.append(fila)
#       return dias_semana
        return calendario_final

def setDictRecurso (datetime, diccionario):
    # Debería pillar el día y la hora y buscar reservas del recurso tal que inicio <= tiempo y fin >= tiempo
    try:
        reserva = Reserva.objects.get (
                Q(inicio__lte = datetime) &
                Q(fin__gt = datetime) &
                Q(recurso = diccionario['recurso_id'])
            )
        return ({'texto': reserva.responsable, 'class': 'ocupado'})
    except Reserva.DoesNotExist:
        return ({'texto': ' ', 'class': 'libre'})

