import pytest

from process_ciod_module_relationship import expand_conditional_statement


def test_expand_conditional_statement_normal_cases():
    assert expand_conditional_statement('C') == ('C', None)
    assert expand_conditional_statement('M') == ('M', None)
    assert expand_conditional_statement('U') == ('U', None)


def test_expand_conditional_statement_with_conditional_statement():
    assert expand_conditional_statement('C - Hello') == ('C', 'Hello')


def test_expand_conditional_statement_discards_comments_after_user_optional():
    assert expand_conditional_statement('U - Comment') == ('U', None)


def test_expand_conditional_statement_with_conditional_statement_containing_dashes():
    assert expand_conditional_statement('C - Has - Dashes') == ('C', 'Has - Dashes')


def test_expand_conditional_statement_raises_if_empty():
    with pytest.raises(Exception):
        expand_conditional_statement()
