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
            self.BASIC_BLUEPRINT_SECTION, 7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install: missing_plugin.install
                - terminate: missing_plugin.terminate
        properties:
            - install_agent: 'false'
            - key
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 10, DSLParsingLogicException)

    def test_merge_non_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
blueprint:
    name: test_app2
    topology:
        -   name: test_node2
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 3, DSLParsingLogicException)

    def test_illegal_merge_on_nested_mergeable_rules_on_import(self):
        imported_yaml = self.MINIMAL_BLUEPRINT + """
policies:
    rules:
        rule1:
            message: "custom message"
            rule: "custom clojure code"
            """
        yaml = self.create_yaml_with_imports([imported_yaml]) + """
policies:
    rules:
        rule1:
            message: "some other message"
            rule: "some other code"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 4, DSLParsingLogicException)

    def test_type_derive_non_from_none_existing(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
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
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
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

    def test_node_duplicate_name(self):
        yaml = """
blueprint:
    name: test_app
    topology:
    -   name: test_node
        type: test_type
        properties:
            key: "val"
    -   name: test_node
        type: test_type
        properties:
            key: "val"

types:
    test_type: {}
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 101, DSLParsingLogicException)
        self.assertEquals('test_node', ex.duplicate_node_name)

    def test_first_level_workflows_unavailable_ref(self):
        ref_alias = 'custom_ref_alias'
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        ref: {0}
        """.format(ref_alias)
        self._assert_dsl_parsing_exception_error_code(yaml, 31)

    def test_first_level_policy_unavailable_ref(self):
        ref_alias = 'custom_ref_alias'
        yaml = self.MINIMAL_BLUEPRINT + """
policies:
    types:
        custom_policy:
            message: "custom message"
            ref: {0}
        """.format(ref_alias)
        self._assert_dsl_parsing_exception_error_code(yaml, 31)

    def test_illegal_merge_on_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
plugins:
    test_plugin:
        properties:
            url: "http://test_url2.zip"
types:
    test_type: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 4, DSLParsingLogicException)

    def test_illegal_merge_on_nested_mergeable_policies_events_on_import(self):
        imported_yaml = self.MINIMAL_BLUEPRINT + """
policies:
    types:
        policy1:
            message: "custom message"
            policy: "custom clojure code"
            """
        yaml = self.create_yaml_with_imports([imported_yaml]) + """
policies:
    types:
        policy1:
            message: "some other message"
            policy: "some other code"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 4, DSLParsingLogicException)

    def test_node_with_undefined_policy_event(self):
        yaml = self.POLICIES_SECTION + self.MINIMAL_BLUEPRINT + """
            policies:
                -   name: "undefined_policy_event"
                    rules:
                        -   type: "test_rule"
                            properties:
                                state: "custom state"
                                service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 16, DSLParsingLogicException)

    def test_node_with_undefined_rule(self):
        yaml = self.POLICIES_SECTION + self.MINIMAL_BLUEPRINT + """
            policies:
                -   name: "test_policy"
                    rules:
                        -   type: "undefined_rule"
                            properties:
                                state: "custom state"
                                service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 17, DSLParsingLogicException)

    def test_type_with_undefined_policy_event(self):
        yaml = self.POLICIES_SECTION + self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        policies:
            -   name: undefined_policy
                rules:
                    -   type: "test_rule"
                        properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 16, DSLParsingLogicException)

    def test_type_with_undefined_rule(self):
        yaml = self.POLICIES_SECTION + self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        policies:
            -   name: test_policy
                rules:
                    -   type: "undefined_rule"
                        properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 17, DSLParsingLogicException)

    def test_plugin_with_wrongful_derived_from_field(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
plugins:
    test_plugin:
        derived_from: "bad value"
        properties:
            url: "http://test_url.zip"

types:
    test_type:
        properties:
            - key
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
        #target value is a non-existent node
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
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
        #type value is a non-existent relationship
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
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
        #A relationship from a node to itself is not valid
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
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
        -   name: test_node2
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
blueprint:
    name: test_app
    topology:
        -   name: test_node1
            type: test_type
types:
    test_type:
        interfaces:
            test_interface:
                - start: test_plugin.start
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 24, DSLParsingLogicException)

    def test_type_implementation_ambiguous(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific1_test_type:
        derived_from: test_type
    specific2_test_type:
        derived_from: test_type

type_implementations:
    first_implementation:
        derived_from: specific1_test_type
        node_ref: test_node
    second_implementation:
        derived_from: specific2_test_type
        node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 103, DSLParsingLogicException)
        self.assertItemsEqual(
            ['first_implementation', 'second_implementation'],
            ex.implementations)

    def test_type_implementation_not_derived_type(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific1_test_type: {}

type_implementations:
    impl:
        derived_from: specific1_test_type
        node_ref: test_node
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 102, DSLParsingLogicException)
        self.assertEquals('impl', ex.implementation)

    def test_node_interface_duplicate_operation_with_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
            interfaces:
                test_interface1:
                    - install
                    - install: test_plugin.install
types:
    test_type:
        properties:
            - key
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_type_interface_duplicate_operation_with_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install
                - install: test_plugin.install
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_relationship_source_interface_duplicate_operation_with_mapping(
            self):
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
types:
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
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
types:
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
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: empty_relationship
                    target: test_node
                    source_interfaces:
                        test_interface1:
                            - install
                            - install: test_plugin.install
types:
    test_type:
        properties:
            - key: default
relationships:
    empty_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_instance_relationship_target_interface_duplicate_operation_with_mapping(self):  # NOQA
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: empty_relationship
                    target: test_node
                    target_interfaces:
                        test_interface1:
                            - install
                            - install: test_plugin.install
types:
    test_type:
        properties:
            - key: default
relationships:
    empty_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 20, DSLParsingLogicException)

    def test_operation_properties_injection_get_property_non_existing_prop(
            self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            - key
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
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            - some_key: 'val'
            - key
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

    def test_node_set_non_existing_property(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type: {}
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)
        self.assertEquals('key', ex.property)

    def test_node_doesnt_implement_schema_mandatory_property(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            - key
            - mandatory
"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException)
        self.assertEquals('mandatory', ex.property)
