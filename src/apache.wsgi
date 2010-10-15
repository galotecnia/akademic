#!/usr/bin/env python

import os
import sys
sys.stdout = sys.stderr

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(p)
sys.path.append(p+"/..")

os.environ['PYTHON_EGG_CACHE'] = os.path.join(p, 'egg-cache')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

