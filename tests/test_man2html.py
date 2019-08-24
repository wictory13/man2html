from man2html import Converter
import unittest
from dominate import tags


def add_head(doc):
    doc_head = doc.add(tags.head())
    with doc_head:
        tags.meta(charset='utf-8')
        tags.title('Man')
        tags.link(rel='stylesheet', href='styles.css')
    return doc


def add_row(row, first, second, third):
    column_left = tags.div(cls='column left')
    paragraph = tags.p()
    paragraph.add(first)
    column_left.add(paragraph)
    column_center = tags.div(cls='column center')
    paragraph = tags.p()
    paragraph.add(second)
    column_center.add(paragraph)
    column_right = tags.div(cls='column right')
    paragraph = tags.p()
    paragraph.add(third)
    column_right.add(paragraph)
    row.add(column_left)
    row.add(column_center)
    row.add(column_right)
    return row


class TestMan2Html(unittest.TestCase):
    def test_font_styles(self):
        c = Converter('Man', file='font_styles.man')
        c.translate()
        text = c.html.render()
        text = c.change_special_symbols(text)
        doc = tags.html(lang='en')
        doc = add_head(doc)
        doc_body = doc.add(tags.body())
        lines = [tags.b('one'), '\ntwo', tags.b('three'), tags.b('four'),
                 tags.i('five'), tags.b('six'), '\nseven eight',
                 tags.b('nine'), '\nten eleven twelve', tags.i('13'),
                 tags.b('14'), tags.i('15'), tags.i('file'), '\n.',
                 tags.small('bbbbb'), tags.small('aaaaaa dfghjhg'),
                 tags.b('--posix'), tags.i('file1 file2')]
        with doc_body:
            paragraph = tags.p()
            for line in lines:
                paragraph += line
        self.assertEqual(doc.render(), text)

    def test_many_argument_strings(self):
        c = Converter('Man', file='links.man')
        c.translate()
        text = c.html.render()
        text = c.change_special_symbols(text)
        doc = tags.html(lang='en')
        doc = add_head(doc)
        doc_body = tags.body()
        row = tags.div(cls='row')
        row = add_row(row, 'GREP(1)', 'User Commands', 'GREP(1)')
        doc_body.add(row)
        with doc_body:
            paragraph = tags.p()
            paragraph += (tags.a('the bug-reporting address',
                                 href='mailto:bug-grep@gnu.org'))
            paragraph += tags.br()
            paragraph += (tags.a(
                'email archive',
                href='http://lists.gnu.org/mailman/listinfo/bug-grep'))
            paragraph += tags.br()
            paragraph += tags.br()
        row = tags.div(cls='row')
        row = add_row(row, 'GNU grep 3.1', '2017-06-21', 'GREP(1)')
        doc_body.add(row)
        doc.add(doc_body)
        self.assertEqual(doc.render(), text)

    def test_file_structure(self):
        c = Converter('Man', file='structured_file.man')
        c.translate()
        text = c.html.render()
        text = c.change_special_symbols(text)
        doc = tags.html(lang='en')
        doc = add_head(doc)
        doc_body = tags.body()
        row = tags.div(cls='row')
        row = add_row(row, 'BASH(1)', '', 'BASH(1)')
        doc_body.add(row)
        with doc_body:
            tags.h2('NAME')
            content = tags.div(cls='content')
            paragraph = tags.p()
            paragraph += '\ngrep, egrep, fgrep, rgrep'
            content.add(paragraph)
            content.add(tags.h4('Simple Commands'))
            content2 = tags.div(cls='content')
            content2.add(tags.br())
            paragraph = tags.p()
            paragraph += '\nA \\fIsimple command\\fP'
            content2.add(paragraph)
            def_list = tags.dl()
            def_termin = tags.dt()
            def_termin.add('\nInterpret')
            def_list.add(def_termin)
            def_list.add(tags.dd(cls='indent'))
            content2.add(def_list)
            def_list = tags.dl()
            def_termin = tags.dt(cls='short')
            def_termin.add((tags.b('%%')))
            def_list.add(def_termin)
            def_def = tags.dd(cls='indent')
            def_def.add('\nA literal')
            def_list.add(def_def)
            content2.add(def_list)
            content.add(content2)
        row = tags.div(cls='row')
        row = add_row(row, 'GNU Bash 4.4', '2016-08-26', 'BASH(1)')
        doc_body.add(row)
        doc.add(doc_body)
        doc = c.change_special_symbols(doc.render())
        self.assertEqual(doc, text)

    def test_other(self):
        c = Converter('Man', file='diff.man')
        c.translate()
        text = c.html.render()
        text = c.change_special_symbols(text)
        doc = tags.html(lang='en')
        doc = add_head(doc)
        doc_body = tags.body()
        row = tags.div(cls='row')
        row = add_row(row, 'GCC(1)', '', 'GCC(1)')
        doc_body.add(row)
        with doc_body:
            paragraph = tags.p()
            paragraph.add(tags.br())
            paragraph.add('\n\\f(CW        c  c-header  cpp-output\\fP')
            paragraph.add(tags.br())
            paragraph.add(tags.br())
            def_list = tags.dl()
            def_termin = tags.dt()
            def_termin.add('\n')
            def_termin.add('\\fB-x none\\fR')
            def_def = tags.dd(cls='indent')
            def_def.add('\nstandard_output.')
            def_list.add(def_termin)
            def_list.add(def_def)
        row = tags.div(cls='row')
        row = add_row(row, '', '2018-07-20', 'GCC(1)')
        doc_body.add(row)
        doc.add(doc_body)
        doc = c.change_special_symbols(doc.render())
        self.assertEqual(doc, text)
