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
