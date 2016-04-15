# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from types import NoneType
from collections import namedtuple

from .framework import Element
from .framework.functions import register, unregister, Function


_BaseFunctionExpansion = namedtuple(
    'PropertyFunctionExpansion', 'action, name, function')
_BaseElementExpansion = namedtuple(
    'ElementExpansion', 'action, target_element, new_element, schema_key')


class _ValidatorMixin(object):
    _ACTION_EXCEPTION_MESSAGE = 'action arg options: {actions}, got {action}'
    _ARGUMENT_TYPE_EXCEPTION_MESSAGE = (
        '{name} argument mast be {type} based, got {arg!r}')

    @classmethod
    def validate_actions(cls, action):
        if action not in cls.ACTIONS:
            raise TypeError(cls._ACTION_EXCEPTION_MESSAGE.format(
                actions=cls.ACTIONS, action=action))

    @classmethod
    def validate_type(cls, argument_name, argument, expected_type):
        if not issubclass(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXCEPTION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_instance(cls, argument_name, argument, expected_type):
        if not isinstance(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXCEPTION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))


class PropertyFunctionExpansion(_BaseFunctionExpansion, _ValidatorMixin):
    ADD_FUNCTION_ACTION = 'add'
    REMOVE_FUNCTION_ACTION = 'remove'
    ACTIONS = (ADD_FUNCTION_ACTION, REMOVE_FUNCTION_ACTION)

    def __new__(cls, action, name, function):
        cls.validate_actions(action)
        cls.validate_type('function', function, Function)
        cls.validate_instance('name', name, basestring)
        return super(PropertyFunctionExpansion, cls).__new__(
            cls, action, name, function)


class ElementExpansion(_BaseElementExpansion, _ValidatorMixin):
    REPLACE_ELEMENT_ACTION = 'replace'
    INSERT_ELEMENT_TO_SCHEMA_ACTION = 'schema'
    ACTIONS = (REPLACE_ELEMENT_ACTION, INSERT_ELEMENT_TO_SCHEMA_ACTION)

    def __new__(cls, action, target_element, new_element, schema_key=None):
        cls.validate_actions(action)
        cls.validate_type('target_element', target_element, Element)
        cls.validate_type('new_element', new_element, Element)
        cls.validate_instance('schema_key', schema_key, (NoneType, basestring))
        return super(ElementExpansion, cls).__new__(
            cls, action, target_element, new_element, schema_key)


class ParserExpander(object):
    def __init__(self):
        self._property_function_handlers = {
            PropertyFunctionExpansion.ADD_FUNCTION_ACTION:
                self._add_function,
            PropertyFunctionExpansion.REMOVE_FUNCTION_ACTION:
                self._remove_function,
        }
        self._element_handlers = {
            ElementExpansion.INSERT_ELEMENT_TO_SCHEMA_ACTION:
                self._add_to_schame,
            ElementExpansion.REPLACE_ELEMENT_ACTION:
                self._replace_element,
        }

    def expand_elements(self, *expansions):
        for expansion in expansions:
            self._element_handlers[expansion.action](expansion)

    def expand_property_functions(self, *expansions):
        for expansion in expansions:
            self._property_function_handlers[expansion.action](expansion)

    def _remove_function(self, expansion):
        unregister(name=expansion.name)

    def _add_function(self, expansion):
        register(expansion.function, name=expansion.name)

    def _add_to_schame(self, expansion):
        expansion.target_element.schema[
            expansion.schema_key] = expansion.new_element

    def _replace_element(self, expansion):
        element_name = expansion.target_element.__name__
        for module in sys.modules.itervalues():
            if not module or not module.__name__.startswith(__package__):
                continue
            obj = getattr(module, element_name, None)
            if obj and issubclass(obj, Element):
                setattr(module, element_name, expansion.new_element)
