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


_BaseFunctionExtension = namedtuple(
    'IntrinsicFunctionExtension', 'action, name, function')
_BaseElementExtension = namedtuple(
    'ElementExtension', 'action, target_element, new_element, schema_key')


class _ValidatorMixin(object):
    _ACTION_EXTENSION_MESSAGE = 'action arg options: {actions}, got {action}'
    _ARGUMENT_TYPE_EXTENSION_MESSAGE = (
        '{name} argument mast be {type} based, got {arg!r}')

    @classmethod
    def validate_actions(cls, action):
        if action not in cls.ACTIONS:
            raise TypeError(cls._ACTION_EXTENSION_MESSAGE.format(
                actions=cls.ACTIONS, action=action))

    @classmethod
    def validate_type(cls, argument_name, argument, expected_type):
        if not issubclass(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXTENSION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_instance(cls, argument_name, argument, expected_type):
        if not isinstance(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXTENSION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))


class IntrinsicFunctionExtension(_BaseFunctionExtension, _ValidatorMixin):
    # todo: maybe add replace action and check in add that we don't replace...
    ADD_FUNCTION_ACTION = 'add'
    REMOVE_FUNCTION_ACTION = 'remove'
    ACTIONS = (ADD_FUNCTION_ACTION, REMOVE_FUNCTION_ACTION)

    def __new__(cls, action, name, function):
        cls.validate_actions(action)
        cls.validate_type('function', function, Function)
        cls.validate_instance('name', name, basestring)
        return super(IntrinsicFunctionExtension, cls).__new__(
            cls, action, name, function)


class ElementExtension(_BaseElementExtension, _ValidatorMixin):
    # todo: maybe add replace action and check in add that we don't replace...
    REPLACE_ELEMENT_ACTION = 'replace'
    ADD_ELEMENT_TO_SCHEMA_ACTION = 'schema'
    ACTIONS = (REPLACE_ELEMENT_ACTION, ADD_ELEMENT_TO_SCHEMA_ACTION)

    def __new__(cls, action, target_element, new_element, schema_key=None):
        cls.validate_actions(action)
        cls.validate_type('target_element', target_element, Element)
        cls.validate_type('new_element', new_element, Element)
        cls.validate_instance('schema_key', schema_key, (NoneType, basestring))
        return super(ElementExtension, cls).__new__(
            cls, action, target_element, new_element, schema_key)


class ParserExtender(_ValidatorMixin):
    def __init__(self):
        self._intrinsic_function_handlers = {
            IntrinsicFunctionExtension.ADD_FUNCTION_ACTION:
                self._add_function,
            IntrinsicFunctionExtension.REMOVE_FUNCTION_ACTION:
                self._remove_function,
        }
        self._element_handlers = {
            ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION:
                self._add_to_schame,
            ElementExtension.REPLACE_ELEMENT_ACTION:
                self._replace_element,
        }

    def extend(self, **extension_lists):
        """

        :param element_extensions:
        :type element_extensions: (tuple, list)
        :param function_extensions:
        :type function_extensions: (tuple, list)
        """
        element_extensions = extension_lists.pop('element_extensions', ())
        function_extensions = extension_lists.pop('function_extensions', ())
        self.validate_instance(
            'element_expansions', element_extensions, (tuple, list))
        self.validate_instance(
            'function_expansions', function_extensions, (tuple, list))

        self.extend_elements(*element_extensions)
        self.extend_intrinsic_functions(*function_extensions)

    def extend_elements(self, *extensions):
        for extension in extensions:
            self.validate_instance(
                extension.__class__.__name__,
                extension,
                ElementExtension)
            self._run_handler(
                extension,
                handlers=self._element_handlers)

    def extend_intrinsic_functions(self, *extensions):
        for extension in extensions:
            self.validate_instance(
                extension.__class__.__name__,
                extension,
                IntrinsicFunctionExtension)
            self._run_handler(
                extension,
                handlers=self._intrinsic_function_handlers)

    def _run_handler(self, expansion, handlers):
        handlers[expansion.action](expansion)

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
            try:
                element = getattr(module, element_name)
                if all([issubclass(element, Element),
                        element is not expansion.new_element]):
                    setattr(module, element_name, expansion.new_element)
            except AttributeError:
                pass
