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


DSL_VERSION_1_0 = 'cloudify_dsl_1_0'


class TestParserLogicExceptions(ParserTestCase, TempDirectoryTestCase):

    def test_parse_dsl_from_file_bad_path(self):
        self.assertRaises(EnvironmentError, parse, 'fake-file.yaml')

    def test_no_type_definition(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.assert_parser_raise_exception(7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                    implementation: missing_plugin.install
                    inputs: {}
                terminate:
                    implementation: missing_plugin.terminate
                    inputs: {}
        properties:
            install_agent:
                default: 'false'
            key: {}
"""
        self.assert_parser_raise_exception(10, DSLParsingLogicException)

    def test_type_derive_non_from_none_existing(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += """
node_types:
    test_type:
        derived_from: "non_existing_type_parent"
        """
        self.assert_parser_raise_exception(
            ERROR_UNKNOWN_TYPE, DSLParsingLogicException)

    def test_import_bad_path(self):
        self.template.version_section('1.0')
        self.template += """
imports:
    -   fake-file.yaml
        """
        self.assert_parser_raise_exception(13, DSLParsingLogicException)

    def test_cyclic_dependency(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += """
node_types:
    test_type:
        derived_from: "test_type_parent"

    test_type_parent:
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        derived_from: "test_type"
    """
        ex = self.assert_parser_raise_exception(100, DSLParsingLogicException)
        circular = ex.circular_dependency
        self.assertEqual(len(circular), 4)
        self.assertEqual(circular[0], circular[-1])

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

    def test_top_level_relationships_relationship_with_undefined_plugin(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
relationships:
    test_relationship:
        source_interfaces:
            some_interface:
                op:
                    implementation: no_plugin.op
                    inputs: {}
                        """
        self.assert_parser_raise_exception(19, DSLParsingLogicException)

    def test_workflow_mapping_no_plugin(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += self.template.BASIC_TYPE
        self.template += """
workflows:
    workflow1: test_plugin2.workflow1
"""
        self.assert_parser_raise_exception(21, DSLParsingLogicException)

    def test_top_level_relationships_import_same_name_relationship(self):
        self.template.node_type_section()
        self.template.plugin_section()
        self.template += """
relationships:
    test_relationship: {}
            """
        yaml = self.create_yaml_with_imports([str(self.template)]) + """
relationships:
    test_relationship: {}
            """
        self.template.version_section('1.0')
        self.template += yaml
        self.assert_parser_raise_exception(4, DSLParsingLogicException)

    def test_top_level_relationships_circular_inheritance(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
relationships:
    test_relationship1:
        derived_from: test_relationship2
    test_relationship2:
        derived_from: test_relationship3
    test_relationship3:
        derived_from: test_relationship1
        """
        self.assert_parser_raise_exception(100, DSLParsingLogicException)

    def test_instance_relationships_bad_target_value(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: fake_node
relationships:
    test_relationship: {}
            """
        self.assert_parser_raise_exception(25, DSLParsingLogicException)

    def test_instance_relationships_bad_type_value(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            -   type: fake_relationship
                target: test_node
relationships:
    test_relationship: {}
            """
        self.assert_parser_raise_exception(26, DSLParsingLogicException)

    def test_instance_relationships_same_source_and_target(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node2
relationships:
    test_relationship: {}
            """
        self.assert_parser_raise_exception(23, DSLParsingLogicException)

    def test_instance_relationship_with_undefined_plugin(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            -   type: "test_relationship"
                target: "test_node"
                source_interfaces:
                    an_interface:
                        op: no_plugin.op
relationships:
    test_relationship: {}
                        """
        self.assert_parser_raise_exception(19, DSLParsingLogicException)

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

    def test_ambiguous_plugin_operation_mapping(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    test_type: {}
node_templates:
    test_node:
        type: test_type
        interfaces:
            test_interface:
                op: one.two.three.four
plugins:
    one.two:
        executor: host_agent
        source: dummy
    one:
        executor: host_agent
        source: dummy
        """
        self.assert_parser_raise_exception(91, DSLParsingLogicException)

    def test_node_set_non_existing_property(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += """
node_types:
    test_type: {}
"""
        ex = self.assert_parser_raise_exception(106, DSLParsingLogicException)
        self.assertEquals('key', ex.property)

    def test_node_doesnt_implement_schema_mandatory_property(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += """
node_types:
    test_type:
        properties:
            key: {}
            mandatory: {}
"""
        ex = self.assert_parser_raise_exception(107, DSLParsingLogicException)
        self.assertEquals('mandatory', ex.property)

    def test_relationship_instance_set_non_existing_property(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        properties:
            key: "val"
        relationships:
            -   type: test_relationship
                target: test_node
                properties:
                    do_not_exist: some_value
relationships:
    test_relationship: {}
"""
        ex = self.assert_parser_raise_exception(106, DSLParsingLogicException)
        self.assertEquals('do_not_exist', ex.property)

    def test_relationship_instance_doesnt_implement_schema_mandatory_property(self):  # NOQA
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        properties:
            key: "val"
        relationships:
            -   type: test_relationship
                target: test_node
relationships:
    test_relationship:
        properties:
            should_implement: {}
"""
        ex = self.assert_parser_raise_exception(107, DSLParsingLogicException)
        self.assertEquals('should_implement', ex.property)

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

    def test_group_missing_member(self):
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
        members: [vm]
        policies:
            policy:
                type: policy_type
                properties: {}
"""
        self.assert_parser_raise_exception(40, DSLParsingLogicException)

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

    def test_properties_schema_invalid_values_for_types(self):
        def test_type_with_value(prop_type, prop_val):
            self.template.clear()
            self.template.version_section('1.0')
            self.template += """
node_templates:
    test_node:
        type: test_type
        properties:
            string1: {0}
node_types:
    test_type:
        properties:
            string1:
                type: {1}
        """.format(prop_val, prop_type)
            self.assert_parser_raise_exception(
                ERROR_VALUE_DOES_NOT_MATCH_TYPE,
                DSLParsingLogicException)

        test_type_with_value('boolean', 'not-a-boolean')
        test_type_with_value('boolean', '"True"')
        test_type_with_value('boolean', '5')
        test_type_with_value('boolean', '5.0')
        test_type_with_value('boolean', '1')
        test_type_with_value('integer', 'not-an-integer')
        test_type_with_value('integer', 'True')
        test_type_with_value('integer', '"True"')
        test_type_with_value('integer', '5.0')
        test_type_with_value('integer', '"5"')
        test_type_with_value('integer', 'NaN')
        test_type_with_value('float', 'not-a-float')
        test_type_with_value('float', 'True')
        test_type_with_value('float', '"True"')
        test_type_with_value('float', '"5.0"')
        test_type_with_value('float', 'NaN')
        test_type_with_value('float', 'inf')

    def test_no_version_field(self):
        self.template.node_type_section()
        self.template.node_template_section()
        self.assert_parser_raise_exception(
            27, DSLParsingLogicException)

    def test_no_version_field_in_main_blueprint_file(self):
        self.template.version_section('1.0')
        imported_yaml_filename = self.create_yaml_with_imports(
            [str(self.template)])
        self.template.clear()
        self.template += imported_yaml_filename
        self.template.node_type_section()
        self.template.node_template_section()
        self.assert_parser_raise_exception(27, DSLParsingLogicException)

    def test_mismatching_version_in_import(self):
        self.template.version_section('1.0')
        self.template += self.create_yaml_with_imports(
            [self.template.version_section('1.1', raw=True)])
        self.template.node_type_section()
        self.template.node_template_section()
        self.assert_parser_raise_exception(28, DSLParsingLogicException)

    def test_unsupported_version(self):
        self.template.version_section('unsupported_version')
        self.template.node_type_section()
        self.template.node_template_section()
        self.assert_parser_raise_exception(29, DSLParsingLogicException)

    def test_script_mapping_illegal_script_path_override(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    {0}:
        executor: central_deployment_agent
        install: false
node_types:
    type:
        interfaces:
            test:
                op:
                    implementation: stub.py
                    inputs:
                        script_path:
                            default: invalid
                            type: string
node_templates:
    node:
        type: type

""".format(SCRIPT_PLUGIN_NAME)
        self.write_to_file(content='content', filename='stub.py')
        yaml_path = self.write_to_file(
            content=str(self.template), filename='blueprint.yaml')
        exc = self.assertRaises(DSLParsingLogicException, parse, yaml_path)
        self.assertEqual(60, exc.err_code)

    def test_script_mapping_missing_script_plugin(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    type:
        interfaces:
            test:
                op:
                    implementation: stub.py
                    inputs: {}
node_templates:
    node:
        type: type
"""
        self.write_to_file(content='content', filename='stub.py')
        yaml_path = self.write_to_file(
            content=str(self.template), filename='blueprint.yaml')
        exc = self.assertRaises(DSLParsingLogicException, parse, yaml_path)
        self.assertEqual(61, exc.err_code)

    def test_plugin_with_install_args_wrong_dsl_version(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template += self.template.PLUGIN_WITH_INSTALL_ARGS
        self.template += self.template.BASIC_TYPE
        self.assert_parser_raise_exception(
            ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH, DSLParsingException)

    def test_parse_empty_or_none_dsl_version(self):
        expected_err_msg = 'tosca_definitions_version is missing or empty'
        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg,
                               parse_dsl_version, '')
        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg,
                               parse_dsl_version, None)

    def test_parse_not_string_dsl_version(self):
        expected_err_msg = 'Invalid tosca_definitions_version: \[1\] is not' \
                           ' a string'
        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg,
                               parse_dsl_version, [1])

    def test_parse_wrong_dsl_version_format(self):
        expected_err_msg = (
            'Unexpected tosca_definitions_version {0}; '
            'Currently supported versions are:')
        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg.format('1_0'),
                               parse_dsl_version, '1_0')

        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg.format('cloudify_dsl_1.0'),
                               parse_dsl_version,
                               'cloudify_dsl_1.0')

        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg.format('cloudify_dsl_a_0'),
                               parse_dsl_version,
                               'cloudify_dsl_a_0')

        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg.format('cloudify_dsl_1_a'),
                               parse_dsl_version,
                               'cloudify_dsl_1_a')

        self.assertRaisesRegex(DSLParsingLogicException,
                               expected_err_msg.format('cloudify_dsl_1_1_a'),
                               parse_dsl_version,
                               'cloudify_dsl_1_1_a')

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
        self.template.node_type_section()
        self.template.node_template_section()
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
        self.template.node_type_section()
        self.template.node_template_section()
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

    def test_missing_required_property(self):
        self.template.version_section('1.2')
        self.template += """
node_types:
  type:
    properties:
      property:
        required: true
node_templates:
  node:
    type: type
"""
        self.assert_parser_raise_exception(107, DSLParsingLogicException)

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
