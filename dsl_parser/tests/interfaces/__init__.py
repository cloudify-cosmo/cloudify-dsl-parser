########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

from dsl_parser.framework import parser
from dsl_parser.framework.elements import Element
from dsl_parser.elements import data_types, version


def validate(obj, element_cls):
    class TestElement(Element):
        schema = {
            'tosca_definitions_version': version.ToscaDefinitionsVersion,
            'test': element_cls,
            'data_types': data_types.DataTypes
        }
    obj = {
        'tosca_definitions_version': 'cloudify_dsl_1_1',
        'test': obj
    }
    parser.parse(obj,
                 element_cls=TestElement,
                 inputs={
                     'validate_version': True
                 },
                 strict=True)
