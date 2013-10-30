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

import os
from dsl_parser.parser import DSLParsingLogicException, parse_from_path
from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from urllib import pathname2url

class TestParserLogicExceptions(AbstractTestParser):

    def test_no_type_definition(self):
        self._assert_dsl_parsing_exception_error_code(self.BASIC_blueprint_SECTION, 7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_blueprint_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "missing_plugin"
        properties:
            install_agent: 'false'
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 10, DSLParsingLogicException)

    def test_missing_interface_definition(self):
        yaml = self.BASIC_blueprint_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
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
        yaml = self.BASIC_blueprint_SECTION + """
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

    def test_implicit_interface_with_no_matching_plugins(self):
        yaml = self.BASIC_blueprint_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface2
        properties:
            install_agent: 'false'

interfaces:
    test_interface2:
        operations:
            -   "install"
            -   "terminate"
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 11, DSLParsingLogicException)

    def test_implicit_interface_with_ambiguous_matches(self):
        yaml = self.create_yaml_with_imports([self.blueprint_WITH_INTERFACES_AND_PLUGINS]) + """
plugins:
    other_test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            interface: "test_interface1"
            url: "http://other_test_url.zip"
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 12, DSLParsingLogicException)

    def test_dsl_with_interface_without_plugin(self):
        yaml = self.BASIC_blueprint_SECTION + self.BASIC_TYPE + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 5, DSLParsingLogicException)

    def test_merge_non_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_blueprint_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        imported_yaml = self.MINIMAL_blueprint + """
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

    def test_recursive_imports_with_inner_circular(self):
        bottom_level_yaml = """
imports:
    -   {0}
        """.format(os.path.join(self._temp_dir, "mid_level.yaml")) + self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_file_with_name(mid_level_yaml, 'mid_level.yaml')

        top_level_yaml = self.BASIC_blueprint_SECTION + """
imports:
    -   {0}""".format(mid_file_name)

        ex = self._assert_dsl_parsing_exception_error_code(top_level_yaml, 8, DSLParsingLogicException)
        expected_circular_path = [pathname2url(x) for x in [mid_file_name, bottom_file_name, mid_file_name]]
        self.assertEquals(len(expected_circular_path), len(ex.circular_path))
        for expected_element, element in zip(expected_circular_path, ex.circular_path):
            self.assertTrue(expected_element in element, '{0} not in {1}'.format(expected_element,element))

    def test_recursive_imports_with_complete_circle(self):
        bottom_level_yaml = """
imports:
    -   {0}
            """.format(os.path.join(self._temp_dir, "top_level.yaml")) + self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_blueprint_SECTION + """
imports:
    -   {0}""".format(mid_file_name)
        top_file_name = self.make_file_with_name(top_level_yaml, 'top_level.yaml')
        ex = self._assert_dsl_parsing_exception_error_code(top_file_name, 8, DSLParsingLogicException, parse_from_path)
        expected_circular_path = [pathname2url(x) for x in [top_file_name, mid_file_name, bottom_file_name,
                                  top_file_name]]
        self.assertEquals(len(expected_circular_path), len(ex.circular_path))
        for expected_element, element in zip(expected_circular_path, ex.circular_path):
            self.assertTrue(expected_element in element, '{0} not in {1}'.format(expected_element,element))

    def test_type_derive_non_from_none_existing(self):
        yaml = self.BASIC_blueprint_SECTION + """
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
        yaml = self.BASIC_blueprint_SECTION + """
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
        yaml = self.MINIMAL_blueprint + """
workflows:
    install:
        ref: {0}
        """.format(ref_alias)
        self._assert_dsl_parsing_exception_error_code(yaml, 15)

    def test_type_duplicate_interface(self):
        yaml = self.BASIC_blueprint_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
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
        yaml = self.MINIMAL_blueprint + """
policies:
    types:
        custom_policy:
            message: "custom message"
            ref: {0}
        """.format(ref_alias)
        self._assert_dsl_parsing_exception_error_code(yaml, 15)

    def test_illegal_merge_on_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_blueprint_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        imported_yaml = self.MINIMAL_blueprint + """
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
        yaml = self.POLICIES_SECTION + self.MINIMAL_blueprint + """
            policies:
                undefined_policy:
                    rules:
                        -   type: "test_rule"
                            properties:
                                state: "custom state"
                                value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 16, DSLParsingLogicException)

    def test_node_with_undefined_rule(self):
        yaml = self.POLICIES_SECTION + self.MINIMAL_blueprint + """
            policies:
                test_policy:
                    rules:
                        -   type: "undefined_rule"
                            properties:
                                state: "custom state"
                                value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 17, DSLParsingLogicException)

    def test_type_with_undefined_policy_event(self):
        yaml = self.POLICIES_SECTION + self.BASIC_blueprint_SECTION + """
types:
    test_type:
        policies:
            undefined_policy:
                rules:
                    -   type: "test_rule"
                        properties:
                            state: "custom state"
                            value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 16, DSLParsingLogicException)

    def test_type_with_undefined_rule(self):
        yaml = self.POLICIES_SECTION + self.BASIC_blueprint_SECTION + """
