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

from dsl_parser import exceptions
from dsl_parser import elements
from dsl_parser.framework.elements import (DictElement,
                                           Element,
                                           Leaf,
                                           Dict)


class SchemaPropertyDefault(Element):

    schema = Leaf(type=elements.PRIMITIVE_TYPES)


class SchemaPropertyDescription(Element):

    schema = Leaf(type=str)


class SchemaPropertyType(Element):

    schema = Leaf(type=str)

    def validate(self):
        if self.initial_value is None:
            return
        if self.initial_value not in ['string', 'integer', 'float',
                                      'boolean']:
            raise exceptions.DSLParsingFormatException(
                1,
                "Illegal property schema type '{0}'".format(
                    self.initial_value))


class SchemaProperty(Element):

    schema = {
        'default': SchemaPropertyDefault,
        'description': SchemaPropertyDescription,
        'type': SchemaPropertyType,
    }


class Schema(DictElement):

    schema = Dict(type=SchemaProperty)
