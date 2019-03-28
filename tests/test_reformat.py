import pytest
import reformat

def test_plus_operator():
    out = reformat.reformat('a+b')
    assert out == 'a + b'

def test_unary_plus_operator():
    out = reformat.reformat('(+a-b)')
    assert out == '(+a - b)'
    out = reformat.reformat('(a- +b)')
    assert out == '(a - +b)'
    out = reformat.reformat('return +1;')
    assert out == 'return +1;'

def test_minus_operator():
    out = reformat.reformat('a-b')
    assert out == 'a - b'
    out = reformat.reformat('a-     b')
    assert out == 'a - b'

def test_unary_minus_operator():
    out = reformat.reformat('(-a-b)')
    assert out == '(-a - b)'
    out = reformat.reformat('(a+ -b)')
    assert out == '(a + -b)'
    out = reformat.reformat('return -1;')
    assert out == 'return -1;'

def test_two_char_operator():
    out = reformat.reformat('a==b')
    assert out == 'a == b'
    out = reformat.reformat('a!=b')
    assert out == 'a != b'
    out = reformat.reformat('a<=b')
    assert out == 'a <= b'
    out = reformat.reformat('a>=b')
    assert out == 'a >= b'
    out = reformat.reformat('a&=b')
    assert out == 'a &= b'
    out = reformat.reformat('a^=b')
    assert out == 'a ^= b'
    out = reformat.reformat('a|=b')
    assert out == 'a |= b'
    out = reformat.reformat('a*=b')
    assert out == 'a *= b'
    out = reformat.reformat('a+=b')
    assert out == 'a += b'
    out = reformat.reformat('a-=b')
    assert out == 'a -= b'
    out = reformat.reformat('a%=b')
    assert out == 'a %= b'

def test_three_char_operator():
    out = reformat.reformat('a<<=b')
    assert out == 'a <<= b'
    out = reformat.reformat('a>>=b')
    assert out == 'a >>= b'

def test_increment_operator():
    out = reformat.reformat('a++ - b')
    assert out == 'a++ - b'
    out = reformat.reformat('a++-b')
    assert out == 'a++ - b'
    out = reformat.reformat('a++*b')
    assert out == 'a++ * b'

def test_bitshift_operator():
    out = reformat.reformat('a>>b')
    assert out == 'a >> b'
    out = reformat.reformat('a<<b')
    assert out == 'a << b'
    code = '''std::cout << "test" <<
    "test 2" << "test 3" <<
    "test 4" << std::endl;'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''std::cout << "test"
          << f("test 2") << "test 3"
          << "test 4" << std::endl;'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''std::cout<<"test"
<<f("test 2")<<"test 3";
out2<<"test"
<<f("test 2")<<"test 3";'''
    code2 = '''std::cout << "test"
          << f("test 2") << "test 3";
out2 << "test"
     << f("test 2") << "test 3";'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code2
    code = '''
std::cout << std::endl << "test" << std::endl;
std::cout << "test" << "test"
          << "test" << "test"
          << std::endl;'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_less_than_operator():
    out = reformat.reformat('a<b')
    assert out == 'a < b'

def test_greater_than_operator():
    out = reformat.reformat('a>b')
    assert out == 'a > b'

def test_template_arguments():
    out = reformat.reformat('a<b> = c')
    assert out == 'a<b> = c'
    out = reformat.reformat('a<b *> = c')
    assert out == 'a<b *> = c'
    out = reformat.reformat('a<b &> = c')
    assert out == 'a<b &> = c'
    out = reformat.reformat('a = dynamic_cast<const b &>(c);')
    assert out == 'a = dynamic_cast<const b &>(c);'
    out = reformat.reformat('a<const b> = c')
    assert out == 'a<const b> = c'

def test_nested_template_arguments():
    out = reformat.reformat('a<b<c> > = d')
    assert out == 'a<b<c> > = d'
    out = reformat.reformat('a<b<c> > = d', set_indent=True)
    assert out == 'a<b<c> > = d'
    out = reformat.reformat('a<b<c> > d')
    assert out == 'a<b<c> > d'
    out = reformat.reformat('a<b<c> > d', set_indent=True)
    assert out == 'a<b<c> > d'

