import sys
import os
import re

from .Scope import Scope

class StringReplacer(object):
    Normal = 0
    String = 1
    Comment = 2
    MultilineComment = 3
    EOL = 4

    brackets = {'(': ')', '[': ']', '<': '>'}
    keywords = ['for', 'if', 'while', 'return']

    def __init__(self, text, type, first = True, scope = None):
        self.text = text
        self.type = type
        self.start_of_line = first
        self.start_of_statement = first
        self.after_bracket = False
        self.pos = 0

        if isinstance(scope, Scope):
            self.scope = scope
        else:
            self.scope = Scope(scope)

        self.indentation = ''
        if self.start_of_line:
            self.indentation = re.match('^\s*', self.text).group(0)

    def replace(self, search, replace):
        if self.type in [self.Normal]:
            self.text = self.text.replace(search, replace)

    def regex_replace(self, search, replace):
        if self.type in [self.Normal]:
            self.text = re.sub(search, replace, self.text)

    def repeated_replace(self, search, replace):
        text = self.text
        self.replace(search, replace)
        while text != self.text:
            text = self.text
            self.replace(search, replace)

    def repeated_regex_replace(self, search, replace):
        text = self.text
        self.regex_replace(search, replace)
        while text != self.text:
            text = self.text
            self.regex_replace(search, replace)

    def handle_pointers(self, pointer_type='*'):
        '''Handles pointers in C-type languages'''
        escaped_pointer_type = re.escape(pointer_type)

        # Pointers in function definitions and the global scope
        if self.scope.is_global():
            self.repeated_regex_replace('^([^=\+\-/%]+)'+escaped_pointer_type+' ', '\g<1>'+pointer_type)

        # lvalue pointers, up to any operator or bracket
        if self.start_of_statement:
            counts = True
            for s in self.scope:
                for b in self.brackets:
                    if b in s:
                        counts = False
            if self.scope.last in self.keywords:
                counts = False
            if counts:
                self.repeated_regex_replace(
                    '^([^=\+\-/%\(]+)'+escaped_pointer_type+' ',
                    '\g<1>'+pointer_type)

        # Put back spaces when an operator with more than 1 char was before
        # the *
        self.repeated_regex_replace('(>>.*\w+.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')
        self.repeated_regex_replace('(<<.*\w+.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')

    def handle_templates(self):
        '''Handle C++ templates'''
        # Space after multiple closing brackets
        if self.after_bracket:
            self.regex_replace('^\s*>', ' >')

    def handle_brackets(self):
        '''Don't allow spaces before and after brackets'''
        for lb, rb in self.brackets.iteritems():
            if not lb in self.scope.last and \
               not (self.scope.last in self.keywords and lb == '('):
                continue

            elb = re.escape(lb)
            erb = re.escape(rb)

            self.regex_replace('\s*'+elb+'\s*', lb)
            self.regex_replace('\s*'+erb+'\s*', rb)

        if self.after_bracket and self.start_of_statement:
            self.text = ' ' + self.text

    def handle_colon(self):
        '''Handle colons at the end of the line like in public:'''
        if 'class' in self.scope and self.start_of_statement:
            self.repeated_regex_replace('^([^=\+\-/%\(]+) :', '\g<1>:')

    def handle_exponent(self):
        '''Handle exponents like 1.1e-1'''
        self.regex_replace('(\d*\.\d+|\d+)e ([\+\-]) (\d+)', '\g<1>e\g<2>\g<3>')

    def handle_unary(self, operators=None):
        '''Handle unary operators like -1'''
        for op in operators:
            eop = re.escape(op)
            self.regex_replace('([^\w\]\)'+eop+']) '+eop+' ', '\g<1> '+op)

            if self.start_of_statement:
                self.regex_replace('^\s*'+eop+' ', op)

            self.replace('return '+op+' ', 'return '+op)

        # Increment and decrement
        for op1 in ['+', '-']:
            for op2 in ['+', '-', '*']:
                self.replace(op1+op1+' '+op2, op1+op1+' '+op2+ ' ')

    def handle_increment_and_decrement_operator(self):
        '''Handle ++ and -- operators'''
        for op in ['+', '-']:
            escaped_op = re.escape(op)
            self.replace(' '+op+' '+op+' ', op+op)
            self.regex_replace('([\+\-\*\/&\|])'+escaped_op+escaped_op,
                               '\g<1> '+op+op)
            self.regex_replace(escaped_op+escaped_op+'([\+\-\*\/&\|])',
                               op+op+' \g<1>')

    def handle_keywords(self):
        '''Spaces after keywords'''
        for key in self.keywords:
            self.regex_replace(key+'$', key+' ')

    def handle_punctuation(self):
        '''Handle punctuation like . , ;'''
        # Put spaces after , and ;
        for op in [',', ';']:
            self.regex_replace(re.escape(op)+'\s*', op+' ')

        # Remove spaces before , ; .
        for op in [',', ';', '.']:
            self.regex_replace('\s+'+re.escape(op), op)

        # Remove spaces after .
        for op in ['.']:
            self.regex_replace(re.escape(op)+'\s+', op)

    def set_bracket_positions(self):
        '''Set the position of brackets in the scope'''
        if self.type == self.Normal and self.scope.last and \
           not isinstance(self.scope.last, dict) and \
           self.scope.last in self.brackets:
            if self.start_of_line or \
               self.text == self.scope.last:
                # Bracket at the end of the line
                self.scope.last = {self.scope.last: -1}
            else:
                self.scope.last = {self.scope.last: self.pos}

    def set_indenting(self):
        '''Set the indenting of the line part based on the scope'''
        self.set_bracket_positions()

        if not self.start_of_line:
            return

        # Handle empty lines
        if self.type == self.EOL:
            return

        self.text = self.text.lstrip()

        # Defines
        if self.text.startswith('#'):
            self.indentation = ''
            return

        scopes = self.scope.indented_scopes()

        # Align with brackets
        for s in self.scope:
            aligned = True
            for b in self.brackets:
                if b in s:
                    if isinstance(s, dict) and s[b] > 0:
                        if not aligned:
                            continue
                        self.indentation = s[b] * ' '
                        return
                    elif isinstance(s, dict) and s[b] == 0:
                        raise ValueError('Position can\'t be 0')
                    else:
                        aligned = False
                        scopes += 1

        # Class definitions (public is not indented,
        # but function definitions are)
        for s in ('class', 'struct'):
            if s in self.scope and not self.text.strip() in \
               ['private:', 'protected:', 'public:']:
                scopes += 1

        scopes -= self.text.strip() == ':' and \
                  self.scope.last == 'initializer list'

        self.indentation = "    " * scopes

    def __str__(self):
        if self.type == self.EOL:
            return '\n'
        elif self.start_of_line:
            return self.indentation + self.text.lstrip()
        else:
            return self.text

    def __repr__(self):
        str(self)

