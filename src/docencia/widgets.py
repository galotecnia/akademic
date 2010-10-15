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
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words

class ForeignKeySearchInput(forms.HiddenInput):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a ``select`` box.
    """
    class Media:
        css = {
            'all': ('media/css/jquery.autocomplete.css', 'media/css/thickbox.css',)
        }
        js = (
            'media/js/lib/jquery.js',
            'media/js/lib/jquery.bgiframe.min.js',
            'media/js/lib/jquery.ajaxQueue.js',
            'media/js/jquery.autocomplete.js'
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    # Init con campos extra: module, app, url_search y label, agregados para ser utilizados
    # por modelos que no sean foreignkey.
    def __init__(self, rel, search_fields, module = None, app = None, url_search = '../search', label = '', attrs=None):
        self.rel = rel
        self.search_fields = search_fields
        self.module_name = module  # In example, alumno
        self.app_label = app # in example, docencia
        self.url_search = url_search 
        self.label = label # Field label
        super(ForeignKeySearchInput, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        rendered = super(ForeignKeySearchInput, self).render(name, value, attrs)
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        return rendered + mark_safe(u'''
            <style type="text/css" media="screen">
                #lookup_%(name)s {
                    padding-right:16px;
                    background: url(
                        %(admin_media_prefix)simg/admin/selector-search.gif
                    ) no-repeat right;
                }
                #del_%(name)s {
                    display: none;
                }
            </style>
<label><b>%(field_label)s</b></label><input type="text" id="lookup_%(name)s" value="%(label)s"/>
<a href="#" id="del_%(name)s">
<img src="%(admin_media_prefix)simg/admin/icon_deletelink.gif" />
</a>
<script type="text/javascript">
            if ($('#lookup_%(name)s').val()) {
                $('#del_%(name)s').show()
            }
            $('#lookup_%(name)s').autocomplete('%(url_search)s', {
                extraParams: {
                    search_fields: '%(search_fields)s',
                    app_label: '%(app_label)s',
                    model_name: '%(model_name)s',
                },
            }).result(function(event, data, formatted) {
                if (data) {
                    $('#id_%(name)s').val(data[1]);
                    $('#del_%(name)s').show();
                }
            });
            $('#del_%(name)s').click(function(ele, event) {
                $('#id_%(name)s').val('');
                $('#del_%(name)s').hide();
                $('#lookup_%(name)s').val('');
            });
            </script>
        ''') % {
            'search_fields': ','.join(self.search_fields),
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'model_name': self.rel.to._meta.module_name if not self.module_name else self.module_name,
            'app_label': self.rel.to._meta.app_label if not self.app_label else self.app_label,
            'label': label,
            'name': name,
            'url_search' : self.url_search,
            'field_label': self.label,
        }

