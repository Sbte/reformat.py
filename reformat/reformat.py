import sys
import os
import re

def is_global_scope(scope):
    for s in scope:
        if s not in ('namespace', 'struct', 'class'):
            return False
    return True

class StringReplacer(object):
    Normal = 0
    String = 1
    Comment = 2
    MultilineComment = 3
    Index = 4
    InitializerList = 5

    def __init__(self, text, type, scope = None):
        self.text = text
        self.type = type

        if scope:
            self.scope = list(scope)
        else:
            self.scope = []

    def replace(self, search, replace):
        if self.type in [self.Normal, self.Index, self.InitializerList]:
            self.text = self.text.replace(search, replace)

    def regex_replace(self, search, replace):
        if self.type in [self.Normal, self.Index, self.InitializerList]:
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
        self.regex_replace('(\W+) '+escaped_pointer_type+'\s*(\w+)', '\g<1> '+pointer_type+'\g<2>')

        # Pointers in function definitions and the global scope
        if self.is_global_scope():
            self.repeated_regex_replace('^([^=\+-/%]+)'+escaped_pointer_type+' ', '\g<1>'+pointer_type)

        # lvalue pointers, up to any operator or bracket
        self.repeated_regex_replace('^([^=\+-/%\(]+)'+escaped_pointer_type+' ', '\g<1>'+pointer_type)

        # Put back spaces when an operator with more than 1 char was before
        # the *
        self.repeated_regex_replace('(>>.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')
        self.repeated_regex_replace('(<<.*) '+escaped_pointer_type+'([^ ])', '\g<1> '+pointer_type+' \g<2>')

    def handle_brackets(self):
        '''Don't allow spaces before and after brackets'''

        self.replace('( ', '(')
        self.replace(' )', ')')

    def __str__(self):
        if self.text.endswith('\n'):
            return self.text.rstrip() + '\n'
        else:
            return self.text

    def __repr__(self):
        str(self)

def is_normal_line_type(line_type):
    normal_types = [StringReplacer.Normal, StringReplacer.InitializerList]
    if isinstance(line_type, list):
        return line_type[-1] in normal_types
    else:
        return line_type in normal_types

def set_scopes(line_parts):
    new_line_parts = []
    scope = []
    scope_keyword = ''
    for line_part in line_parts:
        if line_part.type == StringReplacer.Normal:
            new_line_part = ''
            for char in line_part.text:
                if char == '{':
                    if scope_keyword == 'initializer list':
                        # We added a : scope that we need to remove first
                        scope.pop()
                        scope_keyword = ''

                    new_line_parts.append(StringReplacer(new_line_part, StringReplacer.Normal, scope))
                    scope.append(scope_keyword)
                    scope_keyword = ''
                    new_line_part = ''
                elif char == '}':
                    new_line_parts.append(StringReplacer(new_line_part, StringReplacer.Normal, scope))
                    scope.pop()
                    scope_keyword = ''
                    new_line_part = ''
                elif scope_keyword and char == ';':
                    scope_keyword = ''

                new_line_part += char

                for keyword in ('namespace', 'class', 'struct'):
                    if re.match('^\W*'+keyword+'\W$', new_line_part):
                        scope_keyword = keyword
            if new_line_part:
                new_line_parts.append(StringReplacer(new_line_part, StringReplacer.Normal, scope))
        elif line_part.type == StringReplacer.InitializerList and is_global_scope(scope):
            scope.append('initializer list')
            scope_keyword = 'initializer list'
            new_line_part = ''
            line_part.scope = list(scope)
            new_line_parts.append(line_part)
        else:
            line_part.scope = list(scope)
            new_line_parts.append(line_part)

    # All scopes should be closed at the end of the file
    assert scope == []

    return new_line_parts

