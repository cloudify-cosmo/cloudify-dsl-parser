########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import copy

from dsl_parser import exceptions


class Unparsed(object):
    pass
UNPARSED = Unparsed()


class ElementType(object):

    def __init__(self, type):
        if isinstance(type, list):
            type = tuple(type)
        self.type = type


class Leaf(ElementType):
    pass


class Dict(ElementType):
    pass


class List(ElementType):
    pass


class Element(object):

    schema = None
    required = False
    requires = {}
    provides = []

    def __init__(self, context, initial_value, name=None):
        self.context = context
        self._initial_value = initial_value
        self._parsed_value = UNPARSED
        self._provided = None
        self.name = name

    def __str__(self):
        return '{0}(name={1}, initial_value={2}, value={3})'.format(
            self.__class__, self.name, self._initial_value,
            self._parsed_value)

    __repr__ = __str__

    def validate(self, **kwargs):
        pass

    def parse(self, **kwargs):
        return self.initial_value

    @property
    def index(self):
        """Alias name for list based elements"""
        return self.name

    @property
    def initial_value(self):
        return copy.deepcopy(self._initial_value)

    @property
    def value(self):
        if self._parsed_value == UNPARSED:
            raise exceptions.DSLParsingSchemaAPIException(
                exceptions.ERROR_CODE_ILLEGAL_VALUE_ACCESS,
                'Cannot access element value before parsing')
        return copy.deepcopy(self._parsed_value)

    @value.setter
    def value(self, val):
        self._parsed_value = val

    def calculate_provided(self, **kwargs):
        return {}

    @property
    def provided(self):
        return copy.deepcopy(self._provided)

    @provided.setter
    def provided(self, value):
        self._provided = value

    def _parent(self):
        return next(self.context.ancestors_iter(self))

    def ancestor(self, element_type):
        matches = [e for e in self.context.ancestors_iter(self)
                   if isinstance(e, element_type)]
        if not matches:
            raise exceptions.DSLParsingElementMatchException(
                'No matches found for {0}'.format(element_type))
        if len(matches) > 1:
            raise exceptions.DSLParsingElementMatchException(
                'Multiple matches found for {0}'.format(element_type))
        return matches[0]

    def descendants(self, element_type):
        return [e for e in self.context.descendants(self)
                if isinstance(e, element_type)]

    def child(self, element_type):
        matches = [e for e in self.context.child_elements_iter(self)
                   if isinstance(e, element_type)]
        if not matches:
            raise exceptions.DSLParsingElementMatchException(
                'No matches found for {0}'.format(element_type))
        if len(matches) > 1:
            raise exceptions.DSLParsingElementMatchException(
                'Multiple matches found for {0}'.format(element_type))
        return matches[0]

    def build_dict_result(self):
        return dict((child.name, child.value)
                    for child in self.context.child_elements_iter(self))

    def children(self):
        return list(self.context.child_elements_iter(self))

    def sibling(self, element_type):
        return self._parent().child(element_type)


class DictElement(Element):

    def parse(self, **kwargs):
        return self.build_dict_result()
