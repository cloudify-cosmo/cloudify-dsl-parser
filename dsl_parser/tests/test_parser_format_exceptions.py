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
        self._assert_dsl_parsing_exception_error_code(
            '', 0, DSLParsingFormatException)

    def test_illegal_yaml_dsl(self):
        yaml = """
plugins:
    plugin1:
        -   item1: {}
    -   bad_format: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, -1, DSLParsingFormatException)

    def test_no_blueprint(self):
        yaml = """
plugins:
    plugin1:
        derived_from: cloudify.plugins.remote_plugin
        properties:
            url: some_url
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_no_blueprint_name(self):
        yaml = """
blueprint:
    nodes:
        -   name: test_node
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_illegal_first_level_property(self):
        yaml = """
blueprint:
    nodes:
        -   name: test_node
            type: test_type
            properties:
                key: "val"

illegal_property:
    illegal_sub_property: "some_value"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_without_name(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_without_type_declaration(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_with_no_operations(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    my_type:
        interfaces:
            my_interface: []
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_with_duplicate_operations(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    my_type:
        interfaces:
            test_interface1:
                -   install
                -   terminate
                -   install
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                should: be
                a: list
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - 1 # not a string
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_3(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - a: 1 # key not a string
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_with_empty_interfaces_declaration(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces: {}
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_node_extra_properties(self):
        #testing for additional properties directly under node
        # (i.e. not within the node's 'properties' section)
        yaml = self.BASIC_BLUEPRINT_SECTION + """
            extra_property: "val"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_without_url(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:

            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_import_bad_syntax(self):
        yaml = """
imports: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 2, DSLParsingFormatException)

    def test_import_bad_syntax2(self):
        yaml = """
imports:
    first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 2, DSLParsingFormatException)

    def test_import_bad_syntax3(self):
        yaml = """
imports:
    -   first_file: fake-file.yaml
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 2, DSLParsingFormatException)

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
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key: "not_val"
        derived_from:
            -   "test_type_parent"
            -   "test_type_parent2"

    test_type_parent:
        properties:
            - key: "val1_parent"
    test_type_parent2:
        properties:
            - key: "val1_parent2"
    """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_without_derived_from_field(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        properties:
            url: "http://test_url.zip"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_with_url_and_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
            extra_prop: "some_val"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_plugin_with_folder_and_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            folder: "http://test_url.zip"
            extra_prop: "some_val"
            """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        radial: "custom radial"
        some_other_prop: "val"
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_first_level_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code',
                                             'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
    install:
        radial: "custom radial"
        ref: "{0}"
        """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_workflows_no_ref_or_radial(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install: {}
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_workflows_extra_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code',
                                             'custom_ref.radial')
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        workflows:
            install:
                radial: "custom radial"
                ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    some_other_prop: "val"
                    """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    radial: "custom radial"
                    some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code',
                                             'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    radial: "custom radial"
                    ref: "{0}"
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflows:
            install: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflows:
            install:
                radial: radial
                some_other_prop: "val"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code',
                                             'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflows:
            install:
                radial: radial
                ref: {0}
                """.format(file_name)
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationship_workflows_no_ref_or_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   target: test_node
                    type: test_relationship
                    workflows:
                        install: {}
relationships:
    test_relationship: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationship_workflows_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   target: test_node
                    type: test_relationship
                    workflows:
                        install:
                            radial: radial
                            some_extra_prop: value
relationships:
    test_relationship: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationship_workflows_both_ref_and_radial(self):
        file_name = self.make_file_with_name('some radial code',
                                             'custom_ref.radial')
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   target: test_node
                    type: test_relationship
                    workflows:
                        install:
                            radial: radial
                            ref: {0}""".format(file_name) + """
relationships:
    test_relationship: {}
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

    def test_top_level_relationships_empty_interface(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces: {}
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_top_level_relationships_interface_without_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            my_interface: []
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

    def test_top_level_relationships_interface_with_duplicate_operations(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            test_rel_interface:
                -   install
                -   remove
                -   install
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_relationship(self):
        #relationships are not valid under types whatsoever.
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        relationships: {}
        """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   target: "fake_node"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_without_target(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    extra_prop: "value"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_derived_from_field(self):
        #derived_from field is not valid under an instance relationship
        # definition
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    derived_from: "relationship"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_object(self):
        #trying to use a dictionary instead of an array
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                test_relationship:
                    type: "fake_relationship"
                    target: "fake_node"
                    derived_from: "relationship"
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_empty_source_interfaces(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    source_interfaces: {}
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_empty_target_interfaces(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    target_interfaces: {}
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_source_interface_without_operations(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    source_interfaces:
                        my_interface: []
                """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_instance_relationships_relationship_with_target_interface_without_operations(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships:
                -   type: "fake_relationship"
                    target: "fake_node"
                    target_interfaces:
                        my_interface: []
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
            instances:
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
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install:
                    properties:
                        key: "value"
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_operation_mapping_no_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_operation_mapping_empty_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_interface_operation_mapping_unknown_extra_attributes(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        key: 'value'
                    unknown: 'bla'
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_not_schema_array_format(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            key: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_properties_dictionary_with_multiple_values(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            -   key1: value
                key2: value
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_implementation_no_ref(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
type_implementations:
    impl:
        type: test_type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_implementation_no_derived_from(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
type_implementations:
    impl:
        node_ref: test_node
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_implementation_properties_as_schema(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
type_implementations:
    impl:
        type: test_type
        node_ref: test_node
        properties:
            - new_key: default

"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_type_implementation_with_interfaces(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
type_implementations:
    impl:
        type: test_type
        node_ref: test_node
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_implementation_no_ref(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
relationship_implementations:
    impl:
        type: test_relationship
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_no_derived_from(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
relationship_implementations:
    impl:
        node_ref: test_node
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)

    def test_relationship_properties_non_single_default_value(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            - prop_with_bad_default: 1
              prop2_with_bad_default: 2

    """
        self._assert_dsl_parsing_exception_error_code(
            yaml, 1, DSLParsingFormatException)
