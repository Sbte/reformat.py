import pytest
import reformat

def test_plus_operator():
    out = reformat.reformat('a+b')
    assert out == 'a + b'

def test_minus_operator():
    out = reformat.reformat('a-b')
    assert out == 'a - b'

def test_unary_minus_operator():
    out = reformat.reformat('(-a-b)')
    assert out == '(-a - b)'

def test_equality_operator():
    out = reformat.reformat('a==b')
    assert out == 'a == b'

def test_inequality_operator():
    out = reformat.reformat('a!=b')
    assert out == 'a != b'

def test_increment_operator():
    out = reformat.reformat('a++ - b')
    assert out == 'a++ - b'

def test_bitshift_operator():
    out = reformat.reformat('a>>b')
    assert out == 'a >> b'

    out = reformat.reformat('a<<b')
    assert out == 'a << b'

def test_less_than_operator():
    out = reformat.reformat('a<b')
    assert out == 'a < b'

def test_less_equal_operator():
    out = reformat.reformat('a<=b')
    assert out == 'a <= b'

def test_greater_than_operator():
    out = reformat.reformat('a>b')
    assert out == 'a > b'

def test_greater_equal_operator():
    out = reformat.reformat('a>=b')
    assert out == 'a >= b'

def test_template_arguments():
    out = reformat.reformat('a<b> = c')
    assert out == 'a<b> = c'
    out = reformat.reformat('a<b *> = c')
    assert out == 'a<b *> = c'
    out = reformat.reformat('a<b &> = c')
    assert out == 'a<b &> = c'
    out = reformat.reformat('a<const b> = c')
    assert out == 'a<const b> = c'

def test_nested_template_arguments():
    out = reformat.reformat('a<b<c> > = d')
    assert out == 'a<b<c> > = d'

def test_template_members():
    out = reformat.reformat('a<b>::c')
    assert out == 'a<b>::c'

def test_includes():
    out = reformat.reformat('#include <iostream>')
    assert out == '#include <iostream>'

def test_multiplication_operator():
    out = reformat.reformat('a*b')
    assert out == 'a * b'

def test_pointers():
    out = reformat.reformat('(a*)')
    assert out == '(a *)'
    out = reformat.reformat('static_cast<a*>(b)')
    assert out == 'static_cast<a *>(b)'
    out = reformat.reformat('void f(int *c)')
    #~ assert out == 'void f(int *c)'
    out = reformat.reformat('A *f(int *c)')
    #~ assert out == 'A *f(int *c)'
    out = reformat.reformat('int *a = new int[b];')
    #~ assert out == 'int *a = new int[b];'
