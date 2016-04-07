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

from .version import ToscaDefinitionsVersion
from .data_types import Schema
from . import PRIMITIVE_TYPES, Element, Leaf, DictElement, Dict


class OutputDescription(Element):
    schema = Leaf(type=str)


class OutputValue(Element):
    required = True
    schema = Leaf(type=PRIMITIVE_TYPES)


class Output(Element):
    schema = {
        'description': OutputDescription,
        'value': OutputValue,
    }


class Outputs(DictElement):
    schema = Dict(type=Output)


class Inputs(Schema):
    pass


class DSLDefinitions(Element):
    schema = Leaf(type=[dict, list])
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }

    def validate(self, version, validate_version):
        if validate_version:
            self.validate_version(version, (1, 2))


class Description(Element):
    schema = Leaf(type=str)
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }

    def validate(self, version, validate_version):
        if validate_version:
            self.validate_version(version, (1, 2))
