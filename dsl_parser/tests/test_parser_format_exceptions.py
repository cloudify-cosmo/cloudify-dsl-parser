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

from dsl_parser.parser import DSLParsingFormatException
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestParserFormatExceptions(AbstractTestParser):

    def test_empty_dsl(self):
        self._assert_dsl_parsing_exception_error_code('', 0, DSLParsingFormatException)

    def test_illegal_yaml_dsl(self):
        yaml = """
interfaces:
    test_interface:
        -   item1: {}
    -   bad_format: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, -1, DSLParsingFormatException)

    def test_no_blueprint(self):
        yaml = """
interfaces:
    test_interface2:
        operations:
            -   "install"
            -   "terminate"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_no_blueprint_name(self):
        yaml = """
blueprint:
    topology:
        -   name: test_node
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_illegal_first_level_property(self):
        yaml = """
blueprint:
    topology:
        -   name: test_node
            type: test_type
            properties:
                key: "val"

illegal_property:
    illegal_sub_property: "some_value"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_node_without_name(self):
        yaml = """
blueprint:
    name: test_app
    topology:
        -   type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_node_without_type_declaration(self):
        yaml = """
blueprint:
    name: test_app
    topology:
        -   name: test_node
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_no_operations(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
interfaces:
    test_interface1: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_empty_operations_list(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_duplicate_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
            -   "install"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
                some_other_property: "meh"

            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1:
                    explicit_plugin1: "test_plugin1"
                    explicit_plugin2: "test_plugin2"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_empty_interfaces_declaration(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces: {}
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_dsl_with_explicit_interface_mapped_to_two_plugins(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1:
                    -   "test_plugin"
                    -   "test_plugin2"
        properties:
            install_agent: 'false'
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_node_extra_properties(self):
        #testing for additional properties directly under node (i.e. not within the node's 'properties' section)
        yaml = self.BASIC_BLUEPRINT_SECTION + """
            extra_property: "val"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_without_url(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            interface: "test_interface1"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_import_bad_syntax(self):
        yaml = """
imports: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 2, DSLParsingFormatException)

    def test_import_bad_syntax2(self):
        yaml = """
imports:
    first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 2, DSLParsingFormatException)

    def test_import_bad_syntax3(self):
        yaml = """
imports:
    -   first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 2, DSLParsingFormatException)

    def test_duplicate_import_in_same_file(self):
        yaml = """
imports:
    -   fake-file.yaml
    -   fake-file2.yaml
    -   fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 2, DSLParsingFormatException)

    def test_type_multiple_derivation(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            key: "not_val"
        derived_from:
            -   "test_type_parent"
            -   "test_type_parent2"

    test_type_parent:
        properties:
            key: "val1_parent"
    test_type_parent2:
        properties:
            key: "val1_parent2"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_without_interface(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_without_derived_from_field(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        properties:
            url: "http://test_url.zip"
            interface: "test_interface1"
            extra_prop: "some_val"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_with_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
            interface: "test_interface1"
            extra_prop: "some_val"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install: {}        
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        radial: "custom radial"
        some_other_prop: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code', 'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        radial: "custom radial"
        ref: "{0}"
        """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_no_ref_or_radial(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install: {}
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_extra_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code', 'custom_ref.radial')
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    some_other_prop: "val"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    radial: "custom radial"
                    some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code', 'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    radial: "custom radial"
                    ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_extra_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom clojure code"
            extra_prop: "extra prop value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_both_policy_and_ref(self):
        file_name = self.make_file_with_name('some clojure code', 'custom_ref.clj')
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom clojure code"
            ref: "{0}"
    """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_empty_policy(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy: {}
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_no_policy_and_ref(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_no_message(self):
        file_name = self.make_file_with_name('some clojure code', 'custom_ref.clj')
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy:
            ref: "{0}"
    """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_empty_rule(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_no_message(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    rules:
        custom_rule:
            rule: "custom clojure code"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_no_rule(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    rules:
        custom_rule:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_extra_prop(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
policies:
    rules:
        custom_rule:
            message: "custom message"
            rule: "custom clojure code"
            extra_prop: "extra prop value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_empty_policy(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy: {}
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_empty_rules(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_empty_rules(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    extra_prop: "value"
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                                service: "custom value"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_with_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            extra_prop: "value"
                            properties:
                                state: "custom state"
                                service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_without_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   properties:
                                state: "custom state"
                                service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_without_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


    def test_instance_policies_rule_properties_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                                service: "custom value"
                                extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_properties_without_value(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_properties_without_state(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)




    def test_type_policies_empty_policy(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy: {}
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_empty_rules(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_empty_rules(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_extra_prop(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                extra_prop: "value"
                rules:
                    -   type: "custom type"
                        properties:
                            state: "custom state"
                            service: "custom value"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_with_extra_prop(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        extra_prop: "value"
                        properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_without_type(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   properties:
                            state: "custom state"
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_without_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


    def test_type_policies_rule_properties_extra_prop(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        properties:
                            state: "custom state"
                            service: "custom value"
                            extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_properties_without_value(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        properties:
                            state: "custom state"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_properties_without_state(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        properties:
                            service: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_bad_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    extra_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        extra_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_empty_interface(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface: {}
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_without_name(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface:
            operations:
                -   "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_without_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface:
            name: "test_rel_interface"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_with_empty_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface:
            name: "test_rel_interface"
            operations: []
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_with_operations_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface:
            name: "test_rel_interface"
            operations: "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_with_duplicate_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        interface:
            name: "test_rel_interface"
            operations:
                -   "install"
                -   "remove"
                -   "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_workflow_with_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflow:
            install: {}
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_workflow_with_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflow:
            install:
                radial: "custom radial"
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_workflow_with_both_ref_or_radial(self):
        file_name = self.make_file_with_name('some radial code', 'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflow:
            install:
                radial: "custom radial"
                ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_relationship(self):
        #relationships are not valid under types whatsoever.
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        relationships: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   target: "fake_node"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_target(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_target(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_derived_from_field(self):
        #derived_from field is not valid under an instance relationship definition
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    derived_from: "relationship"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_object(self):
        #trying to use a dictionary instead of an array
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                test_relationship:
                    type: "fake_relationship"
                    target: "fake_node"
                    derived_from: "relationship"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)








    def test_instance_relationships_relationship_with_empty_interface(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface: {}
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_interface_without_name(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface:
                        operations:
                            -   "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_interface_without_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface:
                        name: "test_rel_interface"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_interface_with_empty_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface:
                        name: "test_rel_interface"
                        operations: []
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_interface_with_operations_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface:
                        name: "test_rel_interface"
                        operations: "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_interface_with_duplicate_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    interface:
                        name: "test_rel_interface"
                        operations:
                            -   "install"
                            -   "remove"
                            -   "install"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_workflow_with_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    workflow:
                        install: {}
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_workflow_with_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    workflow:
                        install:
                            radial: "custom radial"
                            some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_workflow_with_both_ref_or_radial(self):
        file_name = self.make_file_with_name('some radial code', 'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    workflow:
                        install:
                            radial: "custom radial"
                            ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_with_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            instances:
                deploy: 2
                extra_prop: value
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_without_deploy_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            instances:
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_multiple_instances_string_value(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            instances:
                deploy: '2'
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)