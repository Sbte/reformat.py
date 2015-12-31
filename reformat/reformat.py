import sys
import os
import re

def num_scopes(scope):
    scopes = 0
    for s in scope:
        if s not in ('namespace', 'struct', 'class', '('):
            scopes += 1
    return scopes

def is_global_scope(scope):
    return not num_scopes(scope)

class StringReplacer(object):
    Normal = 0
    String = 1
    Comment = 2
    MultilineComment = 3
    Index = 4

    def __init__(self, text, type, first = True, scope = None):
        self.text = text
        self.type = type
        self.start_of_line = first
        self.start_of_statement = first
        self.after_bracket = False

        if scope:
            self.scope = list(scope)
        else:
            self.scope = []

        self.keywords = ['for', 'if', 'while', 'return']

    def replace(self, search, replace):
        if self.type in [self.Normal, self.Index]:
            self.text = self.text.replace(search, replace)

    def regex_replace(self, search, replace):
        if self.type in [self.Normal, self.Index]:
            self.text = re.sub(search, replace, self.text)

    def repeated_regex_replace(self, search, replace):
        text = self.text
        self.regex_replace(search, replace)
        while text != self.text:
            text = self.text
            self.regex_replace(search, replace)

    def is_global_scope(self):
        return is_global_scope(self.scope)

    def handle_pointers(self, pointer_type='*'):
        '''Handles pointers in C-type languages'''
        escaped_pointer_type = re.escape(pointer_type)

        # Pointer casts (int *) and static_cast<int *>()
        self.regex_replace('([\(<])\s*(\w+)\s*'+escaped_pointer_type+'\s*([\)>])', '\g<1>\g<2> '+pointer_type+'\g<3>')
        self.regex_replace('([\(<]\w+ '+escaped_pointer_type+'[\)>]) \(', '\g<1>(')

        # Pointers as function argument etc, like f(a, *b)
        self.regex_replace('([^\w\)]+)( )'+escaped_pointer_type+'\s*([\w\(]+)', '\g<1>\g<2>'+pointer_type+'\g<3>')
        if self.start_of_statement:
            self.regex_replace('^( )'+escaped_pointer_type+'\s*([\w\(]+)', '\g<1>'+pointer_type+'\g<2>')

        # Pointers in function definitions and the global scope
        if self.is_global_scope() and self.start_of_statement:
            self.repeated_regex_replace('^([^=\+\-/%]+)'+escaped_pointer_type+' ', '\g<1>'+pointer_type)

        # lvalue pointers, up to any operator or bracket
        if self.start_of_statement and not '(' in self.scope and \
           (len(self.scope) and not self.scope[-1] in self.keywords):
            self.repeated_regex_replace('^([^=\+\-/%\(]+)'+escaped_pointer_type+' ', '\g<1>'+pointer_type)

        # Put back spaces when an operator with more than 1 char was before
        # the *
        self.repeated_regex_replace('(>>.*\w+.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')
        self.repeated_regex_replace('(<<.*\w+.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')

    def handle_templates(self):
        '''Handle C++ templates'''
        # Templates and includes should not have spaces
        self.repeated_regex_replace(' <\s*((?:[\w\.<>:\*& ])+?)\s*((?:> )*)>[^\S\n]*', '<\g<1>\g<2>> ')

        # Template members
        self.replace('> ::', '>::')

        # No space before a bracket
        self.repeated_regex_replace('<((?:[\w\.<>:\*& ])+?)((?:> )*)> \(', '<\g<1>\g<2>>(')

    def handle_brackets(self):
        '''Don't allow spaces before and after brackets'''

        # Handle spaces after a bracket
        if self.after_bracket:
            self.regex_replace('^[^\S\n]*([^\(])', ' \g<1>')

        self.regex_replace('\([^\S\n]+', '(')
        self.regex_replace('\s+\)', ')')

    def handle_eol_colon(self):
        '''Handle colons at the end of the line like in public:'''
        self.regex_replace('\s:[^\S\n]+$', ':')

    def handle_exponent(self):
        '''Handle exponents like 1.1e-1'''
        self.regex_replace('(\d*\.\d+|\d+)e ([\+\-]) (\d+)', '\g<1>e\g<2>\g<3>')

    def handle_unary(self):
        '''Handle unary operators like -1'''
        self.regex_replace('([^\w\]\)\-]) \- ', '\g<1> -')
        self.regex_replace('([^\w\]\)\+]) \+ ', '\g<1> +')

        if self.start_of_statement:
            self.regex_replace('^\s*\- ', '-')
            self.regex_replace('^\s*\+ ', '+')

        self.replace('return - ', 'return -')
        self.replace('return + ', 'return +')

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
            self.replace(key+'(', key+' (')

    def handle_punctuation(self):
        '''Handle punctuation like . , ;'''
        # Put spaces after , and ;
        for op in [',', ';']:
            self.regex_replace(re.escape(op)+'[^\S\n]*', op+' ')

        # Remove spaces before , ; .
        for op in [',', ';', '.']:
            self.regex_replace('\s+'+re.escape(op), op)

        # Remove spaces after .
        for op in ['.']:
            self.regex_replace(re.escape(op)+'[^\S\n]+', op)

        print self.scope

    def set_indenting(self):
        '''Set the indenting of the line part based on the scope'''
        if not self.start_of_line:
            return

        # Handle empty lines
        if self.text.endswith('\n') and self.text.lstrip() == '':
            self.text = '\n'
            return

        text = self.text.lstrip()
        text = "    " * num_scopes(self.scope) + text
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        str(self)