class ScopeSetter(object):
    def __init__(self, line_parts, base_scope=None):
        self.line_parts = line_parts
        self.new_line_parts = []

        self.scope = Scope(base_scope)
        self.base_scope = Scope(base_scope)

        self.scope_keyword = ''
        self.last_char = ''

        self.start_of_statement = True
        self.start_of_line = True
        self.after_bracket = False
        self.continuation = False

    def pop_scope(self, continuation=False):
        if not continuation and self.scope[-1] == 'continuation':
            self.scope = self.scope.parent

        self.scope = self.scope.parent

    def add_scope(self, item):
        self.scope = Scope(self.scope, item)

    def add_line_part(self, closing = False):
        '''Add a new line part to the new_line_parts list'''
        if self.new_line_part == '' or \
           (self.start_of_line and not self.new_line_part.strip()):
            return

        new_line_part = self.new_line_part

        # Add scope when a line continues from the last line
        if self.start_of_line and self.continuation and not closing and \
           (not len(self.scope) or self.scope[-1] != 'continuation'):
            self.add_scope('continuation')
        elif closing and len(self.scope) and self.scope[-1] == 'continuation':
            self.pop_scope(True)

        for keyword in ('namespace', 'class', 'struct'):
            if re.match('^\W*'+keyword+'\W+[^;]+$', self.new_line_part) or \
               re.match('^\W*'+keyword+'$', self.new_line_part):
                self.scope_keyword = keyword

        for keyword in StringReplacer.keywords:
            if re.match('\W+'+keyword+'\W*$', self.new_line_part) or \
               re.match('^'+keyword+'\W*$', self.new_line_part):
                self.scope_keyword = keyword

        self.new_line_parts.append(StringReplacer(
            self.new_line_part, StringReplacer.Normal, self.start_of_line, self.scope))
        self.new_line_parts[-1].start_of_statement = self.start_of_statement
        self.new_line_parts[-1].after_bracket = self.after_bracket
        self.new_line_part = ''

        if closing:
            for b in StringReplacer.brackets:
                while b in self.scope:
                    self.scope.remove(b)
            if 'initializer list' in self.scope:
                self.scope.remove('initializer list')

        if closing or self.start_of_line:
            self.continuation = False

        if new_line_part.strip() or closing:
            self.start_of_statement = True
            self.start_of_line = False
            self.after_bracket = False

    def parse(self):
        '''Parse the line_parts list that was set in the constructor'''
        self.continuation = False
        self.start_of_statement = True
        for line_part in self.line_parts:
            self.start_of_line = line_part.start_of_line
            if line_part.type == StringReplacer.Normal:
                self.new_line_part = ''
                for char in line_part.text:
                    if char == '>' and self.new_line_part.endswith('-'):
                        # For instance for (int i = 0; i < a->c; ++i)
                        self.new_line_part += char
                    elif char in line_part.brackets.iterkeys():
                        self.add_line_part()
                        self.new_line_part += char
                        self.add_scope(self.scope_keyword or char)
                        self.scope_keyword = ''
                        self.add_line_part()
                    elif char == '{':
                        self.add_line_part()
                        if self.scope.last == 'initializer list':
                            self.pop_scope()
                        self.new_line_part += char
                        self.add_line_part(True)
                        self.add_scope(self.scope_keyword or char)
                        self.scope_keyword = ''
                    elif char == '}':
                        self.add_line_part(True)
                        self.pop_scope()
                        self.scope_keyword = ''
                        self.new_line_part += char
                        self.add_line_part()
                    elif char == ')' and self.scope.last in line_part.keywords:
                        self.new_line_part += char
                        self.add_line_part()
                        self.after_bracket = True
                        self.pop_scope()
                        self.scope_keyword = ''
                    elif char in line_part.brackets.get(
                            self.scope.last, []):
                        self.new_line_part += char
                        self.add_line_part()
                        self.after_bracket = True
                        self.start_of_statement = False
                        self.continuation = False
                        self.pop_scope()
                        self.scope_keyword = ''
                    elif self.scope_keyword and char == ';':
                        self.scope_keyword = ''
                        self.new_line_part += char
                        self.add_line_part(True)
                    elif char == ':' and self.last_char == ')':
                        self.add_line_part(True)
                        self.add_scope('initializer list')
                        self.new_line_part += char
                        self.add_line_part()
                        self.continuation = True
                    elif char == ';':
                        self.new_line_part += char
                        self.add_line_part(True)
                    elif char == ',' and self.scope.last in line_part.brackets:
                        self.new_line_part += char
                        self.add_line_part()
                        self.start_of_statement = True
                    else:
                        self.new_line_part += char

                    # Store the last char to be able to detect initializer lists
                    if not re.match('\s', char):
                        self.last_char = char

                    for keyword in ['private', 'protected', 'public']:
                        if re.match('^\s*'+keyword+':$', self.new_line_part):
                            self.add_line_part()
                if self.new_line_part:
                    new_line_part = self.new_line_part
                    self.add_line_part()

                    # There was stuff on this line that
                    # continues on the next line
                    if new_line_part.rstrip():
                        self.continuation = True
                        self.start_of_statement = False
            else:
                line_part.scope = self.scope
                self.new_line_parts.append(line_part)

        for b in StringReplacer.brackets:
            while b in self.scope:
                self.scope.remove(b)

        # All scopes should be closed at the end of the file
        assert self.scope == self.base_scope

        return self.new_line_parts

    def merge_equal_scopes(self):
        '''Merge line parts that have equal scopes'''
        prev_line_part = None
        new_line_parts = []
        for line_part in self.new_line_parts:
            if not prev_line_part:
                new_line_parts.append(line_part)
                prev_line_part = line_part
                continue

            if line_part.type == prev_line_part.type and \
               line_part.scope == prev_line_part.scope and \
               not line_part.type == StringReplacer.EOL:
                prev_line_part.text += line_part.text
                continue

            new_line_parts.append(line_part)
            prev_line_part = line_part

        self.new_line_parts = new_line_parts
        return self.new_line_parts

