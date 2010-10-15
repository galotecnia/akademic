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

import authority
from authority import permissions

# Modelos a los que se les asocia permisos
from models import *
from horarios.models import Horario
from padres.models import Padre
from pas.models import Pas
from recursos.models import Recurso

import logging

log = logging.getLogger('galotecnia')


class GrupoAulaPermission(permissions.BasePermission):

    label = 'grupoaula_permission'
    check = ('has_class_privs',)

    def has_class_priv(self, grupoaula, asignatura = None):
       
        try: 
            profile = self.user.get_profile()
        except PersonaPerfil.DoesNotExist:
            # Si no tiene perfil no sabemos que tipo de persona es
            # por lo tanto, denegamos el acceso
            log.error(u"No existe perfil asociado al usuario %s" % self.user.username)
            return False
        profesor = None
        if self.user.has_perm('director'): # Si se desea añadir comprobación de más permisos de django, aqui
            return True
        else:
            try:
                profesor = profile.profesor
            except Profesor.DoesNotExist:
                # Si se quieren añadir más roles que tengan acceso a
                # la información de una clase, se añadirían aquí
                pass 
        if profesor is None:
            log.error(u"El usuario %s no es profesor" % self.user)
            return False
        jefe = profesor.jefeestudios_set.all()
        for j in jefe:
            if j.nivel == grupoaula.curso.ciclo.nivel:
                return True 
        coordinador = profesor.coordinadorciclo_set.all()
        for c in coordinador:
            if c.ciclo == grupoaula.curso.ciclo:
                return True
        tutor = profesor.tutor_set.all()
        for t in tutor:
            if t.grupo == grupoaula:
                return True
        try:
            if asignatura:
                clase = Horario.objects.get(grupo = grupoaula, profesor = profesor, asignatura = asignatura)
            else:
                clase = Horario.objects.get(grupo = grupoaula, profesor = profesor)
            return True
        except Horario.DoesNotExist:
            log.error(u"El profesor %s no tiene privilegios para acceder a %s" % (profesor, grupoaula))
            return False
        return False

class AlumnoPermission(permissions.BasePermission):
    
    label = 'alumno_permission'
    check = ('has_alu_priv', )
    
    def has_alu_priv(self, alumno, asignatura = None):
        """
            Comprueba si el usuario tiene permisos sobre el alumno pasado como argumento
        """
        log.debug("Obtenemos el perfil del usuario %s para el alumno %s", self.user, alumno)
        try:
            profile = self.user.get_profile()
        except PersonaPerfil.DoesNotExist:
            # Si no tiene perfil no sabemos que tipo de persona es
            # por lo tanto, denegamos el acceso
            log.error(u"No existe perfil asociado al usuario %s" % self.user.username)
            return False

        if self.user.has_perm('director'): 
            log.debug("El usuario es director, así que se le concede permisos")
            return True

        # TODO: Si se desea añadir más comprobaciones de permisos de django, aqui
        profesor = None
        padre = None
        try:
            padre = profile.padre
        except Padre.DoesNotExist:
            try:
                profesor = profile.profesor
            except Profesor.DoesNotExist:
                # TODO: Si se quieren añadir más roles que tengan acceso a
                # la información de una clase, se añadirían aquí
                pass

        if padre:
            log.debug("El usuario es padre, comprobamos potestad")
            if alumno.padre == padre and alumno.potestadPadre: 
                return True
            if alumno.madre == padre and alumno.potestadMadre:
                return True
            log.debug(u"%s no puede acceder a la info de %s" % (padre.persona, alumno))
            return False 

        if profesor is None:
            log.error(u"El usuario %s no es profesor" % self.user)
            return False

        # Usuario profesor
        for ga in alumno.grupoaulaalumno_set.exclude(grupo__seccion = 'Pendientes'):
            log.debug("GrupoAulas para el alumno: %s", ga)
            jefe = profesor.jefeestudios_set.all()
            for j in jefe:
                if j.nivel == ga.grupo.curso.ciclo.nivel:
                    return True 
            coordinador = profesor.coordinadorciclo_set.all()
            for c in coordinador:
                if c.ciclo == ga.grupo.curso.ciclo:
                    return True
            tutor = profesor.tutor_set.all()
            for t in tutor:
                if t.grupo == ga.grupo:
                    return True
            try:
                if asignatura:
                    clase = Horario.objects.get(grupo = ga.grupo, profesor = profesor, asignatura = asignatura)
                else:
                    clase = Horario.objects.get(grupo = ga.grupo, profesor = profesor)
                return True
            except Horario.DoesNotExist:
                log.error(u"El profesor %s no tiene privilegios para acceder a %s" % (profesor, alumno))
                return False
        return False

authority.register(Alumno, AlumnoPermission)
authority.register(GrupoAula, GrupoAulaPermission)
