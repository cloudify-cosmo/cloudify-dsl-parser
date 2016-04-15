"""
  Aria.parser Expantion Demo
"""
from __future__ import print_function

import sys
from functools import wraps, partial

from tosca_parser.framework.elements.blueprint import Blueprint
from tosca_parser.framework.functions import template_functions
from tosca_parser.expansion_tools import (
    Element, ElementExpansion,
    Function, PropertyFunctionExpansion,
)
from tosca_parser import parse, expand


def main_demo():
    print('create a new Debug Blueprint Element,')
    print('This is a Blueprint Element with a debug print on every func call')
    TestBlueprint = print_class_methods_args(
        Blueprint, prefix='Aria.parser Expansion Demo:\n')
    print('TestBlueprint: {0!r}'.format(TestBlueprint))

    print('creating a ElementExpansion object')
    print('In this ElementExpansion:')
    print('    action: replace element')
    print('    target_element: element to action on')
    print('    new_element: element to action with')
    element_expantion = ElementExpansion(
        action=ElementExpansion.REPLACE_ELEMENT_ACTION,
        target_element=Blueprint,
        new_element=TestBlueprint)
    print('element_expantion: {0!r}'.format(element_expantion))

    print('creating a PropertyFunctionExpansion object')
    print('In this PropertyFunctionExpansion:')
    print('    action: add function')
    print('    name: function name')
    print('    function: Function class to action with')
    function_expantion = PropertyFunctionExpansion(
        action=PropertyFunctionExpansion.ADD_FUNCTION_ACTION,
        name='test_func',
        function=type('TestFunction', (Function,), {}),
    )
    print('function_expantion: {0!r}'.format(function_expantion))

    print('Expanding the aria.parser "Language"')
    expand(element_expantions=[element_expantion],
           function_expantions=[function_expantion])

    print('Check function expanded, result:'.format(
        bool(template_functions.get('test_func'))))

    tosca_template = ('/home/liorm/work/workspace/bootstrap/'
                      'cloudify-manager-blueprints/'
                      'openstack-manager-blueprint.yaml')
    print('Check element replacement expanding:')
    print('    for this test lets run the parser')
    print('tosca-template: {0}'.format(tosca_template))
    parse(tosca_template)
    print('Success!...')


def print_func_args(func=None, prefix='DEBUG:'):
    """
    Decorator to print function call details - parameters names and effective values
    !!!Do not use on production ONLY for debug!!!
    :param func: decorated function to analyze
    :param prefix: prifix for the debug prints
    :return: print_func_args wrapper
    """
    if func is None:
        return partial(print_func_args, prefix=prefix)

    @wraps(func)
    def wrapper(*func_args, **func_kwargs):
        arg_names = func.func_code.co_varnames[:func.func_code.co_argcount]
        args = func_args[:len(arg_names)]
        defaults = func.func_defaults or ()
        start = len(defaults) - (func.func_code.co_argcount - len(args))
        args += defaults[start:]
        params = zip(arg_names, args)
        args = func_args[len(arg_names):]
        if args:
            params.append(('args', args))
        if func_kwargs:
            params.append(('kwargs', func_kwargs))
        try:
            func_path = func.__qualname__
        except AttributeError:
            func_path = func.__module__ + '.' + func.__name__
        print('%s %s(%s)' % (prefix, func_path, ', '.join('%s = %r' % p for p in params)))
        return func(*func_args, **func_kwargs)
    return wrapper


def print_class_methods_args(cls=None, prefix='DEBUG:'):
    """
    Decorate every class method with print_func_args decorator
    (won't work with classmethods and staticmethods)
    !!!Do not use on production ONLY for debug!!!
    :param cls: class to decorate
    :param prefix: prifix for the debug prints
    :return: Decorated class
    """
    if cls is None:
        return partial(print_class_methods_args, prefix=prefix)

    for name, method in vars(cls).iteritems():
        if callable(method):
            setattr(cls, name, print_func_args(method, prefix))
    cls.__init__ = print_func_args(cls.__init__, prefix)
    return cls

if __name__ == '__main__':
    sys.exit(main_demo())
