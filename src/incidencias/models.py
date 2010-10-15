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
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.comments.models import Comment
from django.conf import settings

TIPOS_DE_INCIDENCIA = (
        (1, 'Informática'),
        (2, 'Mantenimiento'),
        (3, 'Akademic'),
        (4, 'Otras'),
    )

ESTADOS_DE_INCIDENCIA = (
        (1, 'Abierta'),
        (2, 'Resuelta'),
        (3, 'No válida'),
        (4, 'En proceso de solución'),
    )

PRIORIDADES_DE_INCIDENCIA = (
        (1, 'Crítica'),
        (2, 'Importante'),
        (3, 'Normal'),
        (4, 'Poco importante'),
        (5, 'Irrelevante'),
    )

class Incidencia(models.Model):
    """
        Define una incidencia.
    """
    descripcionCorta = models.CharField ('Descripción corta', max_length= 255, blank = False, null = False)
    texto = models.TextField('Descripción detallada', blank = False, null = False)
    tipoIncidencia = models.IntegerField ('Tipo', choices = TIPOS_DE_INCIDENCIA, null = False)
    fecha = models.DateField (null = False)
    estado = models.IntegerField ('Estado', choices = ESTADOS_DE_INCIDENCIA, null = False)
    prioridad = models.IntegerField ('Prioridad', choices = PRIORIDADES_DE_INCIDENCIA, null = False)
    informador = models.ForeignKey(User)


    def save(self):
        nuevaIncidencia = False
        if not self.id:
            nuevaIncidencia = True
        super(Incidencia, self).save()
        if nuevaIncidencia:
            para = settings.PARA
            de = settings.DE
            asunto = settings.ASUNTO
            s = 'Nueva incidencia: %s' % self.descripcionCorta
            send_mail(
                asunto % s,
                "Usuario: " + self.informador.username + "\nTexto:" + self.texto,
                de, 
                para,
                fail_silently=True
            )


    def __unicode__(self):
        return u"%s" % self.descripcionCorta

    def getEstadoDisplay(self):
        resultado = ESTADOS_DE_INCIDENCIA[self.tipoIncidencia - 1][1]
        return resultado


