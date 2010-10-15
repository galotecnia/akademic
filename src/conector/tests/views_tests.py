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
import shutil

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from conector.import_queue import ImportQueue
from conector.file_manager import FileManager
from pincel.importacion import IMPORT_FILES

class ViewsTest(TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        self.c = Client()
        self.post_data = {
           'username':'testuser',
           'password':'testpassword',
           'md5':'33eea6733a175e558f1bd162af8fb4b8',
           'file': open(os.path.join(os.path.dirname(__file__), 'test_file.txt')),
           'file_date': self.now.strftime ('%Y-%m-%d %H:%M:%S'),
        }

        self.post_data_end_upload = {
           'username':'testuser',
           'password':'testpassword',
           'date': self.now.strftime ('%Y-%m-%d %H:%M:%S'),
        }

    def tearDown(self):
        fm = FileManager()
        iq = ImportQueue()
        if os.path.isdir (fm.build_buffer_path(self.now)):
            shutil.rmtree(fm.build_buffer_path(self.now))
        if os.path.isdir (iq.build_data_path(self.now)):
            shutil.rmtree(iq.build_data_path(self.now))

    def test_upload_data_file_ok(self):
        response = self.c.post(reverse('upload_data_file'), self.post_data)
        self.assertEqual (response.status_code, 200)

    def test_upload_data_file_no_auth(self):
        self.post_data['username'] = 'wrong_username'
        response = self.c.post(reverse('upload_data_file'), self.post_data)
        self.assertEqual (response.status_code, 403)

    def test_upload_data_file_auth_no_rights(self):
        self.post_data['username'] = 'norights'
        response = self.c.post(reverse('upload_data_file'), self.post_data)
        self.assertEqual (response.status_code, 403)

    def test_upload_end_no_src_dir(self):
        response = self.c.post(reverse('end_upload_data'), self.post_data_end_upload)
        self.assertEqual (response.status_code, 400)
        self.assertContains (response, 'No existe el directorio', status_code=400)

    def test_upload_end_no_all_files(self):
        self.c.post(reverse('upload_data_file'), self.post_data)
        response = self.c.post(reverse('end_upload_data'), self.post_data_end_upload)
        self.assertEqual (response.status_code, 400)
        self.assertContains (response, 'No se encuentra el fichero', len (IMPORT_FILES), status_code=400)

    def upload_all_files(self):
        dir = tempfile.mkdtemp()
        test_file_content = open(os.path.join(os.path.dirname(__file__), 'test_file.txt'), 'r').read ()
        for f in IMPORT_FILES:
            test_file = open (os.path.join (dir, f), 'w')
            test_file.write (test_file_content)
            test_file.close ()
            self.post_data['file'] = open (os.path.join (dir, f))
            response = self.c.post(reverse('upload_data_file'), self.post_data)
            self.assertEqual (response.status_code, 200)
            os.unlink (os.path.join (dir, f))
        os.rmdir (dir)

    def test_upload_end_ok(self):
        self.upload_all_files()
        response = self.c.post(reverse('end_upload_data'), self.post_data_end_upload)
        self.assertContains (response, 'ok', status_code=200)

    def test_upload_end_dst_exist(self):
        self.upload_all_files()
        iq = ImportQueue()
        os.mkdir (iq.build_data_path (self.now))
        response = self.c.post(reverse('end_upload_data'), self.post_data_end_upload)
        self.assertContains (response, 'Ya existe un directorio', status_code=400)
