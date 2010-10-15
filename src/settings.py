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
# Django settings for akademic project.

import os.path
PROJECT_ROOT = os.path.dirname(__file__)
SITE_LOCATION = ''

import logging
DEBUG = False
# Mantenimiento, cambiar a True si se desea mostrar el mensaje de mantenimiento
MAINTENANCE = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = PROJECT_ROOT + '/akademic3.db'

# Configuracion de mysql
#
# DATABASE_ENGINE = 'mysql'
# DATABASE_NAME = 'databasename'
# DATABASE_USER = 'username'
# DATABASE_PASSWORD = 'password'
# DATABASE_HOSTNAME = 'localhost'
# DATABASE_OPTIONS = {'init_command': 'SET storage_engine=INNODB'}

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Atlantic/Canary'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'es-es'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = PROJECT_ROOT+'/media/'

# PATH al directorio que contiene las plantillas de los boletines.
OOTEMPLATES = MEDIA_ROOT + '/plantillas-odt'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = SITE_LOCATION + '/media'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/django-admin-media/'


# Make this unique, and don't share it with anybody.
SECRET_KEY = '*q_sgk*x1p=@92-c2mm)7+-fsk0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'akademicLog.AkademicLog',
    'docencia.customMiddleWare.customMiddleWare',
)

ROOT_URLCONF = 'src.urls'


TEMPLATE_DIRS = (
    PROJECT_ROOT + "/templates",
    PROJECT_ROOT + "/docencia/templates",
    PROJECT_ROOT + "/docencia/informes/templates/",
    PROJECT_ROOT + "/incidencias/templates",
    PROJECT_ROOT + "/recursos/templates",
    PROJECT_ROOT + "/pas/templates",
    PROJECT_ROOT + "/padres/templates",
    PROJECT_ROOT + "/conector/templates",
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_extensions',
    'docencia',
    'docencia.faltas',
    'docencia.horarios',
    'docencia.notas',
    'docencia.tutoria',
    'docencia.informes',
    'docencia.verificacion',
    'notificacion',
    'pas',
    'padres',
    'incidencias',
    'recursos',
    'pincel',
    'addressbook',
    'conector',
    'authority',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'docencia.akademicContextProcessor.menuContextProcessor',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

# Fixtures a importar con syncdb (solo para depuracion)
FIXTURE_DIRS = (
   #'./fixtures/',
)

# Fechas relevantes. Ejemplos
# INICIO_CURSO  = '15-09-2008'
# EVALUACIONES  = ['10-12-2008', '18-03-2009', '15-06-2009', '03-09-2009']
# PUBLICACIONES = ['20-12-2008', '30-03-2009', '28-06-2009', '18-09-2009'] 
INICIO_CURSO  = '15-09-2010'
EVALUACIONES  = ['', '', '', '']
PUBLICACIONES = ['', '', '', '']

# Permisos especiales
AUTH_PROFILE_MODULE = 'addressbook.PersonaPerfil'
VERIFICADOR=25

# Navegacion
LOGIN_URL = SITE_LOCATION + '/accounts/login'
ALWAYS_USE_PPC_VERSION=False

# Backend
DATA_BACKEND = 'pincel'
EXCHANGE_DATA_DIR = PROJECT_ROOT + '/private_data'
EXCHANGE_BUFFER_DIR = PROJECT_ROOT + '/buffer'

# Ordenar por numero de pincel o apellidos/nombre
ORDENAR_POR_NUMERO_LISTA = True

# Logging config
LOG_FILENAME = '/var/log/akademic.log'
LOG_FORMAT = "%(asctime)-15s [%(levelname)s] %(filename)s:%(lineno)s %(message)s"

# Configuracion escolar
CICLOS_JORNADA_CONTINUA=(
        {'nivel':'PRI', 'ciclo':'1'}, 
        {'nivel':'PRI', 'ciclo':'2'},
        {'nivel':'INF', 'ciclo':'2'}
    )
CURSO_ESCOLAR_ACTUAL=2010
MAXIMO_NUMERO_CITAS_PARA_TUTORIA=10

# Correos de las notificaciones
DE = "configureme@akademic.galotecnia.com"
PARA = ["info@galotecnia.com", ]
ASUNTO = "[Akademic configureme] %s"
SEND_MAIL_ON_EXCEPTION=False

# Correo de la importacion (tupla de strings)
IMPORT_REPORT_NOTIFICATION=None

# Configuracion para los webservices para SMS
SINGULAR_URL='http://singularms.galotecnia.com/ws/'
SINGULAR_USERNAME='username'
SINGULAR_PASSWORD='password'
SINGULAR_ACCOUNT='akademic'

# Notificar a los supervisores de sms si se sobrepasan los 50 mensajes enviados de una vez.$
NOTIFICAR_SUPERVISOR_SMS=10000000000
TELEFONOS_SUPERVISORES=() # tupla de strings sin "+34"
#TELEFONOS_SUPERVISORES = ("666778899", "666889977")
MONITORING_TOOL_IP='127.0.0.1' # ip del nagios

# Esta dirección se utiliza cuando se crean los nuevos usuarios. La dirección de correo electrónico
# por defecto es username@settings.DEFAULT_EMAIL_DOMAIN
DEFAULT_EMAIL_DOMAIN='akademic.galotecnia.com'

# Nombre dela institución que hospeda la aplicación.
INSTITUTION_NAME=u"Colegio Galotecnia Redes Sistemas y Servicios S.L.L."

# Logo de la institución
LOGO="/imgs/logob_100.png"

# Configuracion local
try:
    from settings_local import *
except ImportError:
    from settings_local import *

# Configuracion del logger una vez cargado settings_local.py
log = logging.getLogger('galotecnia')
if not len(log.handlers): # Esto se importa dos veces (no se por que) y se enchufan dos handlers si no se hace esto.
    fh = logging.FileHandler(LOG_FILENAME)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(fh)
log.setLevel(logging.DEBUG)
