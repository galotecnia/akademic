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

import re
import logging
import os
import shutil
import datetime
import md5
from django.conf import settings
from django.utils.translation import ugettext as _
import zipfile

log = logging.getLogger('akademicLog')
settings.DATA_BACKEND = 'pincel'
import_str = 'from %s.importacion import IMPORT_FILES' % settings.DATA_BACKEND
exec import_str

class DataRepo():

    def __init__(self, buffer_dir = None, data_dir = None):
        if (not buffer_dir) and (not settings.EXCHANGE_BUFFER_DIR):
            error_msg = _(u"No está definido EXCHANGE_BUFFER_DIR en settings.")
            log.error (error_msg)
            raise RuntimeError (error_msg)
        if (not data_dir) and (not settings.EXCHANGE_DATA_DIR):
            error_msg = _(u"No está definido EXCHANGE_DATA_DIR en settings.")
            log.error (error_msg)
            raise RuntimeError (error_msg)
        self.buffer_dir = buffer_dir or settings.EXCHANGE_BUFFER_DIR
        self.data_dir = data_dir or settings.EXCHANGE_DATA_DIR

    def build_data_path(self, d, filename = None):
        if filename:
            return  os.path.join(self.data_dir, d.strftime ('%y-%m-%d_%H:%M'), filename)
        return os.path.join(self.data_dir, d.strftime ('%y-%m-%d_%H:%M'))

    def build_buffer_path(self, d, filename = None):
        if filename:
            return  os.path.join(self.buffer_dir, d.strftime ('%y-%m-%d_%H:%M'), filename)
        return os.path.join(self.buffer_dir, d.strftime ('%y-%m-%d_%H:%M'))

    def check_data_integrity(self, dir, data_date = None):
        if data_date:
            zip_name = self.build_buffer_path(data_date) + '/' + data_date.strftime('%Y%m%d_%H%M%S') + '.zip'
            zip_archive = zipfile.ZipFile(zip_name, 'r')
            if zipfile.is_zipfile(zip_name):
                for info in zip_archive.infolist():
                    log.debug("Recibido y descomprimiendo el fichero ", info.filename)
                    data = zip_archive.read(info.filename)
                    out_name = self.build_buffer_path(data_date, info.filename)
                    log.debug("Se va a crear el fichero ", out_name)
                    fout = open(out_name, 'w')
                    fout.write(data)
                    fout.close()
            else:
                error_msg = _(u"El fichero recibido no es un zip")
                log.error(error_msg)
                raise RuntimeError(error_msg)
            os.remove(zip_name)

        error_msg = ''
        for f in IMPORT_FILES:
            print os.path.join(dir, f)
            if not os.path.isfile(os.path.join(dir, f)):
                error_msg += _(u'No se encuentra el fichero %s necesario para la importación en %s directorio\n' % (f,dir))
        print error_msg
        if error_msg:   
            log.error(error_msg)
            raise RuntimeError(error_msg)

    def find_data_dates(self):
        dates = []
        for d in os.listdir(self.data_dir):
            if os.path.isdir(os.path.join (self.data_dir, d)):
                try:
                    d = map(int, re.split ("[-_:]", d))
                    d[0] += 2000
                    dates.append(datetime.datetime(*d))
                except ValueError:
                    pass
        dates.sort(reverse = True)
        return dates

    def get_md5(self, filename):
        hash = md5.new()
        hash.update(open(filename).read())
        return hash.digest()

    def file_is_modified(self, d_previous, d_last, filename):
        if not d_previous: # No hay datos anteriores
            return True
        h_previous = h_last = None
        if os.path.isfile (self.build_data_path(d_previous, filename)):
            h_previous = self.get_md5(self.build_data_path(d_previous, filename))
        if os.path.isfile (self.build_data_path(d_last, filename)):
            h_last = self.get_md5(self.build_data_path(d_last, filename))
        if h_previous != h_last:
            return True
        return False
