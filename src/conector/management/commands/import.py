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
from django.conf import settings 
from django.core.mail import send_mail

from conector.import_queue import ImportQueue
from docencia.models import Alumno, Profesor, GrupoAula
from docencia.faltas.models import Falta, Ausencia
from docencia.constants import *
from docencia.notas.models import Evaluacion

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--force', default=False, action='store_true', dest='force',
            help=u'Fuerza a que se importe la ultima version aun cuando ya ha sido importada.'),
        make_option('--debug', default=False, action='store_true', dest='debug',
            help=u'No hace backups, acelerando el proceso de importacion en si mismo'),
        make_option('--dry-run', default=False, action='store_true', dest='dry_run',
            help=u'Logea la ejecucion, pero no realiza accion alguna.'),
        make_option('--no-tabular', default=True, action='store_false', dest='tabular',
            help=u'No realiza la ejecucion de import_tabular_data.'),
        make_option('--no-variable', default=True, action='store_false', dest='variable',
            help=u'No realiza la ejecucion de import_variable_data.'),
        make_option('--no-excel', default=True, action='store_false', dest='excel',
            help=u'No realiza la ejecucion de import_excel.'),
        make_option('--no-delete', default=True, action='store_false', dest='delete',
            help=u'No realiza la eliminacion de los datos no marcados.'),
        make_option('--notifica', default=False, action='store_true', dest='notifica',
            help=u'Notifica mediante email de los resultados de la importacion.'),
    )
    help = u'Importa los datos del backend definido en settings.py'

    def genera_mensaje(self):
        context = {}
        context['num_alumnos'] = Alumno.objects.all().count()
        context['num_profesores'] = Profesor.objects.all().count()
        context['num_faltas_asistencia'] = Falta.objects.filter(tipo = FALTA_ASISTENCIA).count()
        context['num_retrasos'] = Falta.objects.filter(tipo = RETRASO).count()
        context['num_faltas_comportamiento'] = Falta.objects.filter(tipo = FALTA_COMPORTAMIENTO).count()
        context['num_faltas_material'] = Falta.objects.filter(tipo = FALTA_MATERIAL).count()
        context['num_faltas_tarea'] = Falta.objects.filter(tipo = FALTA_TAREA).count()
        context['num_ausencias'] = Ausencia.objects.all().count()
        context['num_evaluaciones'] = Evaluacion.objects.all().count()
        context['grupo_aulas'] = GrupoAula.objects.filter(curso__ciclo__nivel__cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL
            ).exclude(seccion = "Pendientes").order_by("curso__ciclo__nivel", "curso")
        context['profesores'] = Profesor.objects.all().order_by("persona__apellidos", "persona__nombre")
        context['evaluaciones'] = Evaluacion.objects.filter(cursoEscolar = settings.CURSO_ESCOLAR_ACTUAL)

        return render_to_string("plantilla_indicadores_importacion.txt", context)

    def handle(self, *app_labels, **options):
        force = options.get('force', False)
        debug = options.get('debug', False)
        dry_run = options.get('dry_run', False)
        tabular = options.get('tabular', True)
        variable = options.get('variable', True)
        excel = options.get('excel', True)
        delete = options.get('delete', True)
        notifica = options.get('notifica', False)
        verbosity = options.get('verbosity', 1) or dry_run
        if settings.DEBUG:
            print u"No se puede empezar la importación porque DEBUG esta a True, y esto es MUY DAÑINO para el servidor"
            return 
        if dry_run:
            print u"Recuerde que esta acciendo un dry-run, ninguna accion sera realizada"
        if verbosity:
            print u"Analizando información para importar desde %s a akademic." % settings.DATA_BACKEND
        iq = ImportQueue(None, dry_run, tabular, variable, excel, delete)
        try:
            todo = iq.get_todo_list()[-1]
        except IndexError:
            if verbosity:
                print u"No hay ninguna importación pendiente."
            return
        if verbosity:
            print u"Encontrada una importación pendiente: %s" % todo
        iq.import_process(todo, verbosity, debug=debug)

        # FIXME: Revisar asunto, from y to
        if notifica and settings.IMPORT_REPORT_NOTIFICATION and len(settings.IMPORT_REPORT_NOTIFICATION):
            print(u"Enviando informe a %s" % settings.IMPORT_REPORT_NOTIFICATION)
            if not dry_run:
                send_mail('Resultado de la carga de datos en akademic %s' % todo,
                        self.genera_mensaje(),
                        'no-reply@galotecnia.com',
                        settings.IMPORT_REPORT_NOTIFICATION,
                        fail_silently=True
                    )
        else:
            print u'Nadie se ha podido enterar de esta notificación, no hay receptores de los informes configurados'

        if verbosity:
            print u"Finalizada la importación de %s" % todo

