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

import logging

log = logging.getLogger('galotecnia')

class Traductor(models.Model):
    """
       Clase padre para dotar a todos los traductores de un bit processed
       para poder controlar los elementos borrados.

       Dirty, significa que se ha tocado durante la importación, es por
       eso que el valor por defecto es False.
    """
    processed = models.BooleanField(default = False)

    class Meta:
        abstract = True

    @staticmethod
    def get_not_processed(traductor):
        """
           Devuelve todos aquellos elementos que no hayan sido tocados durante la importación
        """
        return traductor.objects.filter(processed = False)

    @staticmethod
    def clean_not_processed(traductor, really_sure = False):
        log.debug(u'Entrando en clean_not_processed')
        not_processed = traductor.get_not_processed(traductor)
        log.debug(u'Número de objetos a eliminar: %d', len(not_processed))
        for t in not_processed:
            log.debug(u'Borrando %s con pk = %d', type(t.akademic), t.akademic.pk)
            if really_sure:
                t.akademic.delete()
                t.delete()
        traductor.objects.filter(processed = True).update(processed = False)

    @staticmethod
    def set_processed(ticker, obj):
        """
            Marca un objeto como procesado, de esta forma no se borrará al final.
        """
        obj_translator, created = ticker.objects.get_or_create(akademic = obj)
        obj_translator.processed = True
        obj_translator.save()

class GrupoAulaAlumnoTicker(Traductor):
    """
        Tabla de control para el borrado de los GrupoAulaAlumno.
    """
    akademic = models.ForeignKey('docencia.GrupoAulaAlumno')
    
    class Meta:
        verbose_name = "Ticker de GrupoAulaAlumno"
        verbose_name_plural = "Tickers de GrupoAulaAlumno"

class UsuarioTicker(Traductor):
    """
        Tabla de control para el borrado de los usuarios.
    """
    akademic = models.ForeignKey('auth.User')
    
    class Meta:
        verbose_name = "Ticker de Usuario"
        verbose_name_plural = "Tickers de Usuario"

class TutoriaTicker(Traductor):
    """
        Tabla de control para el borrado de las tutorias.
    """
    akademic = models.ForeignKey('tutoria.Tutoria')

    class Meta:
        verbose_name = "Ticker de Tutoria"
        verbose_name_plural = "Tickers de Tutoria"

class TutorTicker(Traductor):
    """
        Tabla de control para el borrado de los tutores
    """
    akademic = models.ForeignKey('tutoria.Tutor')

    class Meta:
        verbose_name = "Ticker de Tutor"
        verbose_name_plural = "Tickers de Tutor"

class CoordinadorTicker(Traductor):
    """
        Tabla de control para el borrado de coordinadores de ciclo
    """
    akademic = models.ForeignKey('docencia.CoordinadorCiclo')

    class Meta:
        verbose_name = "Ticker de Coordinador de Ciclo"
        verbose_name_plural = "Tickers de Coordinador de Ciclo"

class JefeEstudiosTicker(Traductor):
    """
        Tabla de control para el borrado de jefe de estudios
    """
    akademic = models.ForeignKey('docencia.JefeEstudios')
    
    class Meta:
        verbose_name = "Ticker de Jefe de Estudios"
        verbose_name_plural = "Tickers de Jefe de Estudios"

class HorarioTicker(Traductor):
    """
        Tabla de control para el borrado de los horarios
    """
    akademic = models.ForeignKey('horarios.Horario')

    class Meta:
        verbose_name = "Ticker de Horario"
        verbose_name_plural = "Tickers de Horario"

class MatriculaTicker(Traductor):
    """
        Tabla de control para el borrado de las matrículas.
    """
    akademic = models.ForeignKey('docencia.Matricula')

    class Meta:
        verbose_name = "Ticker de Matricula"
        verbose_name_plural = "Tickers de Matricula"

class CalificacionTicker(Traductor):
    """
        Tabla de control para el borrado de las calificaciones.
    """
    akademic = models.ForeignKey('notas.Calificacion')

    class Meta:
        verbose_name = "Ticker de Calificacion"
        verbose_name_plural = "Tickers de Calificacion"

class CalificacionCompetenciaTicker(Traductor):
    """
        Tabla de control para el borrado de las calificaciones.
    """
    akademic = models.ForeignKey('notas.CalificacionCompetencia')

    class Meta:
        verbose_name = "Ticker de CalificacionCompetencia"
        verbose_name_plural = "Tickers de CalificacionCompetencia"

class TraductorAlumno(Traductor):
    """
        Tabla de traducción para los alumnos
    """
    registro = models.CharField(max_length = 25)
    akademic = models.ForeignKey('docencia.Alumno')
    
    def __unicode__(self):
        return u"Num registro: %s --> %s" % (self.registro, self.akademic)

    class Meta:
        verbose_name = "Traductor de Alumno"
        verbose_name_plural = "Traductores de Alumno"

