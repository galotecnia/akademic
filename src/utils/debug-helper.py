Un template para no estar escribiendo esto mil veces:


from akademic2.akademic.models import *
from django.db.models import Q

grupo = GrupoAula.objects.get(pk = 153)
asignatura = Asignatura.objects.get(pk = 79528)

consulta = Matricula.objects.filter(Q(asignatura = asignatura) & Q(grupo = grupo))

consulta.select_related().order_by('akademic_alumno.apellidos', 'akademic_alumno.nombre')


Si no haces el select_related esto no funcionará en la vida. Es un defecto de DJANGO



Para pillar faltas:
	
asigna = Asignatura.objects.get(pk = 81990)
hora = Hora.objects.get(pk = 22)

faltas = Falta.objects.filter(
	Q(fecha = '2005-12-21')&
	Q(asignatura = asigna) &
	Q(hora = hora)
)

# Esto nos devuelve los id de alumnos en una lista de diccionarios con el formato:
# [{'alumno': 72991}, {'alumno': 72998}]
faltas.values('alumno')