def is_normal_line_type(line_type):
    normal_types = [StringReplacer.Normal]
    if isinstance(line_type, list):
        return line_type[-1] in normal_types
    else:
        return line_type in normal_types

class ScopeSetter(object):
    def __init__(self, line_parts, base_scope=None):
        self.line_parts = line_parts
        self.new_line_parts = []

        self.scope = []
        self.base_scope = base_scope
        if base_scope:
            if isinstance(base_scope, list):
                self.scope = base_scope
            else:
                self.scope = [base_scope]

        self.scope_keyword = ''
        self.last_char = ''

        self.start_of_statement = True
        self.start_of_line = True
        self.after_bracket = False

    def add_line_part(self):
        '''Add a new line part to the new_line_parts list'''
        if self.new_line_part == '':
            return

        self.new_line_parts.append(StringReplacer(
            self.new_line_part, StringReplacer.Normal, self.start_of_line, self.scope))
        self.new_line_parts[-1].start_of_statement = self.start_of_statement
        self.new_line_parts[-1].after_bracket = self.after_bracket
        self.new_line_part = ''

        self.start_of_statement = True
        self.start_of_line = False
        self.after_bracket = False

    def parse(self):
        '''Parse the line_parts list that was set in the constructor'''
        brackets = {'{': '}', '(': ')'}

        self.start_of_statement = True
        for line_part in self.line_parts:
            self.start_of_line = line_part.start_of_line
            if line_part.type == StringReplacer.Normal:
                self.new_line_part = ''
                for char in line_part.text:
                    if len(self.scope) > 0  and char == '{' and \
                       self.scope[-1] == 'initializer list':
                        # We added a : scope that we need to remove
                        self.new_line_part += char
                        self.add_line_part()
                        self.scope.pop()
                        self.scope.append(char)
                        self.scope_keyword = ''
                    elif char in brackets.iterkeys():
                        self.new_line_part += char
                        self.add_line_part()
                        self.scope.append(self.scope_keyword or char)
                        self.scope_keyword = ''
                    elif char == '}':
                        self.add_line_part()
                        self.scope.pop()
                        self.scope_keyword = ''
                        self.new_line_part += char
                    elif char == ')':
                        self.new_line_part += char
                        self.add_line_part()
                        if self.scope[-1] in line_part.keywords:
                            self.start_of_statement = True
                        else:
                            self.start_of_statement = False
                        self.after_bracket = True
                        self.scope.pop()
                        self.scope_keyword = ''
                    elif len(self.scope) > 0 and self.scope[-1]  == 'initializer list' and char == ';':
                        # Remove the initializer list scope from all previous scopes
                        for i in xrange(len(self.new_line_parts)-1, -1, -1):
                            part = self.new_line_parts[i]
                            if 'initializer list' not in part.scope:
                                break
                            while 'initializer list' in part.scope:
                                part.scope.remove('initializer list')
                        self.new_line_part += char
                        self.add_line_part()
                    elif self.scope_keyword and char == ';':
                        self.scope_keyword = ''
                        self.new_line_part += char
                        self.add_line_part()
                    elif char == ':' and self.last_char == ')':
                        self.new_line_part += char
                        self.add_line_part()
                        self.start_of_statement = False
                        self.scope.append('initializer list')
                    elif char == ';':
                        self.new_line_part += char
                        self.add_line_part()
                    else:
                        self.new_line_part += char

                    # Store the last char to be able to detect initializer lists
                    if not re.match('\s', char):
                        self.last_char = char

                    for keyword in ('namespace', 'class', 'struct'):
                        if re.match('^\W*'+keyword+'\W$', self.new_line_part):
                            self.scope_keyword = keyword

                    for keyword in line_part.keywords:
                        if re.match('\W+'+keyword+'\W$', self.new_line_part) or \
                           re.match('^'+keyword+'\W$', self.new_line_part):
                            self.scope_keyword = keyword
                if self.new_line_part:
                    self.add_line_part()
            else:
                line_part.scope = list(self.scope)
                self.new_line_parts.append(line_part)
                if line_part.type == StringReplacer.Comment:
                    self.start_of_statement = True
                else:
                    self.start_of_statement = False

        # All scopes should be closed at the end of the file
        if self.base_scope:
            if isinstance(self.base_scope, list):
                assert self.scope == self.base_scope
            else:
                assert self.scope == [self.base_scope]
        else:
            assert self.scope == []

        return self.new_line_parts

