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
from docencia.models import Profesor
from pas.models import Pas
from models import Recurso
from addressbook.models import PersonaPerfil

import logging

log = logging.getLogger('galotecnia')

class RecursoPermission(permissions.BasePermission):
    
    label = 'recursopermission'
    check = ('reservar_recurso', 'asignar_recurso', 'acceso_recurso',)

    def acceso_recurso(self, recurso = None):
        
        if recurso and not recurso.actualmenteDisponible:
            log.debug(u"El recurso %s no esta disponible actualmente" % recurso)
            return False
        try:
            profile = self.user.get_profile()
        except PersonaPerfil.DoesNotExist:
            # Si no tiene perfil no sabemos que tipo de persona es
            # por lo tanto, denegamos el acceso
            log.error(u"No existe el perfil asociado al usuario %s" % self.user.username)
            return False
        try:
            profesor = profile.profesor
        except Profesor.DoesNotExist:
            try:
                pas = profile.pas
            except Pas.DoesNotExist:
                log.debug(u"El usuario %s no puede ver los recursos" % self.user.username)
                return False
        return True

    def reservar_recurso(self, recurso = None):
   
        if recurso and not recurso.actualmenteDisponible: 
            log.debug(u"El recurso %s no esta disponible actualmente" % recurso)
            return False
        try:
            profile = self.user.get_profile()
        except PersonaPerfil.DoesNotExist:
            # Si no tiene perfil no sabemos que tipo de persona es
            # por lo tanto, denegamos el acceso
            log.error(u"No existe perfil asociado al usuario %s" % self.user.username)
            return False
        try:
            profesor = profile.profesor
        except Profesor.DoesNotExist:
            try:
                pas = profile.pas
            except Pas.DoesNotExist:
                log.debug(u"El usuario %s no puede reservar recursos" % self.user.username)
                return False
        return True

    def asignar_recurso(self, recurso = None):
       
        if recurso and not recurso.actualmenteDisponible:
            log.debug(u"El recurso %s no esta disponible actualmente")
            return False 
        try:
            profile = self.user.get_profile()
        except PersonaPerfil.DoesNotExist:
            # Si no tiene perfil no sabemos que tipo de persona es
            # por lo tanto, denegamos el acceso
            log.error(u"No existe perfil asociado al usuario %s" % self.user.username)
            return False
        try:
            pas = profile.pas
        except Pas.DoesNotExist:
            log.debug(u"El usuario %s no puede asignar el recursos" % self.user.username)
            return False
        return True

authority.register(Recurso, RecursoPermission)