def test_template_members():
    out = reformat.reformat('a<b>::c')
    assert out == 'a<b>::c'

def test_includes():
    out = reformat.reformat('#include <iostream>')
    assert out == '#include <iostream>'
    out = reformat.reformat('#include <iostream> \n#include <string>')
    assert out == '#include <iostream>\n#include <string>'

def test_multiplication_operator():
    out = reformat.reformat('a = b * c;', 1)
    assert out == 'a = b * c;'
    out = reformat.reformat('f(a * b);', 1)
    assert out == 'f(a * b);'
    out = reformat.reformat('std::cout<<a*b;')
    assert out == 'std::cout << a * b;'
    out = reformat.reformat('std::cout<<*a;')
    assert out == 'std::cout << *a;'
    out = reformat.reformat('if (a*b)', 1)
    assert out == 'if (a * b)'
    out = reformat.reformat('f((a*b)*c)', 1)
    assert out == 'f((a * b) * c)'
    out = reformat.reformat('f("a", b*c)', 1)
    assert out == 'f("a", b * c)'
    out = reformat.reformat('''f("a",
  b*c)''', 1)
    assert out == '''f("a",
  b * c)'''

def test_and_operator():
    out = reformat.reformat('a = b & c;', 1)
    assert out == 'a = b & c;'
    out = reformat.reformat('f(a & b);', 1)
    assert out == 'f(a & b);'
    out = reformat.reformat('std::cout<<a&b;')
    assert out == 'std::cout << a & b;'
    out = reformat.reformat('if (a&b)', 1)
    assert out == 'if (a & b)'
    out = reformat.reformat('if (a&&b)', 1)
    assert out == 'if (a && b)'
    out = reformat.reformat('if ((a)&&(b))', 1)
    assert out == 'if ((a) && (b))'

def test_or_operator():
    out = reformat.reformat('a = b | c;', 1)
    assert out == 'a = b | c;'
    out = reformat.reformat('f(a | b);', 1)
    assert out == 'f(a | b);'
    out = reformat.reformat('std::cout<<a|b;')
    assert out == 'std::cout << a | b;'
    out = reformat.reformat('if (a|b)', 1)
    assert out == 'if (a | b)'
    out = reformat.reformat('if (a||b)', 1)
    assert out == 'if (a || b)'
    out = reformat.reformat('if ((a)||(b))', 1)
    assert out == 'if ((a) || (b))'

def test_ternary_operator():
    out = reformat.reformat('a?b:c;')
    assert out == 'a ? b : c;'
    out = reformat.reformat('a=1?2:3;')
    assert out == 'a = 1 ? 2 : 3;'
    out = reformat.reformat('a=1 ? 2 : 3;')
    assert out == 'a = 1 ? 2 : 3;'
    out = reformat.reformat('a ? "a" : "b"')
    assert out == 'a ? "a" : "b"'

