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

import md5
import logging
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.conf import settings
from django.utils.translation import ugettext as _
from forms import UploadFileForm, EndUploadForm
from import_queue import ImportQueue
from file_manager import FileManager

log = logging.getLogger("galotecnia")

def upload_data_file(request):
    """
        Recibe un fichero via post.
        Sólo se debe tragar los ficheros recibidos si no hay importaciones por realizar.
        Para averiguar si hay importaciones por realizar hay que revisar todos los directorios de datos
        y verificar que todos tengan un "log.txt" en su interior. Si hay algún directorio que no tiene
        el fichero no se admitirán nuevas importaciones.
        Hay que ferificar la integridad de los ficheros utilizando el valor del md5 que se envía en el post.
        1.  Nombre de usuario y contraseña inválidos:
              1.  return 403 Forbidden
        2.  Si hay directorios pendientes de procesar en la cola de importaciones
              1.  return status 400 Bad Request: The request contains bad syntax or cannot be fulfilled. FIN
        3.  Calcular md5 al fichero recibido
        4.  Si los md5 no son iguales
              1.  return status 409 Conflict: Indicates that the request could not be processed because
                 of conflict in the request. FIN
        5.  Crear si no existe un directorio utilizando la fecha enviada con el patrón '%y-%m-%d_%H:%M'
        6.  Mover el fichero al directorio
        7.  return 200

    """
    log.debug("Receiving an upload_data_file order.")
    if not request.POST:
        raise Http404

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        log.error(str(form.errors))
        return HttpResponseForbidden()

    import_queue = ImportQueue ()
    if import_queue.todo:
        error_msg = _(u'ERROR: Quedan importaciones pendientes')
        log.error (error_msg)
        return HttpResponse(error_msg, status=400)

    file_manager = FileManager ()
    try:
        file_manager.save_post_file (form.cleaned_data)
    except ValueError, e:
        return HttpResponse(e.message, status=409)
    return HttpResponse ('ok')
    
def end_upload_data(request):
    log.debug("Receiving an end_upload_data order")
    if not request.POST:
        raise Http404

    form = EndUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        error_msg = _(u'ERROR: Final de importacion no valida')
        log.error (error_msg)
        return HttpResponseForbidden()

    file_manager = FileManager ()
    try:
        file_manager.upload_end (form.cleaned_data['date'])
    except RuntimeError, e:
        error_msg = _(u'ERROR: Finalizacion upload con error %s') %e
        log.error (error_msg)
        return HttpResponse(e.message, status=400)
    return HttpResponse ('ok')

def check_upload_data(request):
    log.debug("Receiving a consulting of current imports")

    import_queue = ImportQueue ()
    if import_queue.todo:
        error_msg = u'ERROR: Quedan importaciones pendientes'
        log.error (error_msg)
        return HttpResponse(error_msg, status=400)
    log.debug(u"TODO OK, se procede con la subida de datos")
    return HttpResponse('ok')
