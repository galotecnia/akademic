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

# hack para utf-8 con cron o con |
import sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
import os

from docencia.auxFunctions import genera_boletines


bin_path = os.path.dirname(os.path.abspath(sys.argv[0]))
bin_path += '/boletines'

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run', default=False, action='store_true', dest='dry_run',
            help=u'Logea la ejecucion, pero no realiza accion alguna.'),
        make_option('--odt', default=False, action='store_true', dest='odt',
            help=u'Salida en odt. (Por defecto, en pdf).'),
        make_option('--pdc', default=False, action='store_true', dest='pdc',
            help=u'Incluir grupos de PDC. (Por defecto, no se incluyen).'),
        make_option('--directory', default=bin_path, dest='directory',
            help=u'Directorio donde se guardaran los boletines generados.'),
        make_option('--niveles', default=[], dest='niveles',
            help=u'Niveles para los cuales se generaran los boletines. (Por defecto, todos los niveles)'),
        make_option('--cursos', default=[], dest='cursos',
            help=u'Cursos para los cuales se generaran los boletines. (Por defecto, todos los cursos)'),
    )
    help = u'Proceso de generacion de boletines automatizado.'

    def handle(self, *app_labels, **options):
        dry_run = options.get('dry_run', False)
        odt = options.get('odt', False)
        directory = options.get('directory', bin_path)
        verbosity = options.get('verbosity', 0) or dry_run
        pdc = options.get('pdc', False)
        niveles = options.get('niveles', [])
        cursos = options.get('cursos', [])
        
        filetype = 'odt' if odt else 'pdf'
        print u"Se va a realizar la generacion de boletines en %s en el directorio %s" % (filetype, directory)
        print u"Los niveles son los siguientes: ", niveles if niveles else 'INF, PRI y ESO'
        print u"Los cursos son los siguientes: ", cursos if cursos else 'todos'
        print u"\nEstá seguro?"
        resp = raw_input('[YES|NO]: ')
        if resp.lower() in ['no', 'n']:
            print u"Hasta la proxima."
            sys.exit(0)
        print "Generando %s de los boletines..." % filetype

        genera_boletines(directory, odt, dry_run, pdc, niveles, cursos)
        
        print u"Finalizada la generacion de boletines."
