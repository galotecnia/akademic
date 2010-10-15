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
from django.test import TestCase
from django.contrib.auth.models import User
from docencia.permissions import GrupoAulaPermission, AlumnoPermission, RecursoPermission
from docencia.horarios.models import Horario
from docencia.models import Asignatura, Alumno
from recursos.models import Recurso

class GrupoAulaPermissionTests(TestCase):

    fixtures = ['mydata.json',]

    def test_grupoaula_permission_with_admin(self):
        u = User.objects.filter(username = 'admin')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(False, p.has_class_priv(h.grupo))

    def test_grupoaula_permission_with_prof(self):
        u = User.objects.filter(username = 'Profesor')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(True, p.has_class_priv(h.grupo))
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_class_priv(h.grupo, m))
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))

 
    def test_grupoaula_permission_with_no_prof(self):
        u = User.objects.filter(username = 'NoProfesor')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(False, p.has_class_priv(h.grupo))
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))        

    def test_grupoaula_permission_with_tutor(self):
        u = User.objects.filter(username = 'Tutor')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(True, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_class_priv(h.grupo, m))

    def test_grupoaula_permission_with_no_tutor(self):
        u = User.objects.filter(username = 'NoTutor')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(False, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))       

    def test_grupoaula_permission_with_coordinador(self):
        u = User.objects.filter(username = 'Coordinador')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(True, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_class_priv(h.grupo, m))
 
    def test_grupoaula_permission_with_no_coordinador(self):
        u = User.objects.filter(username = 'NoCoordinador')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(False, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))      
 
    def test_grupoaula_permission_with_jefe_estudios(self):
        u = User.objects.filter(username = 'JefeEstudios')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(True, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_class_priv(h.grupo, m))
 
    def test_grupoaula_permission_with_no_jefe_estudios(self):
        u = User.objects.filter(username = 'NoJefeEstudios')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        self.assertEqual(False, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))      

    def test_grupoaula_permission_with_director(self):
        u = User.objects.filter(username = 'Director')[0]
        p = GrupoAulaPermission(u)
        h = Horario.objects.all()[0]
        #FIXME: provisionalmente False puesto que no hay permiso de director
        #       En cuanto se agregue este permiso, cambiarlo en ambas
        self.assertEqual(False, p.has_class_priv(h.grupo)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_class_priv(h.grupo, m))       


class AlumnoPermissionTests(TestCase):

    fixtures = ['mydata.json',]

    def test_alumno_permission_with_admin(self):
        u = User.objects.filter(username = 'admin')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu))

    def test_alumno_permission_with_prof(self):
        u = User.objects.filter(username = 'Profesor')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(True, p.has_alu_priv(alu))
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_alu_priv(alu, m))
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))

 
    def test_alumno_permission_with_no_prof(self):
        u = User.objects.filter(username = 'NoProfesor')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu))
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))        

    def test_alumno_permission_with_tutor(self):
        u = User.objects.filter(username = 'Tutor')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(True, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_alu_priv(alu, m))

    def test_alumno_permission_with_no_tutor(self):
        u = User.objects.filter(username = 'NoTutor')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))       

    def test_alumno_permission_with_coordinador(self):
        u = User.objects.filter(username = 'Coordinador')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(True, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_alu_priv(alu, m))
 
    def test_alumno_permission_with_no_coordinador(self):
        u = User.objects.filter(username = 'NoCoordinador')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))      
 
    def test_alumno_permission_with_jefe_estudios(self):
        u = User.objects.filter(username = 'JefeEstudios')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(True, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = 'Matematicas')[0]
        self.assertEqual(True, p.has_alu_priv(alu, m))
 
    def test_alumno_permission_with_no_jefe_estudios(self):
        u = User.objects.filter(username = 'NoJefeEstudios')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))      

    def test_alumno_permission_with_director(self):
        u = User.objects.filter(username = 'Director')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        #FIXME: provisionalmente False puesto que no hay permiso de director
        #       En cuanto se agregue este permiso, cambiarlo en ambas
        self.assertEqual(False, p.has_alu_priv(alu)) 
        m = Asignatura.objects.filter(nombreCorto = u'Quimica')[0]
        self.assertEqual(False, p.has_alu_priv(alu, m))      
      
    def test_alumno_permission_with_padre_potestad(self):
        u = User.objects.filter(username = 'Padre')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(True, p.has_alu_priv(alu)) 

    def test_alumno_permission_with_no_padre_potestad(self):
        u = User.objects.filter(username = 'Madre')[0]
        p = AlumnoPermission(u)
        alu = Alumno.objects.all()[0]
        self.assertEqual(False, p.has_alu_priv(alu)) 

class RecursoPermissionTests(TestCase):

    fixtures = ['mydata.json',]

    def test_recurso_book_available_with_prof(self):
        u = User.objects.get(username = 'Profesor')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Proyector')
        self.assertEqual(True, p.reservar_recurso(r))

    def test_recurso_book_available_with_no_prof(self):
        u = User.objects.get(username = 'Padre')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Proyector')
        self.assertEqual(False, p.reservar_recurso(r))

    def test_recurso_book_unavailable_with_prof(self):
        u = User.objects.get(username = 'Profesor')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Canon')
        self.assertEqual(False, p.reservar_recurso(r))

    def test_recurso_book_unavailable_with_no_prof(self):
        u = User.objects.get(username = 'Padre')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Canon')
        self.assertEqual(False, p.reservar_recurso(r))

    def test_recurso_asign_available_with_pas(self):
        u = User.objects.get(username = 'PAS')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Proyector')
        self.assertEqual(True, p.asignar_recurso(r))

    def test_recurso_asign_available_with_no_pas(self):
        u = User.objects.get(username = 'Padre')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Proyector')
        self.assertEqual(False, p.asignar_recurso(r))

    def test_recurso_asign_unavailable_with_pas(self):
        u = User.objects.get(username = 'PAS')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Canon')
        self.assertEqual(False, p.asignar_recurso(r))

    def test_recurso_asign_unavailable_with_no_pas(self):
        u = User.objects.get(username = 'Padre')
        p = RecursoPermission(u)
        r = Recurso.objects.get(descripcion = 'Canon')
        self.assertEqual(False, p.reservar_recurso(r))