class LineSplitter(object):
    def __init__(self, text):
        self.lines = []
        if isinstance(text, basestring):
            self.lines = text.splitlines(True)
        else:
            self.lines = text
        self.line_type = []
        self.line_parts = []
        self.current_line_part = ''
        self.start_of_line = True

    def add_line_part(self, line_part):
        if not line_part.text.strip() and not line_part.type == StringReplacer.EOL:
            self.current_line_part = str(line_part)
            return

        self.current_line_part = ''
        self.line_parts.append(line_part)
        self.start_of_line = False

    def parse(self):
        self.line_type = [StringReplacer.Normal]

        self.line_parts = []
        for line_num, line in enumerate(self.lines):
            self.current_line_part = ''
            if self.line_type[-1] == StringReplacer.Comment:
                self.line_type.pop()

            self.start_of_line = True
            for pos, char in enumerate(line):
                self.current_line_part += char

                if self.line_type[-1] == StringReplacer.MultilineComment:
                    if self.current_line_part.endswith('*/'):
                        self.add_line_part(StringReplacer(
                            self.current_line_part, self.line_type.pop(), self.start_of_line))
                        continue
                    else:
                        continue

                if self.current_line_part.endswith('/*'):
                    self.add_line_part(StringReplacer(
                        self.current_line_part[:-2], self.line_type[-1], self.start_of_line))
                    self.line_type.append(StringReplacer.MultilineComment)
                    self.current_line_part += '/*'
                    continue

                if char == '"':
                    if self.line_type[-1] == StringReplacer.String:
                        self.add_line_part(StringReplacer(
                            self.current_line_part, self.line_type.pop(), self.start_of_line))
                    else:
                        self.add_line_part(StringReplacer(
                            self.current_line_part, self.line_type[-1], self.start_of_line))
                        self.line_type.append(StringReplacer.String)
                    continue

                if self.current_line_part.endswith('//'):
                    self.add_line_part(StringReplacer(
                        self.current_line_part[:-2], self.line_type[-1], self.start_of_line))
                    self.line_type.append(StringReplacer.Comment)
                    self.current_line_part += line[pos-1:]
                    break

                if self.current_line_part.lstrip() == '#':
                    self.add_line_part(StringReplacer(
                        self.current_line_part[:-1], self.line_type[-1], self.start_of_line))
                    self.line_type.append(StringReplacer.Comment)
                    self.current_line_part += line[pos:]
                    break

            last = self.current_line_part
            if self.current_line_part.rstrip():
                self.add_line_part(StringReplacer(self.current_line_part.rstrip(),
                                                  self.line_type[-1], self.start_of_line))
            if last.endswith('\n'):
                self.add_line_part(StringReplacer(self.current_line_part,
                                                  StringReplacer.EOL, self.start_of_line))

