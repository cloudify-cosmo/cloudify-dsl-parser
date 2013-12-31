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
        self._assert_dsl_parsing_exception_error_code(self.BASIC_BLUEPRINT_SECTION, 7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install: missing_plugin.install
                - terminate: missing_plugin.terminate
        properties:
            install_agent: 'false'
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 10, DSLParsingLogicException)

    def test_missing_interface_definition(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            -   missing_interface: "test_plugin2"
        properties:
            install_agent: 'false'

plugins:
    test_plugin2:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            interface: "missing_interface"
            url: "http://test_url2.zip"
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 9, DSLParsingLogicException)

    def test_type_with_interface_with_explicit_illegal_plugin(self):
        #testing to see what happens when the plugin which is explicitly declared for an interface is in fact
        #a plugin which doesn't implement the said interface (even if it supports another interface with same
        # name operations)
        yaml = self.BASIC_BLUEPRINT_SECTION + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
    test_interface2:
        operations:
            -   "install"
            -   "terminate"

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            interface: "test_interface1"
            url: "http://test_url.zip"

types:
    test_type:
        interfaces:
            -   test_interface2: "test_plugin"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 6, DSLParsingLogicException)


    def test_merge_non_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION, self.BASIC_PLUGIN]) + """
blueprint:
    name: test_app2
    topology:
        -   name: test_node2
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 3, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)

    def test_type_derive_non_from_none_existing(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        interfaces:
            -   test_interface1
        derived_from: "non_existing_type_parent"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 14, DSLParsingLogicException)

    def test_import_bad_path(self):
        yaml = """
imports:
    -   fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 13, DSLParsingLogicException)

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
        ex = self._assert_dsl_parsing_exception_error_code(yaml, 100, DSLParsingLogicException)
        expected_circular_dependency = ['test_type', 'test_type_parent', 'test_type_grandparent', 'test_type']
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
        ex = self._assert_dsl_parsing_exception_error_code(yaml, 101, DSLParsingLogicException)
        self.assertEquals('test_node', ex.duplicate_node_name)

    def test_first_level_workflows_unavailable_ref(self):
        ref_alias = 'custom_ref_alias'
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        ref: {0}
        """.format(ref_alias)
        self._assert_dsl_parsing_exception_error_code(yaml, 31)

    def test_type_duplicate_interface(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1
            -   test_interface1: test_plugin
"""
        ex = self._assert_dsl_parsing_exception_error_code(yaml, 102, DSLParsingLogicException)
        self.assertEquals('test_node', ex.node_name)
        self.assertEquals('test_interface1', ex.duplicate_interface_name)

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
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION, self.BASIC_PLUGIN]) + """
plugins:
    test_plugin:
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
types:
    test_type:
        interfaces:
            -   test_interface1
            -   test_interface2

interfaces:
    test_interface2:
        operations:
            -   "start"
            -   "shutdown"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 16, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 17, DSLParsingLogicException)

    def test_type_with_undefined_policy_event(self):
        yaml = self.POLICIES_SECTION + self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            -   name: undefined_policy
                rules:
                    -   type: "test_rule"
                        properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 16, DSLParsingLogicException)

    def test_type_with_undefined_rule(self):
        yaml = self.POLICIES_SECTION + self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            -   name: test_policy
                rules:
                    -   type: "undefined_rule"
                        properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 17, DSLParsingLogicException)

    def test_plugin_with_wrongful_derived_from_field(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "bad value"
        properties:
            interface: "test_interface1"
            url: "http://test_url.zip"

types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 18, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_undefined_plugin(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            some_interface:
                - op: no_plugin.op
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 19, DSLParsingLogicException)


    def test_top_level_relationships_import_same_name_relationship(self):
        imported_yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship: {}
            """
        yaml = self.create_yaml_with_imports([imported_yaml]) + """
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 100, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 25, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 26, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 23, DSLParsingLogicException)

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
        self._assert_dsl_parsing_exception_error_code(yaml, 19, DSLParsingLogicException)


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
            -   "test_interface"
interfaces:
    test_interface:
        operations:
            -   start
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            interface: "test_interface"
            url: "http://test_plugin.zip"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 24, DSLParsingLogicException)

    def test_type_derive_auto_wire_ambiguous(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific1_test_type:
        derived_from: test_type
    specific2_test_type:
        derived_from: test_type

"""
        ex = self._assert_dsl_parsing_exception_error_code(yaml, 103, DSLParsingLogicException)
        self.assertItemsEqual(['specific1_test_type', 'specific2_test_type'], ex.descendants)

    def test_type_derive_auto_wire_ambiguous_with_implements(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific1_test_type:
        derived_from: test_type
    specific2_test_type:
        implements: test_type

"""
        ex = self._assert_dsl_parsing_exception_error_code(yaml, 103, DSLParsingLogicException)
        self.assertItemsEqual(['specific1_test_type', 'specific2_test_type'], ex.descendants)