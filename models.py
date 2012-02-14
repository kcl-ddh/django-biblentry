from datetime import date
import re
from xml.etree import ElementTree

from django.db import models


class BibliographicCategory (models.Model):
    
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = 'Bibliographic categories'
        

    def __unicode__ (self):
        return self.name


class BibliographicEntry (models.Model):
    
    styled_entry = models.TextField(blank=True)
    language = models.ForeignKey('Language', blank=True, null=True)
    categories = models.ManyToManyField(BibliographicCategory, blank=True,
                                        null=True)
    # The remaining fields hold content automatically generated when
    # an entry is saved.
    author = models.CharField(blank=True, max_length=255)
    title_article = models.CharField(blank=True, max_length=1024)
    title_monograph = models.CharField(blank=True, max_length=1024)
    publication_date = models.IntegerField(blank=True, null=True)
    reference_name = models.CharField(blank=True, max_length=32)
    tei_entry = models.TextField(blank=True)
    created = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Bibliographic entries'
        

    def save (self, *args, **kwargs):
        """Generate content derived from the styled entry before
        saving."""
        root = ElementTree.fromstring(self.styled_entry)
        self.author = self._get_author(root)
        self.title_article = self._get_title_article(root)
        self.title_monograph = self._get_title_monograph(root)
        self.publication_date = self._get_publication_date(root)
        self.reference_name = self._get_reference_name(
            self.author, self.publication_date)
        self.tei_entry = self._render_as_tei(root)
        if self.id is None:
            self.created = date.today()
        super(BibliographicEntry, self).save(*args, **kwargs)

    @staticmethod
    def _extract_element_content (root, class_value):
        """Return a list of the text content of all elements with the
        specified class attribute value.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-author">Holt, Jean</span>, <span class="tei-title teia-level__m"><i>Fire in the</i> Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._extract_element_content(root, 'tei-author')
        ['James, P. D.', 'Holt, Jean']
        >>> BibliographicEntry._extract_element_content(root, 'tei-title teia-level__m')
        ['Fire in the Belly']
        >>> BibliographicEntry._extract_element_content(root, 'tei-date')
        ['1997']
        
        """
        # ElementTree has no XPath support, so this is a tedious
        # iterative process. However, an individual entry is small,
        # and it is not worth requiring another library such as lxml
        # to avoid this.
        contents = []
        for element in root.iter():
            if class_value == element.attrib.get('class', ''):
                # Inconveniently, tostring includes any tail content
                # of the element being serialised. This must be
                # removed.
                content = ElementTree.tostring(element, encoding='utf-8',
                                               method='text')
                if element.tail:
                    index = 0 - len(element.tail)
                    content = content[:index]
                contents.append(content)
        return contents

    @staticmethod
    def _get_author (root):
        """Return the text content of the first author (or editor, if
        no authors) listed in the XML element root.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_author(root)
        'James, P. D.'
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-editor">Holt, Jean</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_author(root)
        'James, P. D.'
        >>> root = ElementTree.fromstring('<p><span class="tei-editor">Holt, Jean</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_author(root)
        'Holt, Jean'
        
        """
        authors = BibliographicEntry._extract_element_content(
            root, 'tei-author') or \
            BibliographicEntry._extract_element_content(root, 'tei-editor')
        try:
            author = authors[0]
        except IndexError:
            author = ''
        return author        

    @staticmethod
    def _get_publication_date (root):
        """Return the publication date extracted from root.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span></p>')
        >>> BibliographicEntry._get_publication_date(root)
        ''
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_publication_date(root)
        '1997'
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span> or wait, <span class="tei-date">June 2000</span></p>')
        >>> BibliographicEntry._get_publication_date(root)
        '2000'

        """
        dates = BibliographicEntry._extract_element_content(root, 'tei-date')
        try:
            date = dates[-1]
            year = re.sub(r'\D*', '', date)
        except IndexError:
            year = ''
        return year
    
    @staticmethod
    def _get_reference_name (author, publication_date):
        """Return the reference name derived from author and
        publication date.

        >>> BibliographicEntry._get_reference_name('James, P. D.', '1997')
        '(James 1997)'
        >>> BibliographicEntry._get_reference_name('James', '')
        '(James)'

        """
        try:
            index = author.index(',')
            family_name = author[:index]
        except ValueError:
            family_name = author
        if publication_date:
            family_name += ' '
        name = '(%s%s)' % (family_name, publication_date)
        return name

    @staticmethod
    def _get_title_article (root):
        """Return all article titles in root.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_title_article(root)
        ''
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__a">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_title_article(root)
        'Fire in the Belly'
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__a">Fire in the Belly</span>, <span class="tei-date">1997</span>, <span class="tei-title teia-level__a">The accidental appendix</span></p>')
        >>> BibliographicEntry._get_title_article(root)
        'Fire in the Belly, The accidental appendix'
        
        """
        titles = BibliographicEntry._extract_element_content(
            root, 'tei-title teia-level__a')
        title = ', '.join(titles)
        return title

    @staticmethod
    def _get_title_monograph (root):
        """Return all monograph titles in root.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__a">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_title_monograph(root)
        ''
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._get_title_monograph(root)
        'Fire in the Belly'
        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span>, <span class="tei-title teia-level__m">The accidental appendix</span></p>')
        >>> BibliographicEntry._get_title_monograph(root)
        'Fire in the Belly, The accidental appendix'

        """
        titles = BibliographicEntry._extract_element_content(
            root, 'tei-title teia-level__m')
        title = ', '.join(titles)
        return title

    @staticmethod
    def _parse_class_attribute (attribute):
        """Return a dictionary of element and attribute names and
        values derived from attribute.

        >>> BibliographicEntry._parse_class_attribute('tei-author') == {'attributes': {}, 'tag': 'author'}
        True
        >>> BibliographicEntry._parse_class_attribute('tei-title teia-level__m') == {'attributes': {'level': 'm'}, 'tag': 'title'}
        True
        
        """
        data = {'attributes': {}}
        values = attribute.split()
        for value in values:
            if value.startswith('tei-'):
                data['tag'] = value[4:]
            elif value.startswith('teia-'):
                name, subvalue = value[5:].split('__')
                data['attributes'][name] = subvalue
        return data
    
    @staticmethod
    def _render_as_tei (root):
        """Return root transformed into a TEI XML string.

        >>> root = ElementTree.fromstring('<p><span class="tei-author">James, P. D.</span>, <span class="tei-title teia-level__m">Fire in the Belly</span>, <span class="tei-date">1997</span></p>')
        >>> BibliographicEntry._render_as_tei(root)
        '<bibl><author>James, P. D.</author>, <title level="m">Fire in the Belly</title>, <date>1997</date></bibl>'
        
        """
        root.tag = 'bibl'
        for element in root.iter():
            if 'class' in element.attrib:
                data = BibliographicEntry._parse_class_attribute(
                    element.attrib['class'])
                element.tag = data.get('tag', element.tag)
                for attribute, value in data['attributes'].items():
                    element.set(attribute, value)
                del element.attrib['class']
        return ElementTree.tostring(root, encoding='utf-8')

    def __unicode__ (self):
        name = '%s %s' % (self.title_article, self.reference_name)
        return name.strip()


class Language (models.Model):

    name = models.CharField(unique=True, max_length=32)
    color = models.CharField(blank=True, max_length=8)

    def __unicode__ (self):
        return self.name