def test_pointers():
    out = reformat.reformat('(a*)')
    assert out == '(a *)'
    out = reformat.reformat('static_cast<a*>(b)')
    assert out == 'static_cast<a *>(b)'
    out = reformat.reformat('void f(int *c)')
    assert out == 'void f(int *c)'
    out = reformat.reformat('A *f(int *c)')
    assert out == 'A *f(int *c)'
    out = reformat.reformat('int *a = new int[b];')
    assert out == 'int *a = new int[b];'
    out = reformat.reformat('int *a;')
    assert out == 'int *a;'
    out = reformat.reformat('f(* a)')
    assert out == 'f(*a)'
    out = reformat.reformat('f(* (a) )')
    assert out == 'f(*(a))'
    out = reformat.reformat('f(*a,*b)')
    assert out == 'f(*a, *b)'
    out = reformat.reformat('A *f(int *a, int *b)')
    assert out == 'A *f(int *a, int *b)'
    code = '''
    f(*a,
      *b);'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code

def test_pointer_dereference():
    out = reformat.reformat('a->get();')
    assert out == 'a->get();'
    out = reformat.reformat('(*a)->get();')
    assert out == '(*a)->get();'

def test_references():
    out = reformat.reformat('void f(int &c)')
    assert out == 'void f(int &c)'
    out = reformat.reformat('A &f(int &c)')
    assert out == 'A &f(int &c)'
    out = reformat.reformat('int &a = f[b];')
    assert out == 'int &a = f[b];'
    out = reformat.reformat('f(&a,&b)', 1)
    assert out == 'f(&a, &b)'
    out = reformat.reformat('f(& a)', 1)
    assert out == 'f(&a)'
    out = reformat.reformat('f(& (a) )', 1)
    assert out == 'f(&(a))'
    out = reformat.reformat('A &f(int &a, int &b)')
    assert out == 'A &f(int &a, int &b)'
    out = reformat.reformat('''A &f(int &a,
     int &b)''')
    assert out == '''A &f(int &a,
     int &b)'''

def test_classes():
    out = reformat.reformat('class A { int *f(int *a);};')
    assert out == 'class A {int *f(int *a); };'
    out = reformat.reformat('class A; void f(a*b);')
    assert out == 'class A; void f(a *b);'
    out = reformat.reformat('class A; {f(a*b);}')
    assert out == 'class A; {f(a * b); }'
    code = '''class A
{
public:
    A();
}'''
    out = reformat.reformat(code)
    assert out == code
    code = '''namespace N {
class A
{
public:
    A f(int const &a, int const &b);
};

}'''
    out = reformat.reformat(code)
    assert out == code
    code = '''class A
{
public:
    A f(int const &a, int const &b);
    B f(int const &a, int const &b);
};'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_inheritance():
    code = '''class A : public B,
    public C,
    public D
{
public:
    A f(int const &a, int const &b);
};'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_exponent():
    out = reformat.reformat('1e-5')
    assert out == '1e-5'
    out = reformat.reformat('1.0e-5')
    assert out == '1.0e-5'
    out = reformat.reformat('3.5e+5')
    assert out == '3.5e+5'

def test_if_statement():
    out = reformat.reformat('if (a != b) c;')
    assert out == 'if (a != b) c;'
    out = reformat.reformat('if (a) * b = c;', 1)
    assert out == 'if (a) *b = c;'
    out = reformat.reformat('if (a < 0 || b > 0) *b = c;', 1)
    assert out == 'if (a < 0 || b > 0) *b = c;'

def test_for_statement():
    out = reformat.reformat('for(int i=0;i<c;++i) a;')
    assert out == 'for (int i = 0; i < c; ++i) a;'
    out = reformat.reformat('for(int i=0;i<c;++i)')
    assert out == 'for (int i = 0; i < c; ++i)'
    out = reformat.reformat('for ( int i = 0 ; i < c ; ++i ) ')
    assert out == 'for (int i = 0; i < c; ++i)'
    out = reformat.reformat('for ( int i = 0 ; i < a->c ; ++i ) ')
    assert out == 'for (int i = 0; i < a->c; ++i)'
    code = '''for (int i = 0; i < c; ++i)
{
    f();
}
a = g();'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''for (int i = 0; i < c; ++i)
    f();
a = g();'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''for (int i = 0; i < c; ++i) f();
a = g();'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True, extra_newlines=True)
    assert out == code

def test_nested_for():
    code = '''for (int i = 0; i < c; ++i)
    for (int j = 0; j < c; ++j)
    {
        f();
    }
a = g();'''
    out = reformat.reformat(code, set_indent=True)
    code = '''for (int i = 0; i < c; ++i)
{
    for (int j = 0; j < c; ++j)
    {
        f();
    }
}
a = g();'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''for (int i = 0; i < c; ++i)
    for (int j = 0; j < c; ++j)
        f();
a = g();'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''for (int i = 0; i < c; ++i)
    if (b < c)
        f();
a = g();'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''for (int i = 0; i < c; ++i)
    for (int j = 0; j < c; ++j)
    {
        f();
    }
a = g();'''
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_return_statement():
    out = reformat.reformat('return a;')
    assert out == 'return a;'
    out = reformat.reformat('return(a);')
    assert out == 'return (a);'
    out = reformat.reformat('int f() { return 1; }',
                            set_indent=True, extra_newlines=True)
    assert out == '''int f()
{
    return 1;
}'''

