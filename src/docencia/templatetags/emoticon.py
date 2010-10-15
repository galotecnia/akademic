# -*- encoding: utf8 -*-
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

from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

from docencia.models import Nivel
from docencia.constants import FALTA_COMPORTAMIENTO, FALTA_MATERIAL, FALTA_TAREA

register = template.Library()
INF = 'INF'

@register.filter
def comportamiento(value):
	"""Value es un GrupoAula"""
	if value.curso.ciclo.nivel.nombre == INF:
		return mark_safe('<img src="%s/imgs/sad.gif" />' % settings.MEDIA_URL)
	else:
		return "C"

@register.filter
def tarea(value):
	"""Value es un GrupoAula"""
	if value.curso.ciclo.nivel.nombre == INF:
		return mark_safe('<img src="%s/imgs/molumen_couvert.gif" />' % settings.MEDIA_URL)
	else:
		return "T"

@register.filter
def material(value):
	"""Value es un GrupoAula"""
	if value.curso.ciclo.nivel.nombre == INF:
		return mark_safe('<img src="%s/imgs/korganizer.gif" />' % settings.MEDIA_URL)
	else:
		return "M"

@register.filter
def animo(hijos):
	"""hijos es un vector de hijos"""
	hijo_infantil = False
	hijo_noinfantil = False
	for i in hijos:
		if i['hijo'].getGrupo() and i['hijo'].getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
			hijo_infantil = True
		else:
			hijo_noinfantil = True	
	if hijo_infantil and not hijo_noinfantil:
		return "Ánimo"
	elif hijo_infantil:
		return "Disciplina / Ánimo"
	else:
		return "Disciplina"

@register.filter
def comio(hijos):
	"""hijos es un vector de hijos"""
	hijo_infantil = False
	hijo_noinfantil = False
	for i in hijos:
		if i['hijo'].getGrupo() and i['hijo'].getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
			hijo_infantil = True
		else:
			hijo_noinfantil = True	
	if hijo_infantil and not hijo_noinfantil:
		return "Comedor"
	elif hijo_infantil:
		return "Tarea / Comedor"
	else:
		return "Tarea"

@register.filter
def trabajo(hijos):
	"""hijos es un vector de hijos"""
	hijo_infantil = False
	hijo_noinfantil = False
	for i in hijos:
		if i['hijo'].getGrupo() and i['hijo'].getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
			hijo_infantil = True
		else:
			hijo_noinfantil = True	
	if hijo_infantil and not hijo_noinfantil:
		return "Trabajo"
	elif hijo_infantil:
		return "Material / Trabajo"
	else:
		return "Material"

@register.filter
def header(hijo, arg="header"):
	"""hijo es un elemento del vector de hijos que hay en la plantilla"""
	if arg == "header":
		if hijo['hijo'].getGrupo() and hijo['hijo'].getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
			return mark_safe("<th></th>")
		else:
			return ""

@register.filter
def columna (hijo):
	if hijo['hijo'].getGrupo() and hijo['hijo'].getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
		return '5'
	else:
		return '4'

@register.filter
def iconoFalta(falta):
	if falta.alumno.getGrupo() and falta.alumno.getGrupo().grupo.curso.ciclo.nivel.nombre == INF:
		if falta.tipo == FALTA_COMPORTAMIENTO:
			return mark_safe('<td><img src="%s/imgs/sad.gif" /></td>' % settings.MEDIA_URL)
		elif falta.tipo == FALTA_MATERIAL:
			return mark_safe('<td><img src="%s/imgs/molumen_couvert.gif" /></td>' % settings.MEDIA_URL)
		elif falta.tipo == FALTA_TAREA:
			return mark_safe('<td><img src="%s/imgs/korganizer.gif" /></td>' % settings.MEDIA_URL)
		else:
			return mark_safe('<td></td>')
	else:
		return ""
		
@register.filter
def notaTextual(nota):
	try:
		valor = int(nota)
		if valor < 5:
			salida = "IN"
		elif valor == 5:
			salida = "SU"
		elif valor == 6:
			salida = "BI"
		elif valor == 7:
			salida = "NT"
		elif valor == 8:
			salida = "NT"
		elif valor >= 9:
			salida = "SB"
		salida += "(%s)" % nota
	except:
		salida = nota
	return salida