def reformat(text_in, base_scope=None, set_indent=False):
    splitter = LineSplitter(text_in)
    splitter.parse()
    line_parts = splitter.line_parts

    # Check that we popped all other self.line_types
    # assert line_type == [StringReplacer.Normal]

    set_scopes = ScopeSetter(line_parts, base_scope)
    line_parts = set_scopes.parse()
    line_parts = set_scopes.merge_equal_scopes()

    text = ''
    pos = 0
    for line_part in line_parts:
        if line_part.type not in [StringReplacer.Normal]:
            if set_indent and line_part.type not in [StringReplacer.MultilineComment]:
                line_part.set_indenting()

            text += str(line_part)
            continue

        # Put spaces around operators
        ops = ['=', '+', '/', '-', '<', '>', '%', '*', '&', '|', ':', '?']
        for op in ops:
            line_part.replace(op, ' '+op+' ')
            line_part.replace('  '+op, ' '+op)
            line_part.repeated_replace(op+'  ', op+' ')

        # Remove spaces around ::
        line_part.replace(' : : ', '::')

        line_part.handle_colon()

        line_part.handle_increment_and_decrement_operator()

        # Remove spaces between things like // and ==
        for op2 in ['=', '<', '>', '/', '&', '|']:
            for op1 in ['=', '+', '-', '*', '/', '<', '>', '&', '|']:
                line_part.replace(op1+' '+op2, op1+op2)

        # Remove spaces in indices
        if '[' in line_part.scope.last:
            for op in ops:
                line_part.replace(' '+op+' ', op)

        # != is different because we don't want spaces around !
        line_part.replace('! =', '!=')
        line_part.replace('!=', ' != ')
        line_part.replace('!=  ', '!= ')
        line_part.replace('  !=', ' !=')

        line_part.handle_keywords()

        line_part.handle_exponent()

        line_part.handle_pointers('*')
        line_part.handle_pointers('&')

        line_part.handle_unary(['+', '-', '&', '*'])

        # Comments at the start of a line_part should stay there
        line_part.regex_replace('^ //', '//')

        if line_part.start_of_statement and not line_part.start_of_line:
            line_part.regex_replace('^\s+', '')

        line_part.handle_brackets()
        line_part.handle_templates()
        line_part.handle_punctuation()

        # Pointer dereference ->
        line_part.regex_replace('\s*\-\s*>\s*', '->')

        # Includes should have a space
        line_part.replace('include<', 'include <')

        if set_indent:
            line_part.pos = pos+1
            line_part.set_indenting()

        new_text = str(line_part)
        if line_part.start_of_line:
            pos = len(new_text)
        else:
            pos += len(new_text)

        text += new_text

    # Remove spaces at the end of the lines
    text = re.sub('[^\S\n]+$', '', text, flags=re.MULTILINE)

    return text

def main():
    if len(sys.argv) < 2:
        print 'No filename'
        return

    fname = sys.argv[1]
    if not os.path.exists(fname):
        print fname, 'is not a valid filename'

    f = open(fname, 'r')
    lines = f.readlines()
    f.close()

    if not os.path.exists(fname+'.bak'):
        f = open(fname+'.bak', 'w')
        f.write(''.join(lines))
        f.close()

    text = reformat(lines, set_indent=True)

    f = open(fname, 'w')
    f.write(text)
    f.close()

if __name__ == "__main__":
    main()
