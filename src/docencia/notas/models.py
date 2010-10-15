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
import datetime
import locale
from django.conf import settings
from docencia.auxmodels import *

NOTAS_TEXTUALES = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
)

CODIGOS_PROMOCION = (
    ('PRO', u'Promociona cumpliendo requisitos'),
    ('POB', u'Promociona por imposibilidad de permanencia un año más en el mismo curso'),
    ('PAC', u'Promociona considerando sus adaptaciones curriculares (NEE)'),
    ('REP', u'Permanece un año más en el curso'),
    ('EXT', u'Decisión pendiente de resultados de evaluación extraordinaria'),
    ('DC1', u'Incorporación al primer año de PDC'),
    ('PCE', u'Incorporación al PCPI conducente a título'),
    ('PCP', u'Incorporación a PCPI'),
    ('PCA', u'Incorporación a PCPI adaptado'),
    ('DC2', u'Incorporación al segundo año de PDC'),
    ('TIT', u'Titula'),
    ('PRM', u'Promociona/Titula'),
    ('CER', u'Obtiene certificado en algún módulo'),
    ('NCR', u'No obtiene certificado en ningún módulo'),
    ('NPR', u'No promociona/No titula'),
    ('SUP', u'Superado'),
    ('NSP', u'No superado')
)

CODIGOS_PROMOCION_CORTO = (
    ('PRO', u'Promociona'),
    ('POB', u'Prom. Edad'),
    ('PAC', u'Prom. ACS'),
    ('REP', u'Repite'),
    ('EXT', u'Pend. Ext.'),
    ('DC1', u'Inc. PDC 1º'),
    ('PCE', u'Inc. PCPI.T'),
    ('PCP', u'Inc.PCPI.'),
    ('PCA', u'Inc.PCPI. A'),
    ('DC2', u'Inc. PDC 2º'),
    ('TIT', u'Titula'),
    ('PRM', u'Prom./Tit.'),
    ('CER', u'Ob. Certificado'),
    ('NCR', u'No Ob. Certificado'),
    ('NPR', u'Rep/NoTit.'),
    ('SUP', u'Superado'),
    ('NSP', u'No Superado'),
)

from akademicLog import *
logger = AkademicLog().logger

class Competencia(models.Model):
    """
        Define una competencia básica que pueda asociarse posteriormente a cualquier
        asignatura.
    """
    nombre = models.CharField(max_length = 255)

    def __unicode__(self):
        return self.nombre

class Evaluacion(models.Model):
    """
        Define una sesión de evaluación.
        La propiedad evaluacionCompetencial nos permite mantener el enfoque
        anterior a la aplicación de la LOE, es decir, si es verdadero se
        evalúan competencias básicas. Si no es verdadero se evalúan conocimientos
        procedimientos y actitudes.
        Sobre los nombres de las evaluaciones:
        ESO:
            - 1: Primera evaluación.
            - 2: Segunda evaluación.
            - O: Evaluación ordinaria.
            - U: Evaluación extraordinaria.

        Bachillerato:
            - 1: Primera evaluación.
            - 2: Segunda evaluación.
            - J: Junio.
            - S: Septiembre.

        Ciclos formativo primer curso:
            - 1: Primera evaluación.
            - 2: Segunda evaluación.
            - 3: Tercera evaluación.

        Ciclos formativos segundo curso:
            - P: Primera evaluación.
            - R: Evaluación final ordinaria.
            - X: Evaluación final ciclos formativos.
    """
    nombre = models.CharField(max_length = 255)
    cursoEscolar = models.IntegerField('Curso escolar')

    def __unicode__(self):
        return u"%s %s" % (self.nombre, self.cursoEscolar)

    def is_apta(self):
        today = datetime.datetime.now() 
        numEv = CalificacionCompetencia._getEvaluacionNumerica(self)
        fechaInicio = None
        try:
            fechaInicio = FECHAS_EVALUACIONES[numEv-1]
        except KeyError:
            logger.error("Las fechas de evaluacion no se han definido")
        if not fechaInicio:
            return False
        return fechaInicio <= today
    
    def is_apta_padres(self):
        today = datetime.datetime.now() 
        numEv = CalificacionCompetencia._getEvaluacionNumerica(self)
        fechaInicio = None
        try:
            fechaInicio = FECHAS_PUBLICACION_BOLETINES[numEv-1]
        except KeyError:
            logger.error("Las fechas de evaluacion no se han definido")
        if not fechaInicio:
            return False
        return fechaInicio <= today

