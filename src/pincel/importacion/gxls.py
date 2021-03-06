#!/usr/bin/python
# -*- encoding: utf-8 -*-
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


import pyExcelerator

def getDict (xlsFile):
	def getRows (data):
		numCols = 0
		for row, col in data.keys():
			numCols = max (numCols, col)
		listOfRows = {}
		for row,col in data.keys():
			if row != 0:
				if listOfRows.has_key (row):
					listOfRows[row][col] = data[(row, col)]
				else:
					listOfRows[row] = [''] * (numCols + 1)
					listOfRows[row][col] = data[(row, col)]
		return listOfRows.values ()
		
		
	xls = pyExcelerator.ImportXLS.parse_xls(xlsFile)
	data = {}
	for sheet in xls:
		name = sheet[0]
		rows = getRows (sheet[1])
		data[name] = rows
	return data



if __name__ == '__main__':
	print getDict ('/tmp/PROFESORES Y TUTORES AKADEMIC 24 09 08.xls')
