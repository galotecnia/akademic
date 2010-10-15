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

from django.http import HttpResponseForbidden, HttpResponse
import cStringIO as StringIO
import re
import urllib
import urlparse
import os
from HTMLParser import HTMLParser
from string import strip

from customExceptions import *

class expandCSS(HTMLParser):
	sitio=""
	src = ""
#	debug = True
	debug = False

	def __init__ (self, Sitio):
		HTMLParser.__init__(self)
		self.sitio = Sitio
		self.startEndTagReaded = False

	def parseImg (self, atributos):
		ref=""
		self.src += "<img "
		for h in atributos:
			if h[0] == "src":
				u = urlparse.urlparse (h[1])
				if u[0] == "":
					# Ruta a un fichero local
					# Esto evidentemente no mola en absoluto.
					# Hay que hacerlo porque con el servidor de desarrollo de django, 
					# hasta que no procesa 1 petición no procesa la siguiente y como esto
					# se solicita a si mismo el css se queda atascado.
					#ref = os.path.join(os.getcwd(), h[1].lstrip("/"))
					ref = os.path.join("/home/akademic/akademic3/akademic2/", h[1].lstrip("/"))
				else:
					ref = urlparse.urljoin(self.sitio,h[1])
				self.src += 'src="%s" ' % ref
			else:
				self.src += '%s="%s" ' % (h[0], h[1])
		self.src += "/>"

	def handle_starttag(self,tag,atributos):
		if self.startEndTagReaded:
			return
		if tag == "img":
			self.parseImg (atributos)
		else:
			self.src += self.get_starttag_text()
		if self.debug:
			print "handle_startag"
			self.src += "handle_startag"

	def handle_endtag(self,tag):
		if self.startEndTagReaded:
			self.startEndTagReaded = False
			return
		if tag == "img":
			self.parseImg (atributos)
		else:
			#self.src += self.get_starttag_text()
			self.src += "</" + tag + ">"
		if self.debug:
			print "handle_endtag"
			self.src += "handle_endtag"

	def handle_startendtag(self,tag,atributos):
		if tag == "img":
			self.parseImg (atributos)
			self.startEndTagReaded = True
		elif tag == "link":
			ref=""
			css = False
			screen = True
			for h in atributos:
				if h[0] == "href":
					u = urlparse.urlparse (h[1])
					if u[0] == "":
						# Ruta a un fichero local
						# Esto evidentemente no mola en absoluto.
						# Hay que hacerlo porque con el servidor de desarrollo de django, 
						# hasta que no procesa 1 petición no procesa la siguiente y como esto
						# se solicita a si mismo el css se queda atascado.
						#ref = os.path.join(os.getcwd(), h[1].lstrip("/"))
						ref = os.path.join("/home/akademic/akademic3/akademic2/", h[1].lstrip("/"))
					else:
						ref = urlparse.urljoin(self.sitio,h[1])
				elif h[0] == "type":
					if h[1] == "text/css":
						css = True
				elif h[0] == "media":
					if h[1].find("screen"):
						screen = False
			if ((css == True) and (ref != "") and (screen)):
				if u[0] == "":
					u = open (ref)
				else:
					u = urllib.urlopen (ref)
				style = u.read ()
				u.close ()
				self.src = '<style type="text/css">%s</style>' % style
			else:
				self.src += self.get_starttag_text()
		else:
			self.src += self.get_starttag_text()

		self.startEndTagReaded = True
		if self.debug:
			print "handle_startendtag"
			self.src += "handle_startendtag"


	def handle_comment(self,comment):
		self.src += "<!-- " + comment + "-->"
		if self.debug:
			print "handle_comment"
			self.src += "handle_comment"


	def handle_entityref(self, ref):
		self.src += self.get_starttag_text()
		if self.debug:
			print "handle_entityref"
			self.src += "handle_entityref"


	def handle_charref(self, ref):
		self.src += self.get_starttag_text()
		if self.debug:
			print "handle_charref"
			self.src += "handle_charref"

	def handle_data (self, data):
		self.src += data
		if self.debug:
			print "handle_data"
			self.src += "handle_data"

class customMiddleWare:
	def __init__(self):
		#self.findCSS = re.compile(".*link.*")
		pass

	def process_request(self, request):
		pass

	def process_view(self, request, view_func, view_args, view_kwargs):
		pass

	def process_response(self, request, response):
		if 'aspdf' in request.GET:
			if request.GET['aspdf'] == "True":
				# Hay que colocar aquí la url base del sitio y tal ...
				# (seguro que esto se puede sacar de por ahí)
				p = expandCSS ("http://%s/" % request.META["HTTP_HOST"])
				p.feed (response.content)
				result = StringIO.StringIO()
				content = p.src.decode("utf8").encode("latin1")
				html = content
				#pdf = pisa.CreatePDF(
				#	src = StringIO.StringIO(p.src.encode("ISO-8859-1")),
				#	dest = result,
				#	debug = 0,
				#	show_error_as_pdf = True,
				#	)
				pdf = pisa.CreatePDF(html, result)
				if not pdf.err:
					return HttpResponse(
						result.getvalue(),
						mimetype='application/pdf')
		return response

	def process_exception(self, request, exception):
		if isinstance(exception, UnauthorizedAccess):
			msg = '<h1>Acceso no autorizado</h1>'
			msg += str(exception)
			return HttpResponseForbidden(msg)
		if isinstance(exception, FatalError):
			msg = '<h1>Error Fatal</h1>'
			msg += str(exception)
			return HttpResponse(msg)
		return None