class Calificacion(models.Model):
    """
        Define la calificación de un alumno en una asignatura para una sesión de evaluación.
    """
    matricula = models.ForeignKey('docencia.Matricula')
    evaluacion = models.ForeignKey(Evaluacion)
    nota = models.CharField(max_length = 255)
    comentario = models.TextField(null = True, blank = True)
    conceptos = models.CharField(max_length = 1, choices = NOTAS_TEXTUALES )
    procedimientos = models.CharField(max_length = 1, choices = NOTAS_TEXTUALES )
    actitud = models.CharField(max_length = 1, choices = NOTAS_TEXTUALES)

    def __unicode__(self):
        return u"%s %s" % (self.matricula, self.nota)
    

class InformeEvaluacion(models.Model):
    """
        Almacena el informe de un alumno en una evaluación, típicamente esto tendrá que ver
        con los datos asociados a las competencias básicas, tal y como salen de Pincel.
    """
    alumno = models.ForeignKey('docencia.Alumno')
    evaluacion = models.ForeignKey(Evaluacion)
    informe = models.TextField()

    def __unicode__(self):
        return str(self.alumno) + "--" + str(self.evaluacion)
    
class CalificacionCompetencia(models.Model):
    """
        
    """
    alumno = models.ForeignKey('docencia.Alumno')
    evaluacion = models.ForeignKey(Evaluacion)
    informeCompetencias = models.TextField(blank = True)
    promociona = models.BooleanField(blank = True)
    codigo_promocion = models.CharField(blank = True, max_length = 3, choices = CODIGOS_PROMOCION)

    def __unicode__(self):
        return unicode(self.alumno) + u" " + unicode(self.evaluacion.nombre)

    @staticmethod
    def _limpiaBoletin(writer, page):
        """
           Elimina cualquier campo del boletin que no haya sido rellenado.
        """
        rangoEv = range(1,5)
        page = None
        writer.searchAndReplacePage(page, "$CIAL$", "")
        writer.searchAndReplacePage(page, "$OBSERVACIONES_GENERALES$", "")
        writer.searchAndReplacePage(page, "$PADRE$", "")
        writer.searchAndReplacePage(page, "$MADRE$", "")
        writer.searchAndReplacePage(page, "$GRUPO$", "")
        writer.searchAndReplacePage(page, "$TUTOR$", "")
        writer.searchAndReplacePage(page, "$FECHA_EVAL$", "")
        writer.searchAndReplacePage(page, "$EVALUACION_TEXTO$", "")
        writer.searchAndReplacePage(page, "$PROMOCIONA$", "")
        
        # Limpiamos los campos materia:
        for i in range(1, 12):
            writer.searchAndReplacePage(page, "$MATERIA%d$" % i, "")
            writer.searchAndReplacePage(page, "$OBS%d$" % i, "")
            for j in rangoEv:
                writer.searchAndReplacePage(page, "$NOTA%d_%d$" % (i, j), "")

        codCompetencias = ["CL", "MAT", "CON", "DIG", "SOC", "CUL", "APR", "AUT"]

        for comp in codCompetencias:
            for j in rangoEv:
                writer.searchAndReplacePage(page, "$%s_%d$" % (comp, j), "")

        codFaltas = ["F", "R", "C", "T", "M"]
        for cod in codFaltas:
            for j in rangoEv:
                writer.searchAndReplacePage(page, "$%s_%d$" % (cod, j), "")


    @staticmethod
    def _parseCompetencias(informeCompetencias):
        """
            Parsea un campo de texto con un informe de competencias textual
            y lo convierte a un diccionario para su posterior representacion
            en un boletin.
        """
        AVANZA1 = u"Avanza en su adquisición"
        AVANZA2 = u"Avanza en su adquisición ."
        NAVANZA1 = u"No avanza en su adquisición"
        NAVANZA2 = u"No avanza en su adquisición ."
        lineas = informeCompetencias.split("\n")
        i = 0
        out = {}
        while (i < len(lineas)):
            parsed = False
            value = ""
            if i+1 < len(lineas):
                cadena = unicode(lineas[i+1].strip())
                if cadena == AVANZA1 or cadena == AVANZA2:
                    value = "A"
                    parsed = True
                elif cadena == NAVANZA1 or cadena == NAVANZA2:
                    value = "N"
                    parsed = True
                else:
                    logger.warning("Se ha producido un error parseando competencias basicas")
                    value = " "
            else:
                logger.warning("No se han definido todas las competencias para este alumno")

            ident = unicode(lineas[i].strip().upper())
            if (ident== u"COMPETENCIA EN COMUNICACIÓN LINGÜÍSTICA"):
                out["CL"] = value
            elif (ident == u"COMPETENCIA MATEMÁTICA"):
                out["MAT"] = value
            elif (ident  == u"COMPETENCIA EN EL CONOCIMIENTO Y LA INTERACCIÓN  CON EL MUND") or (ident  == u"COMPETENCIA EN EL CONOCIMIENTO Y LA INTERACCIÓN CON EL MUNDO"):
                out["CON"] = value
            elif (ident == u"TRATAMIENTO DE LA INFORMACIÓN Y COMPETENCIA DIGITAL"):
                out["DIG"] = value
            elif (ident == u"COMPETENCIA SOCIAL Y CIUDADANA"):
                out["SOC"] = value
            elif (ident == u"COMPETENCIA CULTURAL Y ARTÍSTICA"):
                out["CUL"] = value
            elif (ident == u"COMPETENCIA PARA APRENDER A APRENDER"):
                out["APR"] = value
            elif (ident == u"AUTONOMÍA E INICIATIVA PERSONAL"):
                out["AUT"] = value
            if parsed:
                i += 2
            else:
                i += 1
        return out

    @staticmethod
    def generaBoletin(writer, alumno, page = None):
        """
            Genera un boletin para el alumno con la informacion de todas las evaluaciones
            hasta la actualidad.
        """
        locale.setlocale (locale.LC_ALL, 'es_ES.UTF-8')
        tutor = alumno.getTutor()
        grupo = alumno.getGrupo().grupo
        writer.searchAndReplacePage(page, "$ALUMNO$", u"%s" % alumno.persona)
        writer.searchAndReplacePage(page, "$GRUPO$", u"%s %s %s" % (grupo.curso.nombre, grupo.seccion, grupo.curso.ciclo.nivel.nombre))
        writer.searchAndReplacePage(page, "$CIAL$", alumno.cial)
        writer.searchAndReplacePage(page, "$NUMERO$", u"%s" % alumno.posicion)
        
        if alumno.madre:
            writer.searchAndReplacePage(page, "$MADRE$", u"%s %s" % (alumno.madre.persona.nombre, alumno.madre.persona.apellidos))
        if alumno.padre:
            writer.searchAndReplacePage(page, "$PADRE$", u"%s %s" % (alumno.padre.persona.nombre, alumno.padre.persona.apellidos))
        writer.searchAndReplacePage(page, "$CURSO_ESCOLAR$", u"%s-%s" 
                                % (unicode(settings.CURSO_ESCOLAR_ACTUAL), unicode(settings.CURSO_ESCOLAR_ACTUAL + 1)))
        writer.searchAndReplacePage(page, "$TUTOR$", u"%s" % tutor.profesor.persona if tutor else " -- ")
        evaluaciones = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
        contEv = 0
        numEv = len(evaluaciones)

        etiqueta_asignaturas = False
        promociona = False
        codigo_promocion = ''
        for ev in evaluaciones:
            if ev.is_apta():
                if ev.nombre == u"1":
                    suffix = "1"
                    evTexto = u"1ª"
                elif ev.nombre == u"2":
                    suffix = "2"
                    evTexto = u"2ª"
                elif ev.nombre == u"O" or ev.nombre == u"J":
                    suffix = "3"
                    evTexto = u"3ª"
                elif ev.nombre == u"U":
                    suffix = "4"
                    evTexto = u"Extraordinaria"
                if evTexto != u"Extraordinaria":
                    evTexto += u" Evaluación"
                else:
                    evTexto = u"Evaluación " + evTexto
                fechaEvaluacion = FECHAS_EVALUACIONES[int(suffix)-1]
                calif = alumno.getCalificaciones(ev.id)
                if calif["informe"]:
                    comp = CalificacionCompetencia._parseCompetencias(calif["informe"].informeCompetencias)
                    promociona = calif["informe"].promociona
                    codigo_promocion = calif["informe"].get_codigo_promocion_display()
                    for i in comp.keys():
                        cadena = u"$%s_%s$" % (i, suffix)
                        writer.searchAndReplacePage(page, cadena, comp[i])
                faltas = alumno.getFaltasEvaluacion(ev)

                if faltas:
                    for i in faltas.keys():
                        cadena = u"$%s_%s$" % (i, suffix)
                        writer.searchAndReplacePage(page, cadena, faltas[i])

                if calif["calificaciones"]:
                    if not etiqueta_asignaturas:
                        for i in range(len(calif["calificaciones"])):
                            cadena = u"$MATERIA%d$" % (i + 1)
                            writer.searchAndReplacePage(page, cadena, calif["calificaciones"][i].matricula.asignatura.nombreLargo)
                        etiqueta_asignaturas = True
                    from docencia.templatetags.emoticon import notaTextual
                    for i in range(len(calif["calificaciones"])):
                        cadena = u"$NOTA%d_%s$" % (i + 1, suffix)
                        if not calif["calificaciones"][i]:
                            nota = ''
                        else:
                            nota = notaTextual(calif["calificaciones"][i].nota)
                        writer.searchAndReplacePage(page, cadena, "%s" % nota)
                        logger.warn("Evaluacion %d y contEv %d", numEv, contEv)
                        if ev.nombre in ["O", "J"] and numEv in [3,4] or ev.nombre == "U":
                            cadena = "$OBS%d$" % (i + 1)
                            if (nota == '') or (not calif["calificaciones"][i].comentario):
                                coment = "--"
                                logger.warn("Viendo que la calificacion %s no tiene comentarios", calif["calificaciones"][i])
                            else:
                                coment = calif["calificaciones"][i].comentario
                                logger.warn("Viendo que la calificacion %s tiene un comentario %s", calif["calificaciones"][i], calif["calificaciones"][i].comentario)
                            writer.searchAndReplacePage(page, cadena, coment)
            contEv += 1
        pendientes = []
        for pend in alumno.getAsignaturasPendientes():
            for curso in alumno.getCursoAsignaturaPendiente(pend):
                pendiente = "%s %s %s (%s)" % (
                    pend.abreviatura, 
                    curso.nombre, 
                    curso.ciclo.nivel.nombre, 
                    alumno.getNotaAsignaturaPendiente(pend, curso))
                pendientes.append(pendiente)
        writer.searchAndReplacePage(page, "$ASIGNATURAS_PENDIENTES$", ", ".join(pendientes))
        #writer.searchAndReplacePage(page, "$OBSERVACIONES_GENERALES$", "¡¡ FELIZ VERANO !!")
        writer.searchAndReplacePage(page, "$OBSERVACIONES_GENERALES$", "")
        writer.searchAndReplacePage(page, "$EVALUACION_TEXTO$", evTexto)
        writer.searchAndReplacePage(page, "$FECHA_EVAL$", fechaEvaluacion.strftime('%d-%m-%Y'))

        if promociona:
            texto_promociona = "PROMOCIONA: %s" % codigo_promocion
        else:
            texto_promociona = "NO PROMOCIONA: %s" % codigo_promocion
        writer.searchAndReplacePage(page, "$PROMOCIONA$", texto_promociona)

        CalificacionCompetencia._limpiaBoletin(writer, page)

    @staticmethod
    def getDatosBoletinWebKit(alumno):
        """
            Devuelve los datos necesarios para rellenar un boletin de un alumno que
            se convertirá a PDF utilizando webkit.
        """

        tutor = alumno.getTutor()
        grupo = alumno.getGrupo().grupo
        out = {}
        out['alumno'] = "%s" % alumno.persona
        out['grupo'] = "%s" % grupo
        out['cial'] = alumno.cial

        if alumno.madre:
            out['madre'] = "%s" % alumno.madre
        else:
            out['madre'] = ""
        if alumno.padre:
            out['padre'] = "%s" % alumno.padre
        else:
            out['padre'] = ""
        out["cursoEscolar"] = "%s-%s" % (unicode(settings.CURSO_ESCOLAR_ACTUAL), unicode(settings.CURSO_ESCOLAR_ACTUAL + 1))
        out["tutor"] = "%s" % tutor if tutor else " --"
        evaluaciones = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)
        contEv = 0
        numEv = len(evaluaciones)
        evaluac = []
        evTexto = ""
        fechaEvaluacion = ""
        for ev in evaluaciones:
            evaluacion = {}
            if ev.nombre == u"1":
                suffix = "1"
                evTexto = u"1ª"
            elif ev.nombre == u"2":
                suffix = "2"
                evTexto = u"2ª"
            elif ev.nombre == u"O" or ev.nombre == u"J":
                suffix = "3"
                evTexto = u"3ª"
            elif ev.nombre == u"U":
                suffix = "4"
                evTexto = u"Extraordinaria"
            if evTexto != u"Extraordinaria":
                evTexto += u" Evaluación"
            else:
                evTexto = u"Evaluación " + evTexto
            evaluacion['id'] = suffix
            fechaEvaluacion = FECHAS_EVALUACIONES[int(suffix)-1]
            calif = alumno.getCalificaciones(ev.id)
            if calif['informe']:
                comp = CalificacionCompetencia._parseCompetencias(calif["informe"].informeCompetencias)
                evaluacion['informe'] = comp
            else:
                evaluacion['informe'] = ""

            faltas = alumno.getFaltasEvaluacion(ev)
            
            if faltas:
                evaluacion['faltas'] = faltas
            else:
                evaluacion['faltas'] = ""

            cals = []
            if calif["calificaciones"]:
                from docencia.templatetags.emoticon import notaTextual
                for i in range(len(calif["calificaciones"])):
                    calificaAsigna = {}
                    calificaAsigna['materia'] = calif['calificaciones'][i].matricula.asignatura.nombreLargo
                    calificaAsigna['nota'] = notaTextual(calif['calificaciones'][i].nota)
                    if contEv == numEv - 1:
                        if not calif["calificaciones"][i].comentario:
                            calificaAsigna['comentario'] = "--"
                        else:
                            calificaAsigna['comentario'] = calif["calificaciones"][i].comentario
                    cals.append(calificaAsigna)

            evaluacion['calificaciones'] = cals
            evaluac.append(evaluacion)
           
            contEv += 1

        out['evaluaciones'] = evaluac

        pendientes = ""
        for pend in alumno.getAsignaturasPendientes():
            if pendientes:
                pendientes += ", %s %s %s" % (pend.nombreCorto, grupo.curso, grupo.curso.ciclo.nivel.cursoEscolar)
            else:
                pendientes += "%s %s %s" % (pend.nombreCorto, grupo.curso, grupo.curso.ciclo.nivel.cursoEscolar)

        out["pendientes"] = pendientes
        out['evaluacionTexto'] = evTexto
        out['fechaEvaluacion'] = fechaEvaluacion.strftime('%d-%m-%Y')

        return out

    @staticmethod
    def _getEvaluacionNumerica(evaluacion):
        """
           Devuelve el equivalente numerico del nombre
           de la evaluacion dada, siguiendo la siguiente regla:

           1 = 1
           2 = 2
           O = 3
           U = 4

            Otra de esas maravillosas decisiones de diseño de Pincel.
        """
        if unicode(evaluacion.nombre) == u"1":
            return 1
        elif unicode(evaluacion.nombre) == u"2":
            return 2
        elif unicode(evaluacion.nombre) == u"O":
            return 3
        elif unicode(evaluacion.nombre) == u"J":
            return 3
        elif unicode(evaluacion.nombre) == u"U":
            return 4
        elif unicode(evaluacion.nombre) == u"3":
            return 3
        else:
            logger.error("Codigo de evaluacion desconocido")
            sys.exit(-1)


    
