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

__author__ = 'ran'

from dsl_parser.parser import DSLParsingLogicException, parse_from_path
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestParserLogicExceptions(AbstractTestParser):

    def test_parse_dsl_from_file_bad_path(self):
        self.assertRaises(EnvironmentError, parse_from_path, 'fake-file.yaml')

    def test_no_type_definition(self):
        self._assert_dsl_parsing_exception_error_code(
            self.BASIC_NODE_TEMPLATES_SECTION, 7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                - install: missing_plugin.install
                - terminate: missing_plugin.terminate
        properties:
            install_agent:
                default: 'false'
            key: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 10, DSLParsingLogicException)

    def test_type_derive_non_from_none_existing(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        derived_from: "non_existing_type_parent"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 14, DSLParsingLogicException)

    def test_import_bad_path(self):
        yaml = """
imports:
    -   fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 13, DSLParsingLogicException)

    def test_cyclic_dependency(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        derived_from: "test_type_parent"

    test_type_parent:
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        derived_from: "test_type"
    """
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 100, DSLParsingLogicException)
        expected_circular_dependency = ['test_type', 'test_type_parent',
                                        'test_type_grandparent', 'test_type']
        self.assertEquals(expected_circular_dependency, ex.circular_dependency)

    def test_plugin_with_wrongful_executor_field(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
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
                - install: test_plugin.install

        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 18, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_undefined_plugin(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            some_interface:
                - op: no_plugin.op
                        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 19, DSLParsingLogicException)

    def test_workflow_mapping_no_plugin(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1: test_plugin2.workflow1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 21, DSLParsingLogicException)

    def test_top_level_relationships_import_same_name_relationship(self):
        imported_yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship: {}
            """
        yaml = self.create_yaml_with_imports([imported_yaml]) + """
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 4, DSLParsingLogicException)

    def test_top_level_relationships_circular_inheritance(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship1:
        derived_from: test_relationship2
    test_relationship2:
        derived_from: test_relationship3
    test_relationship3:
        derived_from: test_relationship1
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 100, DSLParsingLogicException)

    def test_instance_relationships_bad_target_value(self):
        # target value is a non-existent node
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: fake_node
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 25, DSLParsingLogicException)

    def test_instance_relationships_bad_type_value(self):
        # type value is a non-existent relationship
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: fake_relationship
                target: test_node
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 26, DSLParsingLogicException)

    def test_instance_relationships_same_source_and_target(self):
        # A relationship from a node to itself is not valid
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node2
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 23, DSLParsingLogicException)

    def test_instance_relationship_with_undefined_plugin(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: "test_relationship"
                target: "test_node"
                source_interfaces:
                    an_interface:
                        - op: no_plugin.op
relationships:
    test_relationship: {}
                        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 19, DSLParsingLogicException)

    def test_validate_agent_plugin_on_non_host_node(self):
        yaml = """
node_templates:
    test_node1:
        type: test_type
node_types:
    test_type:
        interfaces:
            test_interface:
                - start: test_plugin.start
plugins:
    test_plugin:
        executor: host_agent
        source: dummy
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 24, DSLParsingLogicException)

    def test_type_implementation_ambiguous(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
node_types:
    specific1_test_type:
        derived_from: test_type
    specific2_test_type:
        derived_from: test_type

type_implementations:
    first_implementation:
        type: specific1_test_type
        node_ref: test_node
    second_implementation:
        type: specific2_test_type
        node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 103, DSLParsingLogicException)
        self.assertItemsEqual(
            ['first_implementation', 'second_implementation'],
            ex.implementations)

    def test_type_implementation_not_derived_type(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
node_types:
    specific1_test_type: {}

type_implementations:
    impl:
        type: specific1_test_type
        node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 102, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)

    def test_node_interface_duplicate_operation_with_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
        interfaces:
            test_interface1:
                - install
                - install: test_plugin.install
node_types:
    test_type:
        properties:
            key: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_type_interface_duplicate_operation_with_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                - install
                - install: test_plugin.install
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_relationship_source_interface_duplicate_operation_with_mapping(
            self):
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type: {}
relationships:
    empty_relationship:
        source_interfaces:
            test_interface1:
                - install
                - install: test_plugin.install
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_relationship_target_interface_duplicate_operation_with_mapping(
            self):
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type: {}
relationships:
    empty_relationship:
        target_interfaces:
            test_interface1:
                - install
                - install: test_plugin.install
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_instance_relationship_source_interface_duplicate_operation_with_mapping(self):  # NOQA
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
    test_node2:
        type: test_type
        relationships:
            -   type: empty_relationship
                target: test_node
                source_interfaces:
                    test_interface1:
                        - install
                        - install: test_plugin.install
node_types:
    test_type:
        properties:
            key:
                default: 'default'
relationships:
    empty_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_instance_relationship_target_interface_duplicate_operation_with_mapping(self):  # NOQA
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
    test_node2:
        type: test_type
        relationships:
            -   type: empty_relationship
                target: test_node
                target_interfaces:
                    test_interface1:
                        - install
                        - install: test_plugin.install
node_types:
    test_type:
        properties:
            key:
                default: 'default'
relationships:
    empty_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_operation_properties_injection_get_property_non_existing_prop(
            self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        key: { get_property: 'non_existing_prop' }

"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 104, DSLParsingLogicException)
        self.assertEqual('non_existing_prop', ex.property_name)

    def test_operation_properties_injection_get_property_with_other_key(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            some_key:
                default: 'val'
            key: {}
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        key:
                            get_property: 'some_key'
                            some_prop: 'some_value'
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 105, DSLParsingLogicException)

    def test_operation_properties_injection_get_property_path_no_dict(
            self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        key: { get_property: 'key.nested' }
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 104, DSLParsingLogicException)
        self.assertEqual('key.nested', ex.property_name)

    def test_operation_properties_injection_get_property_path_no_array(
            self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        key: { get_property: 'key[0]' }
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 104, DSLParsingLogicException)
        self.assertEqual('key[0]', ex.property_name)

    def test_node_set_non_existing_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type: {}
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)
        self.assertEquals('key', ex.property)

    def test_node_doesnt_implement_schema_mandatory_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            key: {}
            mandatory: {}
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException)
        self.assertEquals('mandatory', ex.property)

    def test_relationship_instance_set_non_existing_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)
        self.assertEquals('do_not_exist', ex.property)

    def test_relationship_instance_doesnt_implement_schema_mandatory_property(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
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
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException)
        self.assertEquals('should_implement', ex.property)

    def test_instance_relationship_more_than_one_contained_in(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 112, DSLParsingLogicException)
        self.assertSetEqual({'cloudify.relationships.contained_in',
                             'derived_from_contained_in'},
                            set(ex.relationship_types))

    def test_relationship_implementation_ambiguous(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            - type: test_relationship
              target: test_node

relationships:
    test_relationship: {} """]) + """

relationships:
    specific_test_relationship:
        derived_from: test_relationship

relationship_implementations:
    specific_test_relationship_impl1:
        type: specific_test_relationship
        source_node_ref: test_node2
        target_node_ref: test_node
    specific_test_relationship_impl2:
        type: specific_test_relationship
        source_node_ref: test_node2
        target_node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 108, DSLParsingLogicException)
        self.assertItemsEqual(
            ['specific_test_relationship_impl1',
             'specific_test_relationship_impl2'],
            ex.implementations)

    def test_relationship_implementation_not_derived_type(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            - type: test_relationship
              target: test_node
relationships:
    test_relationship: {} """]) + """

relationships:
    specific_test_relationship: {}

relationship_implementations:
    impl:
        type: specific_test_relationship
        source_node_ref: test_node2
        target_node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 111, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)

    def test_type_impl_non_existing_node(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """

