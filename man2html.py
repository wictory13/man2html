import os
import re
import subprocess
import argparse
import shlex
import sys

from dominate import tags

LINKS_RE = re.compile(r'(\.URL|\.MTO) (\S+)( "([^"]+)"| \S+|)')
PAGE_SECTION_RE = re.compile(r'([a-z]+)(\((\d+)\)|)')

REGISTRY = {}


def register(*operators):
    def inner_register(f):
        for tag in operators:
            REGISTRY[tag] = f

        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return inner_register


def create_parser():
    ap = argparse.ArgumentParser(
        description='Translates documentation from man-format to html-format')
    man = ap.add_mutually_exclusive_group(required=True)
    man.add_argument('-f', '--file', type=str)
    man.add_argument('-n', '--name', type=str)
    ap.add_argument('-t', '--title', type=str, default='Man',
                    help='title of the html-page')
    ap.add_argument('-o', '--output', type=str, default='output',
                    help='title of the output file')
    return ap


class Converter:
    SPECIAL_SYMBOLS = {r'\*(L&quot;': '"',
                       r'\*(R&quot;': '"',
                       r'\*R': '&reg;',
                       r'\*(Tm': '&trade;',
                       r'\*(lq': '&laquo;',
                       r'\*(rq': '&raquo;',
                       r'\|.': '.',
                       r'\-\^\-': '--',
                       r'\-': '-',
                       r'\&': '',
                       r'\(en': '-',
                       r'\(bu': '&bull;',
                       r'\ ': ' ',
                       r'\fB': '<span class="bold">',
                       r'\fI': '<span class="italic">',
                       r'\f(CW':
                           '<span style="font-family: monospace;">',
                       r'\fR': '</span>',
                       r'\fP': '</span>',
                       r'\(aq': "'",
                       r'\(dq': '"',
                       r'\*(C+': 'C++',
                       r'\s-1': '',
                       r'\s0': '',
                       r'\|_': r'_',
                       r'C`': r'"',
                       r"C'": r'"',
                       r'\|': r'',
                       r'\e': '\\',
                       r'amp;': '',
                       r'\,': '',
                       r'\/': '',
                       r'&quot;, &quot;': ', ',
                       r'\*(': '',
                       r'\(co': '&copy;',
                       r'&quot;': ''}

    def __init__(self, _title, file=None, data=None):
        self.file = file
        self.data = data
        self.html = tags.html(lang='en')
        self.head = self.html.add(tags.head())
        self.head.add(tags.meta(charset='utf-8'))
        self.head.add(tags.title(_title))
        self.head.add(tags.link(rel='stylesheet', href='styles.css'))
        self.body = self.html.add(tags.body())
        self.paragraph = None
        self.div_header = None
        self.div_subheader = None
        self.date = None
        self.program = None
        self.name_page = None
        self.iterator = None
        self.indent = 0
        self.rs = None

    def process_line(self, line):
        for tag in REGISTRY:
            if line.startswith(tag):
                REGISTRY[tag](self, line)
                return True
        return False

    def translate(self):
        self.iterator = iter(self.get_line())
        for line in self.iterator:
            check_tag = self.process_line(line)
            if (line.startswith('.') or line.startswith("'") or
                    line.startswith(r'\{') or line.startswith(r'\fI\|\\$1')
                    or line.startswith(r'\\$2')):
                continue
            if not check_tag:
                if line:
                    self.add_roman(line)
                else:
                    self.add_br()
        if self.program and self.date and self.name_page:
            self.add_row(self.program, self.date, self.name_page)
        elif self.name_page and self.date:
            self.add_row('', self.date, self.name_page)
        elif self.name_page:
            self.add_row('', '', self.name_page)

    def get_line(self):
        if self.file:
            with open(self.file) as f:
                for line in f:
                    yield line
        else:
            for line in self.data.splitlines():
                yield line

    def change_special_symbols(self, text):
        for seq, symbol in self.SPECIAL_SYMBOLS.items():
            text = text.replace(seq, symbol)
        return text

    def save(self, output_file):
        text = self.html.render()
        text = self.change_special_symbols(text)
        with open(output_file + '.html', 'w') as f:
            f.write(text)

    @staticmethod
    def select_quotes(str_):
        lex = shlex.shlex(str_)
        lex.quotes = '"'
        lex.whitespace_split = True
        lex.commenters = ''
        return list(lex)

    @register('.BR ', '.BI ', '.RB ', '.RI ', '.IB ', '.IR ', '.SB ')
    def add_joint_styles(self, line):
        operator = line[1:3]
        words = self.select_quotes(self.remove_operator(line))
        for j in range(len(words)):
            symbol = operator[j % 2]
            if symbol == 'B':
                self.add_bold(words[j])
            elif symbol == 'I':
                self.add_italics(words[j])
            elif symbol == 'S':
                self.add_small(words[j])
            else:
                self.add_roman(words[j])

    @register('.B ')
    def add_bold(self, line):
        self.add_paragraph()
        self.paragraph += tags.b(self.remove_operator(line))

    @register('.I ')
    def add_italics(self, line):
        self.add_paragraph()
        self.paragraph += tags.i(self.remove_operator(line))

    def add_roman(self, line):
        self.add_paragraph()
        self.paragraph += '\n' + line.rstrip('\n')

    @register('.SM')
    def add_small(self, line):
        self.add_paragraph()
        self.paragraph += tags.small(self.remove_operator(line))

    @register('.IP ')
    def add_indent_paragraph(self, line):
        line = self.select_quotes(self.remove_operator(line))
        if len(line) > 1:
            self.indent = int(line[1])
        self.paragraph = None
        if self.div_subheader:
            par = self.div_subheader.add(tags.dl())
        elif self.div_header:
            par = self.div_header.add(tags.dl())
        else:
            par = self.body.add(tags.dl())
        if len(line[0]) < self.indent:
            self.paragraph = par.add(tags.dt(cls='short'))
        else:
            self.paragraph = par.add(tags.dt())
        if not self.process_line(line[0]):
            self.add_roman(line[0])
        self.paragraph = par.add(tags.dd(cls='indent'))

    @register('.PP', '.LP', '.P', '.br', '.Sp')
    def add_br(self, *args):
        if not self.paragraph:
            if self.div_subheader:
                self.div_subheader.add(tags.br())
            elif self.div_header:
                self.div_header.add(tags.br())
            else:
                self.body.add(tags.br())
        else:
            self.paragraph.add(tags.br())

    @register('.Vb ')
    def add_verbatim_begin(self, *args):
        self.add_paragraph()
        first_time = True
        while True:
            if first_time:
                self.paragraph.add(tags.br())
                first_time = False
            next_line = next(self.iterator)
            if next_line.startswith('.Ve'):
                break
            if not self.process_line(next_line):
                self.add_roman(next_line)
            self.paragraph.add(tags.br())

    @register('.MTO', '.URL')
    def add_email_or_url(self, line):
        self.add_paragraph()
        r = re.findall(LINKS_RE, line)
        data = r[0]
        text = data[3] if data[3] else data[2]
        address = data[1]
        if data[0] == '.URL':
            self.paragraph.add(tags.a(text, href=address))
        else:
            self.paragraph.add(tags.a(text, href='mailto:{}'.format(address)))

    @register('.SH ')
    def add_header(self, line):
        self.div_header = None
        self.div_subheader = None
        self.paragraph = None
        self.body.add(tags.h2(line[4:].strip('"\n')))
        self.div_header = self.body.add(tags.div(cls='content'))

    @register('.SS ')
    def add_subheader(self, line):
        self.div_subheader = None
        self.paragraph = None
        self.div_header.add(tags.h4(line[4:].strip('"\n')))
        self.div_subheader = self.div_header.add(tags.div(cls='content'))

    def add_paragraph(self):
        if not self.paragraph:
            if self.div_subheader:
                if self.rs:
                    self.paragraph = self.div_subheader.add(
                        tags.p(style="margin-left: {}em;".format(self.rs)))
                else:
                    self.paragraph = self.div_subheader.add(tags.p())
            elif self.div_header:
                if self.rs:
                    self.paragraph = self.div_header.add(
                        tags.p(style="margin-left: {}em;".format(self.rs)))
                else:
                    self.paragraph = self.div_header.add(tags.p())
            else:
                if self.rs:
                    self.paragraph = self.body.add(
                        tags.p(style="margin-left: {}em;".format(self.rs)))
                else:
                    self.paragraph = self.body.add(tags.p())

    @register('.TH ')
    def add_man_data(self, line):
        data = self.select_quotes(self.remove_operator(line))
        # name, page, date, program, man_title = data
        self.name_page = '{}({})'.format(data[0], data[1])
        self.date = data[2] if len(data) > 2 else ''
        self.program = data[3] if len(data) > 3 else ''
        man_title = data[4] if len(data) > 4 else ''
        self.add_row(self.name_page, man_title, self.name_page)

    def add_row(self, *args):
        with self.body.add(tags.div(cls='row')):
            for j in range(len(args)):
                if j == 0:
                    cls = 'left'
                elif j == len(args) - 1:
                    cls = 'right'
                else:
                    cls = 'center'
                tags.div(tags.p(args[j]), cls='column {}'.format(cls))

    @register('.TP ', '.TP')
    def add_hanging_paragraph(self, line):
        x = self.remove_operator(line)
        if x:
            self.indent = int(x)
        self.paragraph = None
        if self.div_subheader:
            par = self.div_subheader.add(tags.dl())
        elif self.div_header:
            par = self.div_header.add(tags.dl())
        else:
            par = self.body.add(tags.dl())
        next_line = next(self.iterator)
        if len(self.remove_operator(next_line)) < self.indent:
            self.paragraph = par.add(tags.dt(cls='short'))
        else:
            self.paragraph = par.add(tags.dt())
        if not self.process_line(next_line):
            self.add_roman(next_line)
        self.paragraph = par.add(tags.dd(cls='indent'))

    @register('.RS')
    def add_start_indent(self, line):
        self.rs = self.remove_operator(line).strip() or 0.5

    @register('.RE')
    def add_end_indent(self, *args):
        self.rs = None

    def remove_operator(self, line):
        for op in REGISTRY:
            if line.startswith(op):
                return line.replace(op, '', 1).strip('\n ')
        return line.rstrip('\n ')


if __name__ == '__main__':
    parser = create_parser()
    namespace = parser.parse_args()
    if namespace.file:
        c = Converter(namespace.title, file=namespace.file)
    else:
        if os.name != 'posix':
            print('Man page search is available only for Linux',
                  file=sys.stderr)
            sys.exit(1)
        params = re.findall(PAGE_SECTION_RE, namespace.name)[0]
        archive = subprocess.run(['man', '-w', params[2] if params[2] else '1',
                                  params[0]], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
        if archive.returncode != 0:
            print('No such man file found', file=sys.stderr)
            sys.exit(2)
        archive_path = archive.stdout.decode().strip()
        man_content = subprocess.run(['gzip', '-c', '-d', archive_path],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL)
        content = man_content.stdout.decode()
        c = Converter(namespace.title, data=content)
    c.translate()
    c.save(namespace.output)
