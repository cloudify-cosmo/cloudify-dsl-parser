#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from aria.parser.constants import SCRIPT_PLUGIN_NAME
from aria.parser.exceptions import (
    DSLParsingLogicException,
    DSLParsingException,
    ERROR_UNKNOWN_TYPE,
    ERROR_VALUE_DOES_NOT_MATCH_TYPE,
    ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
)
from aria.parser.dsl_supported_versions import parse_dsl_version
from tosca_parser import parse

from .suite import ParserTestCase, TempDirectoryTestCase


class TestParserLogicExceptions(ParserTestCase, TempDirectoryTestCase):
    def test_plugin_with_wrongful_executor_field(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += """
plugins:
    test_plugin:
        executor: "bad value"
        source: dummy

node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}

        """
        self.assert_parser_raise_exception(18, DSLParsingLogicException)

    def test_operation_with_wrongful_executor_field(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += """
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy

node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    executor: wrong_executor
                    implementation: test_plugin.install
                    inputs: {}

        """
        self.assert_parser_raise_exception(28, DSLParsingLogicException)

    def test_validate_agent_plugin_on_non_host_node(self):
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: test_type
node_types:
    test_type:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
plugins:
    test_plugin:
        executor: host_agent
        source: dummy
        """
        self.assert_parser_raise_exception(24, DSLParsingLogicException)

    def test_instance_relationship_more_than_one_contained_in(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            - type: cloudify.relationships.contained_in
              target: test_node
            - type: derived_from_contained_in
              target: test_node
relationships:
    cloudify.relationships.contained_in: {}
    derived_from_contained_in:
        derived_from: cloudify.relationships.contained_in
"""
        ex = self.assert_parser_raise_exception(112, DSLParsingLogicException)
        self.assertEqual(
            set(['cloudify.relationships.contained_in',
                 'derived_from_contained_in']),
            set(ex.relationship_types))

    def test_group_missing_policy_type(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_types:
    policy_type:
        properties:
            metric:
                default: 100
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: non_existent_policy_type
                properties: {}
"""
        self.assert_parser_raise_exception(41, DSLParsingLogicException)

    def test_group_missing_trigger_type(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_types:
    policy_type:
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                triggers:
                    trigger1:
                        type: non_existent_trigger
"""
        self.assert_parser_raise_exception(42, DSLParsingLogicException)

    def test_group_policy_type_undefined_property(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_types:
    policy_type:
        properties: {}
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                properties:
                    key: value
"""
        self.assert_parser_raise_exception(106, DSLParsingLogicException)

    def test_group_policy_type_missing_property(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_types:
    policy_type:
        properties:
            key:
                description: a key
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                properties: {}
"""
        self.assert_parser_raise_exception(107, DSLParsingLogicException)

    def test_group_policy_trigger_undefined_parameter(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_triggers:
    trigger:
        source: source
policy_types:
    policy_type:
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                triggers:
                    trigger1:
                        type: trigger
                        parameters:
                            some: undefined
"""
        self.assert_parser_raise_exception(106, DSLParsingLogicException)

    def test_group_policy_trigger_missing_parameter(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
policy_triggers:
    trigger:
        source: source
        parameters:
            param1:
                description: the description
policy_types:
    policy_type:
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                triggers:
                    trigger1:
                        type: trigger
"""
        self.assert_parser_raise_exception(107, DSLParsingLogicException)

    def test_plugin_with_install_args_wrong_dsl_version(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += self.template.PLUGIN_WITH_INSTALL_ARGS
        self.template += self.template.BASIC_TYPE
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH, DSLParsingException)

    def test_max_retries_version_validation(self):
        self.template.version_section('1.1')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
        interfaces:
            my_interface:
                my_operation:
                    max_retries: 1
"""
        self.parse()
        self.template.clear()
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
        interfaces:
            my_interface:
                my_operation:
                    max_retries: 1
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)

    def test_retry_interval_version_validation(self):
        self.template.version_section('1.1')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
        interfaces:
            my_interface:
                my_operation:
                    retry_interval: 1
"""
        self.parse()
        self.template.clear()
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
        interfaces:
            my_interface:
                my_operation:
                    retry_interval: 1
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)

    def test_dsl_definitions_version_validation(self):
        self.template.version_section('1.2')
        self.template += """
dsl_definitions:
    def: &def
        key: value
node_types:
    type:
        properties:
            prop:
                default: 1
node_templates:
    node:
        type: type
"""
        self.parse()
        self.template.clear()
        self.template.version_section('1.1')
        self.template += """
dsl_definitions:
    def: &def
        key: value
node_types:
    type:
        properties:
            prop:
                default: 1
node_templates:
    node:
        type: type
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)
        self.template.clear()
        self.template.version_section('1.0')
        self.template += """
dsl_definitions:
    def: &def
        key: value
node_types:
    type:
        properties:
            prop:
                default: 1
node_templates:
    node:
        type: type
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)

    def test_blueprint_description_version_validation(self):
        self.template.version_section('1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
description: sample description
        """
        self.parse()
        self.template.clear()
        self.template.version_section('1.1')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
description: sample description
        """
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)
        self.template.clear()
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
description: sample description
        """
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)

    def test_required_property_version_validation(self):
        self.template.version_section('1.2')
        self.template += """
node_types:
  type:
    properties:
      property:
        required: false
node_templates:
  node:
    type: type
"""
        self.parse()
        self.template.clear()
        self.template.version_section('1.1')
        self.template += """
node_types:
  type:
    properties:
      property:
        required: false
node_templates:
  node:
    type: type
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)
        self.template.clear()
        self.template.version_section('1.0')
        self.template += """
node_types:
  type:
    properties:
      property:
        required: false
node_templates:
  node:
    type: type
"""
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
            DSLParsingLogicException)

    def test_plugin_fields_version_validation(self):
        base_yaml = """
node_types:
  type:
    properties:
      prop:
        default: value
node_templates:
  node:
    type: type
plugins:
  plugin:
    install: false
    executor: central_deployment_agent
    {0}: {1}
"""

        def test_field(key, value):
            self.template.clear()
            self.template.version_section('1.2')
            self.template += base_yaml.format(key, value)
            self.parse()
            self.template.clear()
            self.template.version_section('1.1')
            self.template += base_yaml.format(key, value)
            self.assert_parser_raise_exception(
                ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                DSLParsingLogicException)
            self.template.clear()
            self.template.version_section('1.0')
            self.template += base_yaml.format(key, value)
            self.assert_parser_raise_exception(
                ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                DSLParsingLogicException)
        fields = {
            'package_name': 'name',
            'package_version': 'version',
            'supported_platform': 'any',
            'distribution': 'dist',
            'distribution_version': 'version',
            'distribution_release': 'release'
        }
        for key, value in fields.items():
            test_field(key, value)