type_implementations:
    impl:
        type: test_type
        node_ref: non_existing_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 110, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)
        self.assertEquals('non_existing_node', ex.node_ref)

    def test_relationship_impl_non_existing_source_node(self):

        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
relationships:
    test_relationship: {}

relationship_implementations:
    impl:
        type: test_relationship
        source_node_ref: non_existing_node
        target_node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 111, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)
        self.assertEquals('non_existing_node', ex.source_node_ref)

    def test_relationship_impl_non_existing_target_node(self):

        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship: {}

relationship_implementations:
    impl:
        type: test_relationship
        source_node_ref: test_node
        target_node_ref: non_existing_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 111, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)

    def test_relationship_impl_for_no_relationship_specified(self):

        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type """]) + """

relationships:
    test_relationship: {}

relationship_implementations:
    impl:
        type: test_relationship
        source_node_ref: test_node
        target_node_ref: test_node2
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 111, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)

    def test_group_missing_member(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 40, DSLParsingLogicException)

    def test_group_missing_policy_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 41, DSLParsingLogicException)

    def test_group_missing_trigger_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 42, DSLParsingLogicException)

    def test_group_policy_type_undefined_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)

    def test_group_policy_type_missing_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException)

    def test_group_policy_trigger_undefined_parameter(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)

    def test_group_policy_trigger_missing_parameter(self):
        yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException)
