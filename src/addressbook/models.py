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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

import operator

TRATAMIENTO = (
    (0, _(u'Sr.')),
    (1, _(u'Sra.')),
    (2, _(u'Dr.')),
    (3, _(u'Dra.')),
    (4, _(u'Srta.')),
)

OPCIONES_SEXO = (
    (True, _(u'Masculino')),
    (False, _(u'Femenino')),
)

DNI      = 10
PASSPORT = 20
NIE      = 30

OPCIONES_DOCUMENTO = (
    (DNI, _(u'D.N.I.')),
    (PASSPORT, _(u'Pasaporte')),
    (NIE, _(u'NIE')),
)

T_PERSONAL = 100
T_TRABAJO = 101
EM_PERSONAL = 102
EM_TRABAJO = 103
F_PERSONAL = 104
F_TRABAJO = 105
M_PERSONAL = 106
M_TRABAJO = 107

OPCIONES_CONTACTO = (
    (T_PERSONAL , _(u'Teléfono personal')),
    (T_TRABAJO, _(u'Teléfono trabajo')),
    (EM_PERSONAL, _(u'Correo electrónico personal')),
    (EM_TRABAJO, _(u'Correo electrónico trabajo')),
    (F_PERSONAL, _(u'FAX personal')),
    (F_TRABAJO, _(u'FAX trabajo')),
    (M_PERSONAL, _(u'Móvil personal')),
    (M_TRABAJO, _(u'Móvil trabajo')),
    (108, _(u'GTalk')),
    (109, _(u'Msn')),
    (110, _(u'ICQ')),
    (111, _(u'Yahoo MSN')),
    (112, _(u'Jabber')),
)

D_PERSONAL = 200
D_PROFESIONAL = 201
D_SERVICIOS = 202
OPCIONES_DIRECCION=(
    (D_PERSONAL, _(u'Domicilio Personal')),
    (D_PROFESIONAL, _(u'Domicilio Profesional')),
    (D_SERVICIOS, _(u'Domicilio Prestación de Servicio')),
)

class Persona(models.Model):
    """
        Este modelo agrupa todos aquellos datos asociados a una persona,
        esto es el nombre, los apellidos, etc.
    """
    nombre = models.CharField(
            verbose_name=_(u'Nombre'),
            max_length = 50
    )
    apellidos = models.CharField(
            verbose_name=_(u'Apellidos'),
            max_length = 100
    )
    sexo = models.BooleanField(
            verbose_name = _(u'Sexo'),
            choices = OPCIONES_SEXO, default = True
    )
    tratamiento = models.IntegerField(
            verbose_name = _(u'Tratamiento'),
            choices = TRATAMIENTO, blank = True, null = True
    )
    documento_identificacion = models.CharField(
            verbose_name = _(u'Documento identificativo'),
            # NOTE: No sería lógico que si puede estar vacio, que se pueda repetir? al menos debugging
            max_length = 15, null = True, blank = True
    )
    tipo_documento_identificacion = models.IntegerField(
            verbose_name = _(u'Tipo de documento identificativo'),
            blank = True, null = True, choices = OPCIONES_DOCUMENTO, default = 10
    )
    fecha_nacimiento = models.DateField(
            verbose_name = _(u'Fecha de nacimiento'),
            blank = True, null = True
    )
    lugar_nacimiento = models.CharField(
            verbose_name = _(u'Lugar de nacimiento'),
            max_length = 200, blank = True, null = True
    )
    nacionalidad = models.CharField(
            verbose_name = _(u'Nacionalidad'),
            max_length = 20, blank = True, null = True
    )
    observaciones = models.TextField(
            verbose_name = _(u'Observaciones'),
            blank = True, null = True
    )

    def __unicode__(self):
        if not self.tratamiento == None:
            return u"%s %s %s" % (dict(TRATAMIENTO)[self.tratamiento], self.nombre, self.apellidos)
        return u"%s %s" % (self.nombre, self.apellidos)

    @staticmethod
    def contactos(persona):
        """Este método devuele una tupla con los datos a ser utilizados en los formularios"""
        if persona.direccion_set.all():
            direccion = persona.direccion_set.all()[0]
        else:
            direccion = ""
        telefono = self.tlf_movil()
        if not telefono:
            telefono = self.tlf_casa()
        if not telefono:
            telefono = self.tlf_trabajo()
        correo = self.email()
        return (direccion, telefono, correo)

    def tlf_casa(self):
        try:
            return self.contacto_set.filter(tipo = T_PERSONAL)[0].dato
        except IndexError:
            return ""

    def tlf_movil(self):
        try:
            return self.contacto_set.filter(tipo=M_PERSONAL)[0].dato
        except IndexError:
            return ""

    def tlf_trabajo(self):
        try:
            return self.contacto_set.filter(tipo = M_TRABAJO)[0].dato
        except IndexError:
            try:
                return self.contacto_set.filter(tipo = T_TRABAJO)[0].dato
            except IndexError:
                return ""

    def email(self):
        try:
            return self.contacto_set.filter(tipo = EM_PERSONAL)[0].dato
        except IndexError:
            try:
                return self.contacto_set.filter(tipo = EM_TRABAJO)[0].dato
            except IndexError:
                return ""

    def fax(self):
        try:
            return self.contacto_set.filter(tipo = F_PERSONAL)[0].dato
        except IndexError:
            try:
                return self.contacto_set.filter(tipo = F_TRABAJO)[0].dato
            except IndexError:
                return ""

    @staticmethod
    def search (query):
        contactos = Contacto.objects.filter (
                reduce (operator.or_, [ models.Q(dato__icontains = bit) for bit in query.split() ])
            )

        search_fields = [
                'nombre__icontains',
                'apellidos__icontains',
                'documento_identificacion__icontains',
                'lugar_nacimiento__icontains',
                'nacionalidad__icontains',
            ] # your search fields here

        personasEncontradas = QuerySet(Persona)
        for bit in query.split (): 
            or_queries = [models.Q(**{field_name: bit}) for field_name in search_fields]
            other_qs = QuerySet(Persona)
            other_qs.dup_select_related(personasEncontradas)
            other_qs = other_qs.filter(reduce(operator.or_, or_queries))
            personasEncontradas = personasEncontradas & other_qs

        pe = []
        for p in personasEncontradas:
            pe.append (p)
        for c in contactos:
            if c.persona not in pe:
                pe.append (c.persona)

        return pe

    def get_direccion(self):
        """
            Devuelve un diccionario con los datos relativos a la dirección de la persona.
            Si no se dispone de la información los campos contendrán una cadena vacía.
            Es especialmente útil en el caso de la generación de facturas, en las que
            deben sustituirse las cadenas de la plantilla y cuando no existe el dato
            sutituirlo por una cadena vacía.
        """

        direccion = ""
        codigo_postal = ""
        poblacion = ""
        provincia = ""
        pais = ""
        direcciones = self.direccion_set.all()
        if direcciones:                                                                       
            d = direcciones[0]
            if d.domicilio: 
                direccion = d.domicilio
            if d.codPostal:
                codigo_postal = d.codPostal
            if d.poblacion:
                poblacion = d.poblacion
            if d.provincia:
                provincia = d.provincia
            if d.pais:
                pais = d.pais
        out = {}
        out['direccion'] = direccion
        out['codigo_postal'] = codigo_postal
        out['poblacion'] = poblacion
        out['provincia'] = provincia
        out['pais'] = pais
        return out


