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
import sys
import os
import re
import datetime
import shutil
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.management.commands.dumpdata import Command as dumpdata
from data_repo import DataRepo

import_str = 'import %s.importacion as backend' % settings.DATA_BACKEND
exec import_str

log = logging.getLogger('galotecnia')

LOG_FILE = 'log.txt'

class ImportQueue(DataRepo):
    def __init__(self, data_dir = None, dry_run = False, tabular = True, variable = True, excel = True, delete = True): 
        if (not data_dir) and (not settings.EXCHANGE_DATA_DIR):
            error_msg = _(u"No está definido EXCHANGE_DATA_DIR en settings.")
            log.error(error_msg)
            raise RuntimeError(error_msg)
        self.data_dir = data_dir or settings.EXCHANGE_DATA_DIR
        # Comentado porque no se usa. 
        self.todo = self.get_todo_list()
        # Opciones de control de ejecucion
        self.dry_run = dry_run
        self.tabular = tabular
        self.variable = variable
        self.excel = excel
        self.delete = delete

    def get_todo_list(self):
        dates = self.find_data_dates()
        todo = []
        for d in dates:
            if not os.path.isfile(os.path.join(self.build_data_path(d), LOG_FILE)):
                todo.append(d)
        return todo

    def django_dumpdata(self, filename):
        apps = [a.split('.')[-1] for a in settings.INSTALLED_APPS]
        if 'django_extensions' in apps:
            apps.remove('django_extensions')
        dd = dumpdata()
        dumped_data = open(filename, 'w')
        #dumped_data.write(dd.handle(format='json', indent=2, *apps))
        dumped_data.write(dd.handle(format='json', *apps))
        dumped_data.close()

    def sgbd_dumpdata(self, filename):
        if settings.DATABASE_ENGINE == 'sqlite3':
            if os.path.isfile (settings.DATABASE_NAME):
                shutil.copy2(settings.DATABASE_NAME, filename)
        elif settings.DATABASE_ENGINE == 'mysql':
            print "mysqldump --- NO IMPLEMENTADO"
        elif settings.DATABASE_ENGINE == 'postgresql':
            print "pg_dump --- NO IMPLEMENTADO"
        else:
            print "No hay soporte para el sgdb. %s" % settings.DATABASE_ENGINE

    def import_process(self, d, verbosity=1, debug=None):
        now = datetime.datetime.now ()
        log.debug("Verificando la integridad de la copia.")
        self.check_data_integrity(self.build_data_path(d))
        if not debug:
            log.debug("Creando copias de seguridad de la base de datos actual.")
            if not self.dry_run:
                self.django_dumpdata (
                    self.build_data_path(
                        d, 'fixtures_antes_de_importar_%s.json' % now.strftime('%Y%m%d_%H:%M:%S'))
                    )
                self.sgbd_dumpdata (
                    self.build_data_path(
                        d, '%s_antes_de_importar_%s.sql' % (settings.DATABASE_ENGINE, now.strftime('%Y%m%d_%H:%M:%S')))
                    )
        else:
            log.warn("Ignorando el proceso de backup,")
        log.debug("Iniciando la importación.")
        import_log = backend.start_import(self.build_data_path(d), self.dry_run, self.tabular, self.variable, self.excel, self.delete)
        log.debug("Finalizando la importación.")
        log.debug("Creando copias de seguridad de la base de datos post-importacion.")
        if not self.dry_run:
            self.django_dumpdata (
                self.build_data_path(
                    d, 'fixtures_despues_de_importar_%s.json' % now.strftime('%Y%m%d_%H:%M:%S'))
                )
            self.sgbd_dumpdata (
                self.build_data_path(
                    d, '%s_despues_de_importar_%s.sql' % (settings.DATABASE_ENGINE, now.strftime('%Y%m%d_%H:%M:%S')))
                )
        log.debug("Escribiendo el log del proceso.")
        if not self.dry_run:
            open(self.build_data_path(d, LOG_FILE), 'w').write(import_log.encode('utf-8'))
        # TODO: Enviar un correo electrónico al "admin" con el log de la imporación.


