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

from .requirements import Requirement, Value, sibling_predicate
from .parser import parse
from .elements.blueprint import (
    BlueprintVersionExtractor, BlueprintImporter, Blueprint)
from .elements import (
    Unparsed, UNPARSED,
    Leaf, Dict, List,
    Element, ElementType, DictElement, UnknownElement,
    UnknownSchema,
)


def validate_version_schema(
        parsed_dsl_holder,
        validate_version):
    result = parse(
        parsed_dsl_holder,
        element_cls=BlueprintVersionExtractor,
        inputs={
            'validate_version': validate_version,
        },
        strict=False)
    return result['plan_version']


def handle_imports(
        parsed_dsl_holder,
        resources_base_url,
        version,
        resolver,
        validate_version):
    result = parse(
        value=parsed_dsl_holder,
        inputs={
            'main_blueprint_holder': parsed_dsl_holder,
            'resources_base_url': resources_base_url,
            'blueprint_location': parsed_dsl_holder.filename,
            'version': version,
            'resolver': resolver,
            'validate_version': validate_version,
        },
        element_cls=BlueprintImporter,
        strict=False)
    return result['resource_base'], result['merged_blueprint']


def parse_blueprint(
        blueprint_holder,
        resource_base,
        validate_version):
    return parse(
        value=blueprint_holder,
        inputs={
            'resource_base': resource_base,
            'validate_version': validate_version,
        },
        element_cls=Blueprint)
