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
sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

from optparse import make_option

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.conf import settings

from conector.import_queue import ImportQueue
from padres.models import Padre
from notificacion.models import Notificacion

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--force', default=False, action='store_true', dest='force',
            help=u'Envia el mensaje a todos los padres, tengan su telefono validado.'),
            make_option('--dry-run', default=False, action='store_true', dest='dry_run',
            help=u'No realiza accion alguna. Solo para testeo de funcionamiento.'),
        )
    help = u'Envia un mensaje sms a todos los padres que tengan hijos matriculados en este curso escolar.'

    def handle(self, *app_labels, **options):
#        msg = u"Por favor, notificar al tutor mediante la agenda la recepción de este mensaje"
#        msg = u"Bienvenidos al curso 2009 2010. Roguemos confirmen la recepcion del SMS"
#        msg = u"Rogamos confirme la recepcion de este SMS en la carta enviada desde el Centro"
        msg = u"Bienvenidos al curso 2010-2011. Rogamos confirmen la recepción de este SMS en la carta que hoy le entregará su hijo/a"
        force = options.get('force', False)
        debug = options.get('debug', False)
        dry_run = options.get('dry_run', False)
        verbosity = int(options.get('verbosity', 1))
        if verbosity == 2:
            print u"Modo verboso"
        if dry_run:
            print u"Modo dry_run"
        # padres_notificados = []
        for p in Padre.objects.filter(
                (
                Q(padre_hijos__grupoaulaalumno__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL) |\
                Q(madre_hijos__grupoaulaalumno__grupo__curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL) \
                ) & Q(verificado__isnull=True) & Q(difunto=False) 
            ).exclude(is_blanco = True).distinct()[1:]: # Evita padres repetidos
            # if p.id in padres_notificados:
            #     if verbosity == 2:
            #         print u"Obviando padre %s, debe tener más de un hijo." % p
            #     continue
            filter = {"grupoaulaalumno__grupo__curso__ciclo__nivel__cursoEscolar": settings.CURSO_ESCOLAR_ACTUAL}
            if not p.get_hijos().filter(**filter).count():
                continue
            if p.persona.tlf_movil() is '':
                continue
            # padres_notificados.append(p.id)
            if not dry_run:
                n = Notificacion.envia_notificacion(p, p.get_hijos()[0], msg, force=True)
                if verbosity == 2:
                    print u"Notificación enviada: %s, %s" % (p, msg)
                if verbosity and not n:
                    print u"No se ha podido enviar la notificación a %s porque no tenía teléfono móvil." % p
            else:
                if verbosity == 2:
                    print u"DRY_RUN: Notificacion NO enviada: %s, %s" % (p, msg)
                

