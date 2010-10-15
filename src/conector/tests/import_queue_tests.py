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
import tempfile
import os
import datetime
from django.test import TestCase
from conector.import_queue import ImportQueue, LOG_FILE

class ImportQueueTest(TestCase):
    def test_get_todo_list_no_dir(self):
        dir = tempfile.mkdtemp()
        i = ImportQueue(dir)
        self.assertEqual(i.todo, [])
        os.rmdir(dir)

    def test_get_todo_list_dir_done (self):
        dir = tempfile.mkdtemp()
        now = datetime.datetime.now()
        work_dir = os.path.join(dir, now.strftime ('%y-%m-%d_%H:%M'))
        os.mkdir (work_dir)
        f = open(os.path.join(work_dir, LOG_FILE), 'w')
        f.write ('test')
        f.close ()
        i = ImportQueue(dir)
        self.assertEqual(i.todo, [])
        os.unlink (os.path.join(work_dir, LOG_FILE))
        os.rmdir(work_dir)
        os.rmdir(dir)

    def test_get_todo_list_dir_todo (self):
        dir = tempfile.mkdtemp()
        now = datetime.datetime.now()
        work_dir = os.path.join(dir, now.strftime ('%y-%m-%d_%H:%M'))
        os.mkdir (work_dir)
        i = ImportQueue(dir)
        self.assertEqual(i.todo[0].date(), now.date())
        self.assertEqual(i.todo[0].hour, now.hour)
        self.assertEqual(i.todo[0].min, now.min)
        os.rmdir(work_dir)
        os.rmdir(dir)
