from django.contrib import admin
from django.db import models
from django.http import HttpResponse

from xml.etree import ElementTree

from biblentry.models import BibliographicCategory, BibliographicEntry, Language

from tinymce.widgets import TinyMCE


class StyledEntryTextarea (TinyMCE):

    def __init__ (self, *args, **kwargs):
        mce_attrs = kwargs.setdefault('mce_attrs', {})
        mce_attrs['plugins'] = 'paste,biblentry,save'
        mce_attrs['theme_advanced_buttons1'] = 'italic,BiblEntryauthor,BiblEntryeditor,BiblEntrytitlemonograph,BiblEntrytitlearticle,BiblEntrydate,BiblEntryunmark,separator,undo,redo,separator,code'
        mce_attrs['theme_advanced_buttons2'] = ''
        super(StyledEntryTextarea, self).__init__(*args, **kwargs)


class BibliographicCategoryAdmin (admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ['name']


class BibliographicEntryAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Reference', {'fields': ('styled_entry',)}),
        ('Others', {'fields': ('language', 'categories')}),
        )
    list_display = ('id', 'author', 'publication_date', 'title_monograph',
                    'title_article')
    list_display_links = list_display
    list_filter = ['language']
    ordering = ['styled_entry']
    actions = ['export_as_TEI']
    formfield_overrides = {
        models.TextField: {'widget': StyledEntryTextarea }
        }

    def export_as_TEI (self, request, queryset):
        entries = ['<listBibl>']
        entries.extend(queryset.values_list('tei_entry', flat=True))
        entries.append('</listBibl>')
        root = ElementTree.fromstringlist(entries)
        tei = ElementTree.tostring(root, encoding='utf-8')
        response = HttpResponse(tei, mimetype='text/xml')
        return response


class LanguageAdmin (admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ['name']


admin.site.register(BibliographicCategory, BibliographicCategoryAdmin)
admin.site.register(BibliographicEntry, BibliographicEntryAdmin)
admin.site.register(Language, LanguageAdmin)
