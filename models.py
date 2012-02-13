from datetime import date
import re

from django.db import models


# Pattern matching all but the first family name in a bibliographic
# entry's author string. Assumes the format "FAMILY, GIVEN" (repeated
# however often, with any separator).
EXTRA_AUTHOR_NAMES = re.compile('\s*,.*$')


class BibliographicCategory (models.Model):
    
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = 'Bibliographic categories'
        

    def __unicode__ (self):
        return self.name


class BibliographicEntry (models.Model):
    
    styled_reference = models.XMLField(blank=True)
    authors = models.CharField(blank=True, max_length=255)
    title_article = models.CharField(blank=True, max_length=1024)
    title_monograph = models.CharField(blank=True, max_length=1024)
    publication_date = models.IntegerField(blank=True, null=True)
    created = models.DateField(blank=True, null=True)
    language = models.ForeignKey('Language', blank=True, null=True)
    categories = models.ManyToManyField(BibliographicCategory, blank=True,
                                        null=True)

    class Meta:
        verbose_name_plural = 'Bibliographic entries'
        

    def get_reference_name (self):
        authors = EXTRA_AUTHOR_NAMES.sub('', self.authors)
        publication_date = ' %s' % self.publication_date
        name = '(%s%s)' % (authors, publication_date.strip())
        return name

    def save (self, *args, **kwargs):
        if self.id is None:
            self.created = date.today()
        super(BibliographicEntry, self).save(*args, **kwargs)

    def __unicode__ (self):
        name = '%s %s' % (self.title_article, self.get_reference_name())
        return name.strip()


class Language (models.Model):

    name = models.CharField(unique=True, max_length=32)
    color = models.CharField(blank=True, max_length=8)

    def __unicode__ (self):
        return self.name
