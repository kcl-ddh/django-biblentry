from django.contrib import admin
from django.db import models

from biblentry.models import BibliographicCategory, BibliographicEntry, Language

from tinymce.widgets import TinyMCE


class StyledReferenceTextarea (TinyMCE):

    def __init__ (self, *args, **kwargs):
        mce_attrs = kwargs.setdefault('mce_attrs', {})
        mce_attrs['plugins'] = 'paste,biblentry,save'
        mce_attrs['theme_advanced_buttons1'] = 'italic,BiblEntryauthor,BiblEntryeditor,BiblEntrytitlemonograph,BiblEntrytitlearticle,BiblEntrydate,BiblEntryunmark,separator,undo,redo,separator,code'
        mce_attrs['theme_advanced_buttons2'] = ''
        super(StyledReferenceTextarea, self).__init__(*args, **kwargs)


class BibliographicCategoryAdmin (admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ['name']


class BibliographicEntryAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Reference', {'fields': ('styled_reference',)}),
        ('Others', {'fields': ('language', 'categories')}),
        )
    list_display = ('id', 'authors', 'publication_date', 'title_monograph',
                    'title_article')
    list_display_links = list_display
    list_filter = ['language']
    ordering = ['styled_reference']

    formfield_overrides = {
        models.XMLField: {'widget': StyledReferenceTextarea }
        }


class LanguageAdmin (admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ['name']


admin.site.register(BibliographicCategory, BibliographicCategoryAdmin)
admin.site.register(BibliographicEntry, BibliographicEntryAdmin)
admin.site.register(Language, LanguageAdmin)
