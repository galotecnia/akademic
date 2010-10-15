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
from pincel.importacion.importer import Importer
from pincel.models import Isla

from tests.mocker import Mocker, ANY, expect, ARGS, KWARGS

#work in progress
GRUPO_DATOS_SIMPLES_TESTS = {    
    'Islas': { 
        'tablapincel': 'islas',
        'modelo': Isla
    },
}

class FakeRow(dict):
    isDeleted = False

class ImporterTests(TestCase):
    def setUp(self):
        self.mocker = Mocker()
        self.mock_repo = self.mocker.mock()
        expect(self.mock_repo.find_data_dates()).result([datetime.datetime.now()]).count(1)
        expect(self.mock_repo.file_is_modified(ANY, ANY, ANY)).result(True).count(1)
        expect(self.mock_repo.build_data_path(ANY, ANY)).result(None).count(1)
        self.db = []
        self.db_mock = self.mocker.proxy(self.db)
        expect(self.db_mock.openFile(ARGS, KWARGS)).result(True)
        expect(self.db_mock.close()).result(None)
        self.mocker.replay()

    def tearDown(self):
        self.mocker.restore()

    def test_import_simple_data(self):
        self.db.append(FakeRow(DEN_CORTA='Tenerife', CODIGO_INT='1',DEN_LARGA='Isla de Tenerife'))
        self.db.append(FakeRow(DEN_CORTA='La Gomera', CODIGO_INT='2',DEN_LARGA='Isla de La Gomera'))
        
        im = Importer('fakefakefakefake', self.db_mock, self.mock_repo)
        im._import_simple_data(nombre='Islas')
        self.assertEqual(Isla.objects.get(idPincel = 1).nombreCorto, 'Tenerife')
        self.assertEqual(Isla.objects.get(idPincel = 2).nombreCorto, 'La Gomera')
        self.mocker.verify()
        
    def test_import_simple_data_iterative(self):
        """
            More consistent and iterative way of testing the importer.
            Testing the simple ones.
        """
        pass

