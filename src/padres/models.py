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

from django.db import models
from django.db.models import Q
from addressbook.models import PersonaPerfil
from docencia.models import Matricula, Alumno, GrupoAulaAlumno
from django.conf import settings
from django.contrib.auth.models import User

class Padre(models.Model):
    """
        Define los datos relativos al padre de un alumno.
    """
    persona = models.OneToOneField(PersonaPerfil)
    # Características particulares de los padres    
    difunto = models.BooleanField()    
    notificarSms = models.BooleanField('Notificar incidencias por SMS')
    notificarEmail = models.BooleanField('Notificar incidencias por E-mail')
    verificado = models.DateField('Fecha de verificación', blank= True, null = True)
    is_blanco = models.BooleanField('Devolvio la hora de verificación en blanco')

    def __unicode__(self):
        return u"%s" % self.persona

    class Meta:
        ordering = ['persona']

    def generate_username(self):
        full_name = self.persona.__unicode__()
        name = unicode(full_name.strip().lower()).encode('ASCII', 'ignore')
        name = name.split(' ')
        lastname = name[-1]
        firstname = name[0]
        username = '%s%s' % (firstname[0], lastname)
        if User.objects.filter(username=username).count() > 0:
            username = '%s%s' % (firstname, lastname[0])
            if User.objects.filter(username=username).count() > 0:
                users = User.objects.filter(username__regex=r'^%s[0-9]{1,}$' % firstname).order_by('username').values('username')
                if len(users) > 0:
                    last_number_used = map(lambda x: int(x['username'].replace(firstname,'')), users)
                    last_number_used.sort()
                    last_number_used = last_number_used[-1]
                    number = last_number_used + 1
                    username = '%s%s' % (firstname, number)
                else:
                    username = '%s%s' % (firstname, 1)
        return username

    def generate_user(self):
        passwd = User.objects.make_random_password(length = 8)
        if self.persona.user:
            self.persona.user.set_password(passwd)
            self.persona.user.save()
        else:
            uname = self.generate_username()
            user = User.objects.create_user(uname, u"%s@%s" % (uname, settings.DEFAULT_EMAIL_DOMAIN), passwd)
            user.save()
            self.persona.user = user
        self.persona.save()
        return passwd

    def get_matriculas_hijos(self, curso = None, hijos = None):
        """
            Devuelve un vector con las matriculas de los hijos
        """
        if not curso:
            curso = settings.CURSO_ESCOLAR_ACTUAL
        if not hijos:
            hijos = self.get_hijos()
        return Matricula.matriculadoAlumnoCurso(hijos, curso)

    def get_hijos(self):
        """
            Devuelve un queryset con los hijos de este padre.
        """
        return Alumno.objects.filter(Q(padre = self, potestadPadre = 1) | Q(madre = self, potestadMadre = 1))

    def get_hijos_matriculados(self, curso = None):
        """
            Devuelve un queryset con los hijos de este padre matriculados en un curso
        """
        return Alumno.objects.filter(grupoaulaalumno__in = GrupoAulaAlumno.objects.filter(
            matricula__in = self.get_matriculas_hijos(curso))).distinct()

    def has_files_left(self):
        """
            Devuelve si tiene archivos pendientes de ver
        """
        for hijo in self.get_hijos():
            if hijo.fileattach_set.filter(visto = False):
                return True
        return False
        