def reformat(text_in, base_scope=None, set_indent=False):
    if isinstance(text_in, basestring):
        lines = text_in.splitlines(True)
    else:
        lines = text_in

    line_type = [StringReplacer.Normal]

    line_parts = []
    for line_num, line in enumerate(lines):
        orig_line = line
        line_part = ''
        if line_type[-1] == StringReplacer.Comment:
            line_type.pop()

        first = True
        for pos, char in enumerate(orig_line):
            line_part += char

            if line_type[-1] == StringReplacer.MultilineComment:
                if line_part.endswith('*/'):
                    line_parts.append(StringReplacer(
                        line_part, line_type.pop(), first))
                    first = False
                    line_part = ''
                    continue
                else:
                    continue

            if line_part.endswith('/*'):
                line_parts.append(StringReplacer(
                    line_part[:-2], line_type[-1], first))
                line_type.append(StringReplacer.MultilineComment)
                first = False
                line_part = '/*'
                continue

            if char == '"':
                if line_type[-1] == StringReplacer.String:
                    line_parts.append(StringReplacer(
                        line_part, line_type.pop(), first))
                else:
                    line_parts.append(StringReplacer(
                        line_part, line_type[-1], first))
                    line_type.append(StringReplacer.String)
                first = False
                line_part = ''
                continue

            if line_part.endswith('//'):
                line_parts.append(StringReplacer(
                    line_part[:-2], line_type[-1], first))
                line_type.append(StringReplacer.Comment)
                first = False
                line_part = orig_line[pos-1:]
                break

            if line_part.endswith('#pragma'):
                line_parts.append(StringReplacer(
                    line_part[:-7], line_type[-1], first))
                line_type.append(StringReplacer.Comment)
                first = False
                line_part = orig_line[pos-6:]
                break

            if line_part.endswith('[') and is_normal_line_type(line_type):
                line_parts.append(StringReplacer(
                    line_part[:-1], line_type[-1], first))
                line_type.append(StringReplacer.Index)
                first = False
                line_part = '['
                continue

            if line_part.endswith(']') and line_type[-1] == StringReplacer.Index:
                line_parts.append(StringReplacer(
                    line_part, line_type.pop(), first))
                first = False
                line_part = ''
                continue

        line_parts.append(StringReplacer(line_part, line_type[-1], first))

    # Check that we popped all other line_types
    # assert line_type == [StringReplacer.Normal]

    set_scopes = ScopeSetter(line_parts, base_scope)
    line_parts = set_scopes.parse()

    text = ''
    for line_part in line_parts:
        if line_part.type not in [StringReplacer.Normal, StringReplacer.Index]:
            text += str(line_part)
            continue

        # Put spaces around operators
        ops = ['=', '+', '/', '-', '<', '>', '%', '*', '&', '|', ':', '?']
        for op in ops:
            line_part.replace(op, ' '+op+' ')
            line_part.replace('  '+op, ' '+op)
            line_part.replace(op+'  ', op+' ')

        # Remove spaces around ::
        line_part.replace(' : : ', '::')

        line_part.handle_eol_colon()

        line_part.handle_increment_and_decrement_operator()

        # Remove spaces between things like // and ==
        for op2 in ['=', '<', '>', '/', '&', '|']:
            for op1 in ['=', '+', '-', '*', '/', '<', '>', '&', '|']:
                line_part.replace(op1+' '+op2, op1+op2)

        # Remove spaces in indices
        if (line_part.type == StringReplacer.Index):
            for op in ops:
                line_part.replace(' '+op+' ', op)

        # != is different because we don't want spaces around !
        line_part.replace('! =', '!=')
        line_part.replace('!=', ' != ')
        line_part.replace('!=  ', '!= ')
        line_part.replace('  !=', ' !=')

        # Remove spaces around operators
        for op in ['->']:
            line_part.replace(' '+op, op)
            line_part.replace(op+' ', op)

        line_part.handle_keywords()

        line_part.handle_templates()
        line_part.handle_exponent()

        line_part.handle_pointers('*')
        line_part.handle_pointers('&')

        line_part.handle_unary()

        # Comments at the start of a line_part should stay there
        line_part.regex_replace('^ //', '//')

        if line_part.start_of_statement and not line_part.start_of_line:
            line_part.regex_replace('^[^\S\n]+', '')

        line_part.handle_brackets()
        line_part.handle_punctuation()

        # Pointer dereference ->
        line_part.regex_replace('\s*\-\s*>[^\S\n]*', '->')

        # Includes should have a space
        line_part.replace('include<', 'include <')

        if set_indent:
            line_part.set_indenting()

        text += str(line_part)

    # Remove spaces at the end of the lines
    text = re.sub('[^\S\n]+$', '', text, flags=re.MULTILINE)

    # Remove spaces at the start of the line that were added by us
    ops = ['=', '+', '/', '-', '<', '>', '%', '*', '&', '|', ':', '?']
    for op in ops:
        text = re.sub('^ '+re.escape(op), op, text, flags=re.MULTILINE)

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
