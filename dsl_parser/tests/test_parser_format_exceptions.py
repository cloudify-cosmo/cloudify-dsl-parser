########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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
import dsl_parser.exceptions as exceptions

from dsl_parser.exceptions import (
    DSLParsingFormatException,
    DSLParsingLogicException,
    DSLParsingInputTypeException)
from dsl_parser.parser import parse as dsl_parse
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestParserFormatExceptions(AbstractTestParser):

    def test_empty_dsl(self):
        self._assert_dsl_parsing_exception_error_code(
            '', 1, DSLParsingFormatException)

    def test_illegal_yaml_dsl(self):
        yaml = """
plugins:
    plugin1:
        -   item1: {}
    -   bad_format: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, -1, DSLParsingFormatException)

    def test_no_node_templates(self):
        yaml = """
plugins:
    plugin1:
        executor: central_deployment_agent
        source: dummy
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_templates_list_instead_of_dict(self):
        yaml = """
node_templates:
    - test_node:
        type: test_type
        properties:
            key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_name_field_under_node_templates(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    name: my_blueprint
    test_node:
        type: test_type
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_illegal_first_level_property(self):
        yaml = """
node_types:
    test_type:
        properties:
            key:
                default: 'default'
node_templates:
    test_node:
        type: test_type
        properties:
            key: "val"

illegal_property:
    illegal_sub_property: "some_value"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_with_name(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    test_node:
        name: my_node_name
        type: test_type
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_properties_as_list(self):
        yaml = """
node_templates:
    test_node:
        -   type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_without_type_declaration(self):
        yaml = """
node_templates:
    test_node:
        properties:
            key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                - should: be a dict
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                1 # not a string
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_3(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                a: 1 # key not a string
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_extra_properties(self):
        # testing for additional properties directly under node
        # (i.e. not within the node's 'properties' section)
        yaml = self.MINIMAL_BLUEPRINT + """
        extra_property: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_import_bad_syntax(self):
        yaml = """
imports: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_import_bad_syntax2(self):
        yaml = """
imports:
    first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_import_bad_syntax3(self):
        yaml = """
imports:
    -   first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_duplicate_import_in_same_file(self):
        yaml = """
imports:
    -   fake-file.yaml
    -   fake-file2.yaml
    -   fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 2, DSLParsingFormatException)

    def test_type_multiple_derivation(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
        derived_from:
            -   "test_type_parent"
            -   "test_type_parent2"

    test_type_parent:
        properties:
            key:
                default: "val1_parent"
    test_type_parent2:
        properties:
            key:
                default: "val1_parent2"
    """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_without_executor_field(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        source: dummy
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
        another_field: bad
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_bad_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    extra_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        extra_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_with_operations_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            test_rel_interface: string
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_relationship(self):
        # relationships are not valid under types whatsoever.
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        relationships: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   target: test_node2
    test_node2:
        type: test_type
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_target(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
relationships:
    relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
                target: "test_node2"
                extra_prop: "value"
    test_node2:
        type: test_type
relationships:
    relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_derived_from_field(self):
        # derived_from field is not valid under an instance relationship
        # definition
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
                target: test_node2
                derived_from: "relationship"
    test_node2:
        type: test_type
relationships:
    relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_object(self):
        # trying to use a dictionary instead of an array
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            test_relationship:
                type: "fake_relationship"
                target: "fake_node"
                derived_from: "relationship"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_with_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: 2
            extra_prop: value
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_without_deploy_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_string_value(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: '2'
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_operation_mapping_no_mapping_prop(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                  properties:
                      key: "value"
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_mapping_invalid_value(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1: 123
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_mapping_no_mapping_field(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        parameters:
            param: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_parameters_simple_dictionary_schema_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_parameters_array_dictionary_schema_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key:
                - default: val1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_parameters_schema_array_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            - key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_parameters_extra_property(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_workflow_properties_instead_of_parameters(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        properties:
            key:
                default: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_operation_mapping_unknown_extra_attributes(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                  implementation: test_plugin.install
                  inputs:
                      key: 'value'
                  unknown: 'bla'
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_simple_dictionary_schema_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_array_dictionary_schema_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                - default: val1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_schema_array_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            - key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_extra_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_properties_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_properties_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                - default: val1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_properties_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            - key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_properties_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_properties_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_properties_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key:
                - default: val1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_properties_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            - key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_properties_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_source_non_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: 1
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        extra_property: i_should_not_be_here
        source: source
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_type_missing_source(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_triggers_parameters_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_triggers_parameters_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key:
                - default: val1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_triggers_parameters_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            - key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_triggers_parameters_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_trigger_source_non_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: 1
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_trigger_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        extra_property: i_should_not_be_here
        source: source
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_policy_trigger_missing_source(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_groups_missing_member(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        policies:
            policy:
                type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_groups_extra_property(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                type: type
        extra_property: extra_property
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_groups_policy_missing_type(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                properties:
                    key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_groups_policy_extra_property(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                type: type
                extra_property: extra_property
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_group_members_bad_type1(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [1]
        policies:
            policy:
                type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_group_members_bad_type2(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: 1
        policies:
            policy:
                type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_group_policy_type_bad_type(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    vm:
        type: test_type
groups:
    group:
        members: [vm]
        policies:
            policy:
                type: 1
                properties:
                    key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_group_policy_type_bad_properties(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    vm:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [vm]
        policies:
            policy:
                type: type
                properties: properties
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_group_no_members(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: []
        policies:
            policy:
                type: type
                properties: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_unknown_property_schema_type(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                type: unknown-type
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, exceptions.ERROR_UNKNOWN_TYPE, DSLParsingLogicException)

    def test_invalid_version_field_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
tosca_definitions_version: [cloudify_dsl_1_0]
    """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException, dsl_parse)

    def test_invalid_blueprint_description_field_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
description:
  nested_key: value
  """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_unicode_in_blueprint(self):
        yaml = self.MINIMAL_BLUEPRINT + u"""
node_types:
    test_type:
        properties:
            key: "M\xf6tley Cr\xfce"
  """
        self._assert_dsl_parsing_exception_error_code(
            yaml, exceptions.ERROR_INVALID_CHARS, DSLParsingInputTypeException)
