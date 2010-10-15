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

import logging
import os
import shutil
import datetime
import md5
from django.conf import settings
from django.utils.translation import ugettext as _
from data_repo import DataRepo

log = logging.getLogger('galotecnia')

class FileManager(DataRepo):

    def save_post_file(self, post_data):
        filename = post_data['file'].name.lower()
        file_date = post_data['file_date']
        filedir = self.build_buffer_path(file_date)
        if not os.path.isdir(filedir):
            os.mkdir(filedir)
        filepath = os.path.join(filedir, filename)
        if os.path.isfile(filepath):
            os.unlink(filepath)
        destination = open(filepath, 'wb+')
        hash = md5.new()
        for chunk in post_data['file'].chunks():
            hash.update(chunk)
            destination.write(chunk)
        destination.close()
        md5_local = hash.hexdigest()
        md5_post = post_data['md5']
        if md5_local != md5_post:
            os.unlink(filepath)
            error_msg = _(u'Fichero %(filename)s incorrecto md5 calculado %(md5_local)s, md5 suministrado %(md5_post)s' % {
                    'filename': filename,
                    'md5_local': md5_local,
                    'md5_post': md5_post }
                )
            log.error(error_msg)
            raise ValueError(error_msg)

    def upload_end(self, data_date):
        src = self.build_buffer_path(data_date)
        if not os.path.isdir(src):
            raise RuntimeError(_(u'No existe el directorio %s, no se puede mover' % src))
        self.check_data_integrity(src, data_date)
        dst = self.build_data_path(data_date)
        if os.path.isdir(dst):
            raise RuntimeError(_(u'Ya existe un directorio %(src)s en %(data_dir)s' % {'src':src, 'data_dir':self.data_dir}))
        shutil.move(src, dst)

