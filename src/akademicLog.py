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
from django.core.mail import send_mail
from django.conf import settings

class AkademicLog:
    def __init__ (self):
        self.logger = logging.getLogger("galotecnia")

    def process_view (self,request, view_func, view_args, view_kwargs):
        try:
            remote = request.META['REMOTE_ADDR']
        except KeyError:
            remote = "testClient"
        log = {
                'msg':"",
                'user':request.user,
                'client': remote,
                'view':view_func.__name__,
                'url':request.get_full_path(),
                'method':request.META['REQUEST_METHOD'],
            }
        try:
            log['sessid'] = request.COOKIES['sessionid']
        except KeyError:
            log['sessid'] = "None"
        try:
            if request.META["HTTP_USER_AGENT"].find ('PPC') != -1:
                log['version'] = 'PPC'
            else:
                log['version'] = 'ESCRITORIO'
        except KeyError:
            if settings.ALWAYS_USE_PPC_VERSION:
                log['version'] = 'PPC'
            else:
                log['version'] = 'ESCRITORIO'
        if request.user.is_anonymous() and (view_func.__name__ != "akademicLogin"):
                log['msg'] += "Warning, intento de pirula"
        if request.POST and (log['view'] != 'akademicLogin'):
                log['msg'] += ' %s' % request.POST
        self.logger.info("[%(user)s] - %(client)s - %(sessid)s - %(view)s <%(version)s> - %(url)s - %(method)s -- %(msg)s" % log)
        return None

    def process_exception(self, request, exception):
        import traceback
        import sys
        import datetime

        exc_info = sys.exc_info()
        mail = "Akademic ha petado hoy a las %s\n" % datetime.datetime.now ()
        mail += "El pete es este que aparece aquí debajo.\n"
        mail += "################################################################\n"
        mail = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        mail += "################################################################\n"
        mail += "La petición http es esta: \n"
        mail += "%s" % request
        para = settings.PARA
        de = settings.DE
        if settings.SEND_MAIL_ON_EXCEPTION:
            send_mail ("ERROR!!!! Excepción en akademic", mail, de, para, fail_silently=False)
        self.logger.info("[PETE!!!!] - Pete de akademic, deberíamos mirar el correo a ver si ha llegado correctamente.")

