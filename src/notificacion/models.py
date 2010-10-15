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
from django.db import models
from constants import *
import datetime

class TextoNotificacion(models.Model):
    """
        Representa un texto relacionado con una notificación SMS
        Puede ser un texto genérico o uno que escriba el usuario
    """
    texto = models.CharField('texto del mensaje', max_length = 160)
    generico = models.BooleanField()
    
    def __unicode__(self):
        return unicode(self.texto)

    def parse_texto(self):
        self.texto = self.texto.replace('<','-')
        self.texto = self.texto.replace('>','-')
        self.save()    

class Notificacion(models.Model):
    """
        REPRESENTA: Una notificación SMS
    """
    profesor = models.ForeignKey('docencia.Profesor', null = True, blank = True)
    padre = models.ForeignKey('padres.Padre')
    alumno = models.ForeignKey('docencia.Alumno')
    fechaCreacion = models.DateTimeField('fecha creación')
    fechaEnvio = models.DateTimeField('fecha envío', null = True, blank = True)
    texto = models.ForeignKey(TextoNotificacion)
    estado = models.IntegerField(choices = ESTADO_NOTIFICACION, default = 0)
    confidencial = models.BooleanField(blank = False, default = False)
    plataformaId = models.CharField(max_length = 50, blank = True, null = True)
    
    def __unicode__(self):
        return unicode(self.padre) + u" - " + unicode(self.fechaCreacion)
    
    def save(self, force_insert = False, force_update = False):
        super(Notificacion, self).save(force_insert, force_update)
        self.texto.parse_texto()

    @staticmethod
    def get_pendientes():
        """
            Devuelve la lista de notificaciones pendientes.
        """
        return Notificacion.objects.filter(fechaEnvio__isnull = True, estado=NOTIFICACION_PENDIENTE)

    @staticmethod
    def get_sin_estado():
        """
            Devuelve la lista de notificaciones sin estado.
        """
        return Notificacion.objects.filter(fechaEnvio__isnull = False, estado=NOTIFICACION_PENDIENTE)

    def set_enviada(self, plataforma_id):
        #self.estado = NOTIFICACION_ENVIADA
        self.fechaEnvio = datetime.datetime.now()
        self.plataformaId = plataforma_id
        self.save()

    def set_status(self, status):
        self.estado = status
        self.save()

    @staticmethod    
    def envia_notificacion(padre, alumno, texto_string=None, texto_notificacion=None,
                            confidencial=False, texto_generico=False, force=False, 
                            estado=0, profesor=None):
        """
            padre, alumno: Instancia del modelo. Previamente se ha comprado que sea correcta
        """
        movil = padre.persona.tlf_movil()
        if movil is "":            
            raise RuntimeError(PADRE_SIN_MOVIL)
        if not force and padre.verificado is None:
            raise RuntimeError(PADRE_MOVIL_NO_VERIFICADO)
        if not force and padre.is_blanco:
            raise RuntimeError(PADRE_NO_RESPONDE)
        if texto_string and texto_notificacion:            
            raise Exception('Se enviaron 2 textos')
        if not texto_string and not texto_notificacion:
            raise Exception("No se envio ningun texto")
        
        if texto_string:
            texto = TextoNotificacion(texto=texto_string, generico=texto_generico)
            texto.save()
        else:
            texto = texto_notificacion            
        notificacion = Notificacion(padre=padre, 
                                    alumno=alumno, 
                                    profesor=profesor,
                                    fechaCreacion=datetime.datetime.now(), 
                                    texto=texto, 
                                    confidencial=confidencial,
                                    estado=estado)        
        notificacion.save()
        return True
    
class Comentario(models.Model):
    """
        Comentarios sobre un alumno. Pueden ser tanto originados por el profesor
        como por un padre en respuesta a uno ya existente.
    """
    resumen = models.CharField(max_length = 255)
    texto = models.TextField(blank = False)
    # Fecha de envío
    fecha = models.DateTimeField(blank = False, auto_now_add = True)
    # Alumno sobre el que se está escribiendo
    alumno = models.ForeignKey('docencia.Alumno')
    # Profesor que escribe el comentario
    profesor = models.ForeignKey('docencia.Profesor')
    # Flag para identificar si el padre ya ha leido el comentario
    leido = models.BooleanField(blank = False, default = False)

    def __unicode__(self):
        return str(self.fecha) + ' ' + self.resumen 

    class Meta:
        ordering = ['-fecha']

class Respuesta(models.Model):
    """
        Respuesta a un comentario.
    """
    resumen = models.CharField(max_length = 255)
    texto = models.TextField(blank = False)
    # Fecha de envío
    fecha = models.DateTimeField(blank = False, auto_now_add = True)
    comentario = models.ForeignKey(Comentario)
    padre = models.ForeignKey('padres.Padre', blank = True, null = True)
    # Flag para identificar si el profesor ya ha leido el comentario
    leido = models.BooleanField(blank = False, default = False)

    class Meta:
        ordering = ['-fecha']

