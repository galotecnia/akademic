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
from conector.file_manager import FileManager

class Chunks:
    def __init__ (self, name):
        self.name = name

    def chunks(self):
        return ['uno', 'dos', 'tres', 'cuatro']

class FileManagerTest(TestCase):

    def setUp(self):
        self.now = datetime.datetime.now()
        self.filename = 'test_filename.txt'
        self.post_data = {
            'file': Chunks (self.filename),
            'file_date': self.now,
            'md5': 'ae918f68c27f52d795c53a0d432e1f8c'
        }
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        fm = FileManager(self.dir)
        os.rmdir(fm.build_buffer_path(self.now))
        os.rmdir(self.dir)

    def test_save_post_file_ok(self):
        fm = FileManager(self.dir)
        fm.save_post_file(self.post_data)
        self.assertTrue(os.path.isfile(os.path.join(fm.build_buffer_path(self.now), self.filename)))
        os.unlink(os.path.join(fm.build_buffer_path(self.now), self.filename))

    def test_save_post_file_wrong_md5(self):
        self.post_data['md5'] = 'malamente'
        fm = FileManager(self.dir)
        self.assertRaises(ValueError, fm.save_post_file, self.post_data)