class PersonaPerfil(Persona):
    """
        Clase que servirá de perfil para la aplicación Auth de Django
    """
    # This is the only required field
    user = models.ForeignKey(User, unique=True, null=True)

    class Meta:
        permissions = (
                ("import_data", "Can import data."),
                ("is_director", "Es director."),
                ("is_verificador", "Es verificador."),
                ("is_orientador", "Es orientador."),
            )

    
class Direccion(models.Model):
    """
        Esta clase se utiliza para manejar las direcciones postales
    """
    tipo = models.IntegerField(
            verbose_name = _(u'Tipo de dirección'),
            choices = OPCIONES_DIRECCION, default = 200
    )
    domicilio = models.CharField(
            verbose_name = _(u'Dirección'),
            max_length = 100, blank = True, null = True,
    )
    codPostal = models.CharField(
            verbose_name = _(u'Código postal'),
            max_length = 5, blank = True, null = True
    )
    poblacion = models.CharField(
            verbose_name = _(u'Población'), 
            max_length = 50, blank = True, null = True
    )
    provincia = models.CharField(
            verbose_name = _(u'Provincia'),
            max_length = 50, blank = True, null = True
    )
    pais = models.CharField(
            verbose_name = _(u'País'),
            max_length = 50, blank = True, null = True
    )
    nota = models.TextField(
            verbose_name = _(u'Nota'), blank = True, null = True
    )
    persona = models.ForeignKey(
            Persona,
            verbose_name = _(u'Persona')
    )

    def __unicode__(self):
        cad = u""
        if self.domicilio:
            cad += self.domicilio + " "
        if self.poblacion:
            cad += self.poblacion + " "
        if self.codPostal:
            cad = cad + "(" + self.codPostal + ")"
        return cad.rstrip()

    class Meta:
        verbose_name = _(u'Dirección')
        verbose_name_plural = _(u'Direcciones')

class Contacto(models.Model):
    """Esta clase se utiliza para almacenar los datos de contacto
    """    
    tipo = models.IntegerField(
            verbose_name = _(u'Tipo'),
            choices=OPCIONES_CONTACTO
    )
    dato = models.CharField(
            verbose_name = _(u'Dato'),
            max_length = 80
    )
    persona = models.ForeignKey(
            Persona,
            verbose_name = _(u'Persona')
    )

    def __unicode__(self):
        return u"%s: %s" %(dict(OPCIONES_CONTACTO)[self.tipo], self.dato)

    class Meta:
        unique_together = [['dato', 'tipo', 'persona']]   # Es tontería almacenar el mismo dato para una persona dos veces. El mismo dato para dos personas es raro pero creo que posible