def test_index():
    out = reformat.reformat('a[i+1];')
    assert out == 'a[i+1];'
    out = reformat.reformat('a[b->idx];')
    assert out == 'a[b->idx];'
    out = reformat.reformat('a[idx(b)];')
    assert out == 'a[idx(b)];'
    out = reformat.reformat('a[idx--];')
    assert out == 'a[idx--];'
    out = reformat.reformat('a[idx++];')
    assert out == 'a[idx++];'
    out = reformat.reformat('a[--idx];')
    assert out == 'a[--idx];'
    out = reformat.reformat('a[++idx];')
    assert out == 'a[++idx];'

def test_namespace():
    code = '''namespace A {

void f(int *a)
{
    g(a * b);
}

}'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    code = '''namespace A
    {
    class B;
    }'''
    out = reformat.reformat(code)
    assert out == code
    expected = '''namespace A
{
class B;
}'''
    out = reformat.reformat(code, set_indent=True)
    assert out == expected

def test_brackets():
    out = reformat.reformat('( a )')
    assert out == '(a)'
    out = reformat.reformat('(   a )')
    assert out == '(a)'
    out = reformat.reformat('(   "a" )')
    assert out == '("a")'

def test_comments():
    code = '''// aaa
a &f(b);'''
    out = reformat.reformat(code)
    assert out == code
    code = '    // aaa:'
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code
    code = 'a; // comment'
    out = reformat.reformat(code, extra_newlines=True)
    assert out == code

def test_initializer_lists():
    code = '''A::A(int &a, int &b)
:
    a_(a * b)
{}'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code

    code = '''A::A(int &a, int &b)
:
    a_(a * b),
    b_(a * b)
{
    f(a);
}'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_multiline_comments():
    code = '''/*
   s*v)23a87+v"asd{"
*/'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code

def test_pragma():
    code = '#pragma omp for schedule(static) reduction(+:a)'
    out = reformat.reformat(code)
    assert out == code

def test_define():
    out = reformat.reformat('    #ifdef DEBUG', 1, set_indent=True)
    assert out == '#ifdef DEBUG'

def test_bracket_alignment():
    code = '''
    f(a,
      b,
      c)'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    code2 = '''
    f(a,
  b,
  c)'''
    out = reformat.reformat(code2, 1)
    assert out == code2
    out = reformat.reformat(code2, 1, set_indent=True)
    assert out == code
    code = '''
    f(
        a,
        b,
        c)'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code
    code = '''
    f(
        A<B> a,
        A<B> b,
        A<B> c)'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code
    code = '''
    f(a, g(b,
           c)
      d);'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code
    code = '''
    f(a, g(b,
           c)
      d);
    f2(a, g(b,
            c)
       d);'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code
    code = '''
    freallylongname(
        freallylongname(
            Atype
                reallylongconstructorname(
                    a)));'''
    out = reformat.reformat(code, 1)
    assert out == code
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == code

def test_curly_bracket_alignment():
    code = '''
    if (a)
    {
        if (a < b < c)c;
        }

        if (e)
        {
            e;
        }'''

    expected = '''
    if (a)
    {
        if (a < b < c) c;
    }

    if (e)
    {
        e;
    }'''
    out = reformat.reformat(code, 1)
    assert out == code.replace(')c', ') c')
    out = reformat.reformat(code, 1, set_indent=True)
    assert out == expected

def test_default_values():
    code = '''f(int a = 2,
  int *b = NULL);'''
    out = reformat.reformat(code)
    assert out == code
    out = reformat.reformat(code, set_indent=True)
    assert out == code

def test_extra_newlines():
    code = '''a f(a b, c d) {b; d;}'''
    out = reformat.reformat(code, set_indent=True,
                            extra_newlines=True)
    expected = '''a f(a b, c d)
{
    b;
    d;
}'''
    assert out == expected

@pytest.mark.xfail
def test_pointers_that_are_not_pointers():
    '''This is something that also doesn't work in astyle'''
    code = '''int a = 1;
int b = 2;
int c(a * b);'''
    out = reformat.reformat(code)
    assert out == code
