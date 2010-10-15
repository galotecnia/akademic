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

from django.http import HttpResponse
from utils.icalendar import Calendar, Event, UTC

import datetime

# 1 hora
DURACION_CITA_POR_DEFECTO = datetime.timedelta(0, 0, 0, 0, 20)

def events2iCalendar(eventos, ical = None):
	"""
		Devuelve un objeto Calendar con los eventos pasados como
		argumento.
	"""
	if ical == None:
		ical = Calendar()
		ical.add('prodid', 'Akademic v2.0')
		ical.add('version', '2.0')
	
	for e in eventos:
		event = Event()
		event.add('summary', e['resumen'])
		event.add('dtstart', e['comienzo'])
		event.add('dtend', e['final'])
		event.add('dtstamp', datetime.datetime.today())
		# TODO: Cambiar el UID por algo más descriptivo
		event.add('uid', e['uid'])
		ical.add_component(event)

	return ical

def HttpResponseCalendar(ical):
	"""
		Devuelve un HttpResponse de Django con el archivo iCalendar
	"""
	ical_str = ical.as_string()
	response = HttpResponse()
	response['Accept-Ranges'] = 'bytes'
	response['Content-Length'] = str(ical_str.__len__())
	response['Content-Type'] = 'text/calendar'
	response.write(ical_str)
	return response