class TraductorHora(Traductor):
    """
        Tabla de traducción para las horas
    """
    denominacion = models.CharField(max_length = 2)
    nivel = models.ForeignKey('docencia.Nivel')
    akademic = models.ForeignKey('horarios.Hora')
    
    def __unicode__(self):
        return u"Denominacion: %s --> %s" % (self.denominacion, self.akademic)

    class Meta:
        verbose_name = "Traductor de Hora"
        verbose_name_plural = "Traductores de Hora"

class TraductorPadre(Traductor):
    """
        Tabla de traducción para los padres
    """
    dni = models.CharField(max_length = 25)
    akademic = models.ForeignKey('padres.Padre')
    
    def __unicode__(self):
        return u"DNI: %s --> %s" % (self.dni, self.akademic)

    class Meta:
        verbose_name = "Traductor de Padre"
        verbose_name_plural = "Traductores de Padre"

class TraductorProfesor(Traductor):
    """
        Tabla de traducción para los profesores
    """
    dni = models.CharField(max_length = 25)
    akademic = models.ForeignKey('docencia.Profesor')
    
    def __unicode__(self):
        return u"DNI: %s --> %s" % (self.dni, self.akademic)

    class Meta:
        verbose_name = "Traductor de Profesor"
        verbose_name_plural = "Traductores de Profesor"

class TraductorCurso(Traductor):
    """
        Tabla de traducción para los cursos
    """
    curso_esco = models.CharField(max_length = 4)
    nivel = models.CharField(max_length = 3)
    ciclo = models.CharField(max_length = 3)
    curso = models.CharField(max_length = 1)
    akademic = models.ForeignKey('docencia.Curso')
    
    def __unicode__(self):
        return u"(curso escolar %s, nivel %s, ciclo %s, curso %s) --> %s" % (
                self.curso_esco, self.nivel, self.ciclo, self.curso, self.akademic
            )

    class Meta:
        verbose_name = "Traductor de Curso"
        verbose_name_plural = "Traductores de Curso"

class TraductorGrupoAula(Traductor):
    """
        Tabla de traducción para los grupoAula
    """
    curso_esco = models.CharField(max_length = 4)
    nivel = models.CharField(max_length = 3)
    ciclo = models.CharField(max_length = 3)
    curso = models.CharField(max_length = 1)
    grupo = models.CharField(max_length = 1)
    akademic = models.ForeignKey('docencia.GrupoAula')
    
    def __unicode__(self):
        return u"(curso escolar %s, nivel %s, ciclo %s, curso %s, grupo %s) --> %s" % (
                self.curso_esco, self.nivel, self.ciclo, self.curso, self.grupo, self.akademic
            )

    class Meta:
        verbose_name = "Traductor de GrupoAula"
        verbose_name_plural = "Traductores de GrupoAula"

class TipoVia(models.Model):
    """
        Define un tipo de vía.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)

    def __unicode__(self):
        return self.nombreCorto

class Municipio(models.Model):
    """
        Define un municipio
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Isla(models.Model):
    """
        Define una isla
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto
    
class Provincia(models.Model):
    """
        Define una provincia
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto
    
class Profesion(models.Model):
    """
        Define una profesion
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class EstudiosPadre(models.Model):
    """
        Define una profesion
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Pais(models.Model):
    """
        Define un país
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto
    
class Autorizacion(models.Model):
    """
        Define una autorización.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class TipoEspacio(models.Model):
    """
        Representa un tipo de espacio dentro del
        centro escolar.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class TipoUso(models.Model):
    """
        Representa un tipo de uso posible para
        un espacio dentro de un centro escolar.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Ubicacion(models.Model):
    """
        Representa un tipo de ubicación dentro del
        centro escolar.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Concierto(models.Model):
    """
        Define un tipo de concierto económico.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Minusvalia(models.Model):
    """
        Define un tipo de minusvalía.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25)
    
    def __unicode__(self):
        return self.nombreCorto

    class Meta:
        unique_together = ('nombreLargo', 'idPincel')


class EstadoCivil(models.Model):
    """
        Define un estado civil.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Centro(models.Model):
    """
        Representa un centro escolar.
    """
    idPincel = models.CharField(max_length = 25, unique = True)
    nombre = models.CharField(max_length = 50)
    domicilio = models.CharField(max_length = 40, blank = True)
    municipio = models.ForeignKey(Municipio)
    localidad = models.CharField(max_length = 30)
    codPostal = models.CharField(max_length = 5, blank = True)
    isla = models.ForeignKey(Isla)
    telefono = models.CharField(max_length = 20, blank = True)
    fax = models.CharField(max_length = 20, blank = True)
    email = models.EmailField(blank = True)
    iesdestino = models.IntegerField(blank = True, null = True)
    
    def __unicode__(self):
        return str(self.id) + "--" + self.nombre

class TipoConstruccion(models.Model):
    """
        Representa un tipo de construcción dentro del
        centro escolar.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

class Clasificacion(models.Model):
    """
        Define una clasificación.
    """
    nombreCorto = models.CharField(max_length = 25)
    nombreLargo = models.CharField(max_length = 50, blank = True)
    idPincel = models.CharField(max_length = 25, unique = True)
    
    def __unicode__(self):
        return self.nombreCorto

