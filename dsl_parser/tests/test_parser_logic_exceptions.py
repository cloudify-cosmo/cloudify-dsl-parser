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
from dsl_parser.parser import DSLParsingLogicException, parse_from_file
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestParserLogicExceptions(AbstractTestParser):

    def test_no_type_definition(self):
        self._assert_dsl_parsing_exception_error_code(self.BASIC_APPLICATION_TEMPLATE, 7, DSLParsingLogicException)

    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "missing_plugin"
        properties:
            install_agent: 'false'
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 10, DSLParsingLogicException)

    def test_missing_interface_definition(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   missing_interface: "test_plugin2"
        properties:
            install_agent: 'false'

plugins:
    test_plugin2:
        properties:
            interface: "missing_interface"
            url: "http://test_url2.zip"
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 9, DSLParsingLogicException)

    def test_type_with_interface_with_explicit_illegal_plugin(self):
        #testing to see what happens when the plugin which is explicitly declared for an interface is in fact
        #a plugin which doesn't implement the said interface (even if it supports another interface with same
        # name operations)
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
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
        yaml = self.create_yaml_with_imports([self.APPLICATION_TEMPLATE]) + """
plugins:
    other_test_plugin:
        properties:
            interface: "test_interface1"
            url: "http://other_test_url.zip"
"""
        self._assert_dsl_parsing_exception_error_code(yaml, 12, DSLParsingLogicException)

    def test_dsl_with_interface_without_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_TYPE + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 5, DSLParsingLogicException)

    def test_merge_non_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
application_template:
    name: testApp2
    topology:
        -   name: testNode2
            type: test_type
            properties:
                key: "val"
        """
        self._assert_dsl_parsing_exception_error_code(yaml, 3, DSLParsingLogicException)

    def test_illegal_merge_on_mergeable_properties_on_import(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}""".format(mid_file_name)

        ex = self._assert_dsl_parsing_exception_error_code(top_level_yaml, 8, DSLParsingLogicException)
        expected_circular_path = [mid_file_name, bottom_file_name, mid_file_name]
        self.assertEquals(expected_circular_path, ex.circular_path)

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

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}""".format(mid_file_name)
        top_file_name = self.make_file_with_name(top_level_yaml, 'top_level.yaml')
        ex = self._assert_dsl_parsing_exception_error_code(top_file_name, 8, DSLParsingLogicException, parse_from_file)
        expected_circular_path = [top_file_name, mid_file_name, bottom_file_name, top_file_name]
        self.assertEquals(expected_circular_path, ex.circular_path)

    def test_type_derive_non_from_none_existing(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
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