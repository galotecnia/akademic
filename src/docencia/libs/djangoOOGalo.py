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

from django.http import HttpResponse
from django.conf import settings
from oogalo import Writer
from com.sun.star.uno import Exception as UnoException
import uno
import tempfile
import os
import subprocess
import signal
import time
import unicodedata

TEMPFILE_PREFIX='oogalo'
TEMPDIR='/opt/tmp'

NoConnectionException = uno.getClass("com.sun.star.connection.NoConnectException")

class DjangoWriter (Writer):
    def __init__ (self):
        self.OOpid = None
        while True:
            try:
                Writer.__init__(self)
                break
            except UnoException, e:
                if (e.Message == 'OpenOffice processs not found') and (settings.DEBUG):
                    self.start_OOo()
                else:
                    raise e

    def HttpResponseFILE (self, filetype = 'odt', filename = None):
        tf = tempfile.NamedTemporaryFile(prefix = TEMPFILE_PREFIX, dir = TEMPDIR)
        temporal = tf.name
        tf.close ()
        if filetype == 'odt':
            mimetype = 'application/vnd.oasis.opendocument.text'
            self.saveODT(temporal)
        elif filetype == 'pdf':
            mimetype = 'application/pdf'
            self.savePDF(temporal)
        elif filetype == 'html':
            self.saveFile (temporal, "HTML (StarWriter)")
            mimetype = 'text/html'
        elif filetype == 'doc':
            self.saveFile (temporal, "MS Word 97")
            mimetype = 'application/msword'
        elif filetype == 'rtf':
            self.saveFile (temporal, "Rich Text Format")
            mimetype = 'application/rtf'
        elif filetype == 'txt':
            self.saveFile (temporal, "Text (encoded)")
            mimetype = 'text/plain'
        else:
            raise TypeError
        buffer = open (temporal, 'r').read()
        os.unlink (temporal)
        response = HttpResponse(mimetype=mimetype)
        if filename.split('.')[-1:] != filetype: filename += ".%s" % filetype
        filename = unicodedata.normalize('NFKD', unicode(filename)).encode('ASCII', 'ignore')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        response.write(buffer)
        self.close()
        if self.OOpid is not None:
            print "Killing OpenOffice.org pid %s" % self.OOpid
            os.kill (self.OOpid, signal.SIGTERM)
        return response

    def HttpResponsePDF (self, filename = None):
        return self.HttpResponseFILE (filetype = 'pdf', filename = filename)

    def HttpResponseODT (self, filename = None):
        return self.HttpResponseFILE (filetype = 'odt', filename = filename)

    def HttpResponseDOC (self, filename = None):
        return self.HttpResponseFILE (filetype = 'doc', filename = filename)

    def HttpResponseRTF (self, filename = None):
        return self.HttpResponseFILE (filetype = 'rtf', filename = filename)

    def HttpResponseTXT (self, filename = None):
        return self.HttpResponseFILE (filetype = 'txt', filename = filename)

    def HttpResponseHTML (self, filename = None):
        return self.HttpResponseFILE (filetype = 'html', filename = filename)

    def start_OOo(self):
        ooffice = '%s -nologo -nodefault -accept=socket,host=%s,port=%s;urp;' % (
            settings.OO_EXECUTABLE,
            settings.OO_HOST,
            settings.OO_PORT,)
        self.OOpid = subprocess.Popen(ooffice.split (' ')).pid
        print "OpenOffice.org Started PID: %s" % self.OOpid
        print "Sleep 2 second"
        time.sleep (2)