def reformat(text_in):
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

        for pos, char in enumerate(orig_line):
            line_part += char

            if line_type[-1] == StringReplacer.MultilineComment:
                if line_part.endswith('*/'):
                    line_parts.append(StringReplacer(line_part, line_type.pop()))
                    line_part = ''
                    continue
                else:
                    continue

            if line_part.endswith('/*'):
                line_parts.append(StringReplacer(line_part[:-2], line_type[-1]))
                line_type.append(StringReplacer.MultilineComment)
                line_part = '/*'
                continue

            if char == '"':
                if line_type[-1] == StringReplacer.String:
                    line_parts.append(StringReplacer(line_part, line_type.pop()))
                else:
                    line_parts.append(StringReplacer(line_part, line_type[-1]))
                    line_type.append(StringReplacer.String)
                line_part = ''
                continue

            if line_part.endswith('//'):
                line_parts.append(StringReplacer(line_part[:-2], line_type[-1]))
                line_type.append(StringReplacer.Comment)
                line_part = orig_line[pos-1:]
                break

            if line_part.endswith('[') and is_normal_line_type(line_type):
                line_parts.append(StringReplacer(line_part[:-1], line_type[-1]))
                line_type.append(StringReplacer.Index)
                line_part = '['
                continue

            if line_part.endswith(']') and line_type[-1] == StringReplacer.Index:
                line_parts.append(StringReplacer(line_part, line_type.pop()))
                line_part = ''
                continue

            if line_part.endswith('::') and line_type[-1] == StringReplacer.InitializerList:
                line_part = line_parts.pop()
                line_part = line_part.text + '::'
                line_type.pop()
                continue

            if line_part.endswith(':') and is_normal_line_type(line_type):
                line_parts.append(StringReplacer(line_part[:-1], line_type[-1]))
                line_type.append(StringReplacer.InitializerList)
                line_part = ':'
                continue

            if line_part.endswith(';') and line_type[-1] == StringReplacer.InitializerList:
                line_type.pop()
                line_parts.append(StringReplacer(line_part, line_type[-1]))
                line_part = ''
                continue

            if line_part.endswith('{') and line_type[-1] == StringReplacer.InitializerList:
                line_parts.append(StringReplacer(line_part[:-1], line_type.pop()))
                line_part = '{'
                continue

        line_parts.append(StringReplacer(line_part, line_type[-1]))

    # Check that we popped all other line_types
    # assert line_type == [StringReplacer.Normal]

    line_parts = set_scopes(line_parts)

    text = ''
    for line_part in line_parts:
        if line_part.type not in [StringReplacer.Normal, StringReplacer.Index,
                                  StringReplacer.InitializerList]:
            text += str(line_part)
            continue

        # Put spaces around operators
        ops = ['=', '+', '/', '-', '<', '>', '%', '*', '&']
        for op in ops:
            line_part.replace(op, ' '+op+' ')
            line_part.replace('  '+op, ' '+op)
            line_part.replace(op+'  ', op+' ')

        # Remove spaces around ++ and --
        for op in ['-', '+']:
            line_part.replace(' '+op+' '+op+' ', op+op)

        # Remove spaces between things like // and ==
        for op2 in ['=', '<', '>', '/']:
            for op1 in ['=', '+', '-', '*', '/', '<', '>']:
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

        # Pointer dereference
        line_part.replace(' - >  ', '->')

        # Remove spaces around operators
        for op in ['->']:
            line_part.replace(' '+op, op)
            line_part.replace(op+' ', op)

        # Spaces after keywords
        for key in ['for', 'if']:
            line_part.replace(key+'(', key+' (')

        # Templates and includes should not have spaces
        line_part.repeated_regex_replace(' <\s*((?:[\w\.<>:\*& ])+?)\s*((?:> )*)>[ \t]*', '<\g<1>\g<2>> ')

        # Template members
        line_part.replace('> ::', '>::')

        # -1 should not have spaces
        line_part.regex_replace('([^\w\]\)]) - ', '\g<1>-')
        for op in ops:
            if op != '-':
                line_part.replace(op+'-', op+' -')

        line_part.handle_pointers('*')
        line_part.handle_pointers('&')

        # Put spaces after , and ;
        for op in [',', ';']:
            line_part.replace(op, op+' ')
            line_part.replace(op+'  ', op+' ')

        # Comments at the start of a line_part should stay there
        line_part.regex_replace('^ //', '//')

        line_part.handle_brackets()

        # Includes should have a space
        line_part.replace('include<', 'include <')

        text += str(line_part)

    return text.rstrip()

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

    text = reformat(lines)

    f = open(fname, 'w')
    f.write(text)
    f.close()

if __name__ == "__main__":
    main()
