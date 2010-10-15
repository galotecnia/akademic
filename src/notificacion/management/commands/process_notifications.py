#!/usr/bin/python
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

import sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

import SOAPpy
import socket
import logging
import re
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from notificacion.models import Notificacion
from notificacion.constants import NOTIFICACION_PENDIENTE, NOTIFICACION_ENVIADA
from notificacion.constants import NOTIFICACION_ERROR, NOTIFICACION_CANCELADA, CHAR_CHANGES

log = logging.getLogger('galotecnia')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--list', default=False, action='store_true', dest='list',
            help=u'Lista las notificaciones por enviar.'),
        make_option('--dryrun', default=False, action='store_true', dest='dryrun',
            help=u'Logea todo el proceso de envio de notificaciones. pero no hace nada realmente.'),
        make_option('--check-status', default=False, action='store_true', dest='check_status',
            help=u'Chequea el estado de los mensajes enviados.'),
        make_option('--max', default=1, action='store', dest='maximo_envios',
            help=u'Numero maximo de envios. 0 indica sin limite.'),
    )
    help = u'Envia las notificaciones pendientes'

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)
        self.url = settings.SINGULAR_URL
        self.username = settings.SINGULAR_USERNAME
        self.password = settings.SINGULAR_PASSWORD
        self.account = settings.SINGULAR_ACCOUNT
        self.server = SOAPpy.SOAPProxy(self.url)

    def process_text(self, text):
        for k,v in CHAR_CHANGES.items():
            text = text.replace(k,v)
        return text
                    

    def _send_message(self, mobile, text):
        if re.compile("^346[0-9]{8}$").match(str(mobile)) is None:
            if mobile is not None:
                log.error (u"Número de teléfono inválido: %s" % mobile)
            else:
                log.error (u"Numero de teléfono inválido: Inexistente")
            return None

        try:
# Para que esto funcione, en el servidor de singular, utilizando soaplib 0.7 hay que
# tocar soaplib-0.7.2dev_r27-py2.5.egg/soaplib/soap.py en la línea 89 poner esto:
#   root, xmlids = ElementTree.XMLID(xml_string.encode('utf-8'))
            text = self.process_text(text)
            return self.server.sendSMS(username=self.username, password=self.password, account=self.account,
                phoneNumber=mobile, text=text)
        except TypeError, e:
            msg = u"You don't have access with user %(username) and password" % {'username': self.username}
            log.fatal(msg)
            print msg
        except socket.error, (e, s):
            msg = u"Error# %(codeError)d creating socket: '%(text)s'" % {'codeError': e, 'text': s}
            log.fatal(msg)
            print msg
        return None

    def _get_status(self, id):
        try:
            return self.server.getStatus(username=self.username, password=self.password, id=id)
        except TypeError, e:
            msg = u"You don't have access with user %(username) and password" % {'username': self.username}
            log.fatal(msg)
            print msg
        except socket.error, (e, s):
            msg = u"Error# %(codeError)d creating socket: '%(text)s'" % {'codeError': e, 'text': s}
            log.fatal(msg)
            print msg
        return None

    def _check_saldo(self, numero_notificaciones_pendientes):
        try:
            if self.verbosity == 2:
                print u"Cuentas disponibles:"
                for account in self.server.getAccounts(username=self.username, password=self.password):
                    print u"Cuenta: %s" % account
                    print u"\tCrédito disponible: %s" % self.server.getCredit(
                                username=self.username, password=self.password,
                                account=account)

            if self.maximo_envios:
                num_envios = min(self.maximo_envios, numero_notificaciones_pendientes)
            else:
                num_envios = numero_notificaciones_pendientes
            if not num_envios:
                log.info(u"No hay notificaciones pendientes que realizar.")
                return -1, -1
            saldo = self.server.getCredit(username=self.username, password=self.password, account=self.account)
            if saldo < 0:
                raise TypeError()
            if saldo < num_envios:
                log.error(u"No tiene saldo para realizar el envío. Saldo %s, número de envíos: %s", saldo, num_envios)
                return -1, saldo

            log.info(u"Saldo disponible: %s", saldo)
            log.info(u"Envíos a realizar: %s", num_envios)
            return num_envios, saldo
        except TypeError, e:
            msg = u"You don't have access with user %(username)s and password" % {'username': self.username}
            print msg
            log.fatal(msg)
        except socket.error, (e, s):
            msg = u"Error# %(codeError)s creating socket: '%(text)s'" % {'codeError': e, 'text': s}
            log.fatal(msg)
            print msg
        except Exception, e:
            msg = u"No tiene crédito disponible. %s" % e
            log.fatal(msg)
            print msg
        return -1, -1

    def _envia_notificaciones_pendientes(self, notificaciones_pendientes):
        sent = 0
        for notificacion in notificaciones_pendientes:
            if self.maximo_envios > 0 and sent >= self.maximo_envios:
                msg = u"Alcanzado número máximo de mensajes enviados."
                log.info(msg)
                print msg
                break
            sent += 1
            if self.listar:
                print u"%s" % notificacion
                continue
            if self.verbosity:
                print u"Enviando notificación:\n\t%s\n\t%s" % (
                    notificacion.padre.persona.tlf_movil(), notificacion.texto.texto)
            log.debug(u'Enviando notificación %s' % notificacion.id)
            if not self.dryrun:
                plataforma_id = self._send_message('34' + notificacion.padre.persona.tlf_movil(), notificacion.texto.texto)
                if plataforma_id is not None:
                    notificacion.set_enviada(plataforma_id)
                else:
                    log.warn(u'No se ha podido enviar la notificación, error inesperado.')
                    sent -= 1
        return sent

    def _check_status(self):
        for notificacion in Notificacion.get_sin_estado():
