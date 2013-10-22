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

    def test_no_application_template(self):
        yaml = """
interfaces:
    test_interface2:
        operations:
            -   "install"
            -   "terminate"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_no_application_template_name(self):
        yaml = """
application_template:
    topology:
        -   name: test_node
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_illegal_first_level_property(self):
        yaml = """
application_template:
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
application_template:
    name: test_app
    topology:
        -   type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_node_without_type_declaration(self):
        yaml = """
application_template:
    name: test_app
    topology:
        -   name: test_node
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_no_operations(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
interfaces:
    test_interface1: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_empty_operations_list(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations: {}
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_duplicate_operations(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
            -   "install"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
                some_other_property: "meh"

            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1:
                    explicit_plugin1: "test_plugin1"
                    explicit_plugin2: "test_plugin2"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_empty_interfaces_declaration(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces: {}
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_dsl_with_explicit_interface_mapped_to_two_plugins(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
            extra_property: "val"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_without_url(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
        properties:
            url: "http://test_url.zip"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_plugin_without_derived_from_field(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
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
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations:
            -   "install"

plugins:
    test_plugin:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
        properties:
            url: "http://test_url.zip"
            interface: "test_interface1"
            extra_prop: "some_val"
            """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
    install:
        some_other_prop: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_extra_properties(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
    install:
        radial: "custom radial"
        some_other_prop: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_both_ref_and_radial(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
    install:
        radial: "custom radial"
        ref: "custom_ref"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_no_ref_or_radial(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        workflows:
            install:
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_extra_properties(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_workflows_both_ref_and_radial(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                ref: "custom_ref"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            workflows:
                install:
                    some_other_prop: "val"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_extra_properties(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            workflows:
                install:
                    radial: "custom radial"
                    some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_both_ref_and_radial(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            workflows:
                install:
                    radial: "custom radial"
                    ref: "custom_ref"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_extra_properties(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom clojure code"
            extra_prop: "extra prop value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_both_policy_and_ref(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom clojure code"
            ref: "ref value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_empty_policy(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy: {}
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_no_policy_and_ref(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_no_message(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy:
            ref: "ref value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_empty_rule(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    types:
        custom_policy:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_no_message(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    rules:
        custom_rule:
            rule: "custom clojure code"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_no_rule(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    rules:
        custom_rule:
            message: "custom message"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_top_level_policies_rules_extra_prop(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
policies:
    rules:
        custom_rule:
            message: "custom message"
            rule: "custom clojure code"
            extra_prop: "extra prop value"
    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_empty_policy(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy: {}
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_empty_rules(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_empty_rules(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_policy_with_extra_prop(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    extra_prop: "value"
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                                value: "custom value"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_with_extra_prop(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            extra_prop: "value"
                            properties:
                                state: "custom state"
                                value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_without_type(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   properties:
                                state: "custom state"
                                value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_without_properties(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


    def test_instance_policies_rule_properties_extra_prop(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                                value: "custom value"
                                extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_properties_without_value(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                state: "custom state"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_instance_policies_rule_properties_without_state(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                custom_policy:
                    rules:
                        -   type: "custom type"
                            properties:
                                value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)




    def test_type_policies_empty_policy(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy: {}
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_empty_rules(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_empty_rules(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules: []
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_policy_with_extra_prop(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                extra_prop: "value"
                rules:
                    -   type: "custom type"
                        properties:
                            state: "custom state"
                            value: "custom value"
                    """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_with_extra_prop(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        extra_prop: "value"
                        properties:
                            state: "custom state"
                            value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_without_type(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   properties:
                            state: "custom state"
                            value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_without_properties(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


    def test_type_policies_rule_properties_extra_prop(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        properties:
                            state: "custom state"
                            value: "custom value"
                            extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_policies_rule_properties_without_value(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            custom_policy:
                rules:
                    -   type: "custom type"
                        properties:
                            value: "custom value"
                """
        self._assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)