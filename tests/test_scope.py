import pytest
from reformat import Scope

def test_last():
    scope = Scope(1)
    scope = Scope(scope, '(')
    scope = Scope(scope, 'last')
    assert scope.last == 'last'