#            print notificacion
            estado = self._get_status(notificacion.plataformaId)
            print u"%s" % estado
#            if estado:
#                notificacion.estado = estado
#                notificacion.save()

    def _alerta_supervisores(self, sent, saldo):
        if sent > settings.NOTIFICAR_SUPERVISOR_SMS:
            log.debug(u"Notificando a los supervisores. %s mensajes enviados", sent)
            if saldo - (sent + len(settings.TELEFONOS_SUPERVISORES)) >= 0:
                for supervisor in settings.TELEFONOS_SUPERVISORES:
                    self._send_message('34' + supervisor, u"Colegio: enviados %d mensajes" % sent)
            else:
                log.warn(u"No se ha podido notificar a los supervisores porque no hay saldo.")
                log.warn(u"Saldo actual: %s", saldo)

    def handle(self, *app_labels, **options):

        self.listar = options.get('list', False)
        self.maximo_envios = int(options.get('maximo_envios', 1))
        self.dryrun = options.get('dryrun', False)
        self.verbosity = int(options.get('verbosity', 1))
        self.check_status = int(options.get('check_status', False))

        log.debug(u'Enviando notificaciones')
        if self.verbosity == 2:
            print u"Enviando notificaciones"
            
        if self.maximo_envios:
            msg = u"Como máximo enviar %d notificaciones." % self.maximo_envios
            log.info(msg)
            if self.verbosity == 2:
                print msg
        if self.dryrun:
            msg = u'Enviando notificaciones en modo dry-run'
            log.info(msg)
            if self.verbosity == 2:
                print msg

        notificaciones_pendientes = Notificacion.get_pendientes()
        num_envios, saldo =  self._check_saldo(len(notificaciones_pendientes))
        if num_envios > 0:
            sent = self._envia_notificaciones_pendientes(notificaciones_pendientes)
            self._alerta_supervisores(sent, saldo)
            msg = u"Enviados %s mensajes." % sent
            log.info(msg)
            print msg
        if self.check_status:
            print u"Not implemented yet."
            #time.sleep(10)
            #self._check_status()