types:
    test_type:
        policies:
            test_policy:
                rules:
                    -   type: "undefined_rule"
                        properties:
                            state: "custom state"
                            value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 17, DSLParsingLogicException)

    def test_plugin_with_wrongful_derived_from_field(self):
        yaml = self.BASIC_blueprint_SECTION + """
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
        yaml = self.MINIMAL_blueprint + """
relationships:
    test_relationship:
        plugin: "undefined_plugin"
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 19, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_bad_bind_at_value(self):
        yaml = self.MINIMAL_blueprint + """
relationships:
    test_relationship:
        bind_at: "bad_value"
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 20, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_bad_run_on_node_value(self):
        yaml = self.MINIMAL_blueprint + """
relationships:
    test_relationship:
        run_on_node: "bad_value"
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 21, DSLParsingLogicException)

    def test_top_level_relationships_import_same_name_relationship(self):
        imported_yaml = self.MINIMAL_blueprint + """
relationships:
    test_relationship: {}
            """
        yaml = self.create_yaml_with_imports([imported_yaml]) + """
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)

    def test_top_level_relationships_circular_inheritance(self):
        yaml = self.MINIMAL_blueprint + """
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
        yaml = self.MINIMAL_blueprint + """
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
        yaml = self.MINIMAL_blueprint + """
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
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node2
relationships:
    test_relationship: {}
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 23, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_undefined_plugin(self):
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    plugin: "undefined_plugin"
relationships:
    test_relationship: {}
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 19, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_bad_bind_at_value(self):
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    bind_at: "bad_value"
relationships:
    test_relationship: {}
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 20, DSLParsingLogicException)

    def test_top_level_relationships_relationship_with_bad_run_on_node_value(self):
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    run_on_node: "bad_value"
relationships:
    test_relationship: {}
                        """
        self._assert_dsl_parsing_exception_error_code(yaml, 21, DSLParsingLogicException)

    #Note: the following tests ensure that there are no duplicate interfaces definitions in any sections of the input.
    #there are additional tests that could have been done, yet this part is subject to change in the very near future,
    #and thus the tests that were already created remained for the moment with no additional ones created.
    def test_top_level_relationships_duplicate_interface_to_top_level_interfaces(self):
        yaml = self.blueprint_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    test_relationship:
        interface:
            name: "test_interface1"
            operations:
                -   "start"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 22, DSLParsingLogicException)

    def test_top_level_relationships_duplicate_interface_to_another_top_level_relationship(self):
        yaml = self.MINIMAL_blueprint + """
relationships:
    test_relationship:
        interface:
            name: "test_interface1"
            operations:
                -   "start"
    test_relationship_2:
        interface:
            name: "test_interface1"
            operations:
                -   "stop"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 22, DSLParsingLogicException)

    def test_instance_relationships_duplicate_interface_to_top_level_interfaces(self):
        #note that this duplicate will generate an error despite the fact that the
        #interface from the top-level interfaces section is not even actually used
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node
                    interface:
                        name: "test_interface1"
                        operations:
                            -   "start"
relationships:
    test_relationship: {}
interfaces:
    test_interface1:
        operations:
            -   "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 22, DSLParsingLogicException)

    def test_instance_relationships_duplicate_interface_to_top_level_relationships_interface(self):
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node
                    interface:
                        name: "test_interface2"
                        operations:
                            -   "start"
relationships:
    test_relationship: {}
    test_relationship2:
        interface:
            name: "test_interface2"
            operations:
                -   "install"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 22, DSLParsingLogicException)

    def test_instance_relationships_duplicate_interface_to_top_level_relationships_interface_despite_override(self):
        #Very similar to the previous test, this test also ensures that same name interface
        #is still invalid even if the duplicate is defined in a context of an override.
        yaml = self.MINIMAL_blueprint + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node
                    interface:
                        name: "test_interface2"
                        operations:
                            -   "start"
relationships:
    test_relationship:
        interface:
            name: "test_interface2"
            operations:
                -   "install"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 22, DSLParsingLogicException)

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

