#!/usr/bin/env python
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

import ConfigParser
from django.conf import settings

#
# Devuelve un objeto ConfigParser con la configuración de Akademic
#
def readConfigFile():
	cp = ConfigParser.ConfigParser()
	filelist = cp.read(settings.CONFIG_FILE)
	if len(filelist) == 0:
		raise IOError("No se ha encontrado el archivo de configuración: %s" % settings.CONFIG_FILE)
	return cp
#
# Obtiene un parámetro del archivo de configuración de Akademic
#
def getConfig (section, parameter, default = None):
    try:
        cp = readConfigFile()
    except IOError, e:
        #print "Fichero:", settings.CONFIG_FILE
        if default is None:
            raise e
        return default
    try:
        return cp.get(section, parameter)
    except ConfigParser.NoOptionError:
        if default is None:
            raise ConfigParser.NoOptionError (section, parameter)
        return default
    except ConfigParser.NoSectionError:
        if default is None:
            raise ConfigParser.NoSectionError (section)
        return default

def getSupervisores ():
	cp = readConfigFile()
	supervisores = []
	try:
		for s in cp.options('supervisores'):
			supervisores.append (cp.get('supervisores', s))
		return supervisores
	except ConfigParser.NoOptionError:
		return []
	except ConfigParser.NoSectionError:
		return []
