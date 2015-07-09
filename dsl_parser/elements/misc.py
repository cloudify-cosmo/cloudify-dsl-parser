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

from dsl_parser import (version as _version,
                        exceptions,
                        models)
from dsl_parser import elements
from dsl_parser.elements import properties
from dsl_parser.framework.elements import (DictElement,
                                           Element,
                                           Leaf,
                                           Dict)
from dsl_parser.framework.requirements import Value


class ToscaDefinitionsVersion(Element):

    schema = Leaf(type=str)
    provides = ['version']

    def validate(self):
        if self.initial_value is None:
            raise exceptions.DSLParsingLogicException(
                27, '{0} field must appear in the main blueprint file'.format(
                    _version.VERSION))

        _version.validate_dsl_version(self.initial_value)

    def parse(self):
        return models.Version(_version.process_dsl_version(self.initial_value))

    def calculate_provided(self):
        return {
            'version': _version.parse_dsl_version(self.initial_value)
        }


class OutputDescription(Element):

    schema = Leaf(type=str)


class OutputValue(Element):

    required = True
    schema = Leaf(type=elements.PRIMITIVE_TYPES)


class Output(Element):

    schema = {
        'description': OutputDescription,
        'value': OutputValue
    }


class Outputs(DictElement):

    schema = Dict(type=Output)


class Inputs(properties.Schema):
    pass


class DSLDefinitions(Element):

    schema = Leaf(type=[dict, list])
    requires = {
        ToscaDefinitionsVersion: [Value('version')]
    }

    def validate(self, version):
        value = self.initial_value
        if value is None:
            return
        if version.definitions_version < (1, 2):
            raise exceptions.DSLParsingLogicException(
                exceptions.ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                "'{0} is not supported for {1} earlier than "
                "'{2}'. You are currently using version '{3}'".format(
                    self.name,
                    _version.VERSION,
                    _version.DSL_VERSION_1_2,
                    version.raw))
