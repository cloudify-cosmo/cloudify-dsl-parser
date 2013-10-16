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

import tempfile
import shutil
import unittest
import os
import uuid
from parser import DSLParsingException, DSLParsingFormatException, DSLParsingLogicException
from parser import parse, parse_from_file


class TestParser(unittest.TestCase):

    BASIC_APPLICATION_TEMPLATE = """
application_template:
    name: testApp
    topology:
        -   name: testNode
            type: test_type
            properties:
                key: "val"
        """

    BASIC_INTERFACE_AND_PLUGIN = """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"

plugins:
    test_plugin:
        properties:
            interface: "test_interface1"
            url: "http://test_url.zip"
            """

    BASIC_TYPE = """
types:
    test_type:
        interfaces:
            -   test_interface1
        properties:
            install_agent: 'false'
            """

    MINIMAL_APPLICATION_TEMPLATE = BASIC_APPLICATION_TEMPLATE + """
types:
    test_type: {}
    """

    APPLICATION_TEMPLATE = BASIC_APPLICATION_TEMPLATE + BASIC_INTERFACE_AND_PLUGIN + BASIC_TYPE



    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)

    def make_yaml_file_with_name(self, content, filename):
        filename_path = os.path.join(self._temp_dir, filename)
        with open(filename_path, 'w') as f:
            f.write(content)
        return filename_path

    def make_yaml_file(self, content):
        filename = 'tempfile{0}.yaml'.format(uuid.uuid4())
        return self.make_yaml_file_with_name(content, filename)

    def create_yaml_with_imports(self, contents):
        yaml = """
imports:"""
        for content in contents:
            filename = self.make_yaml_file(content)
            yaml += """
    -   {0}""".format(filename)
        return yaml

    def assert_dsl_parsing_exception_error_code(self, dsl, expected_error_code, exception_type=DSLParsingException):
        try:
            parse(dsl)
            self.fail()
        except exception_type, ex:
            self.assertEquals(expected_error_code, ex.err_code)

    def test_empty_dsl(self):
        self.assert_dsl_parsing_exception_error_code('', 0, DSLParsingFormatException)

    def test_illegal_yaml_dsl(self):
        yaml = """
interfaces:
    test_interface:
        -   item1:
    -   bad_format
        """
        self.assert_dsl_parsing_exception_error_code(yaml, -1, DSLParsingFormatException)

    def test_no_application_template(self):
        yaml = """
interfaces:
    test_interface2:
        operations:
            -   "install"
            -   "terminate"
            """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_no_application_template_name(self):
        yaml = """
application_template:
    topology:
        -   name: testNode
            type: test_type
            properties:
                key: "val"
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_illegal_first_level_property(self):
        yaml = """
application_template:
    topology:
        -   name: testNode
            type: test_type
            properties:
                key: "val"

illegal_property:
    illegal_sub_property: "some_value"
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_no_type_definition(self):
        self.assert_dsl_parsing_exception_error_code(self.BASIC_APPLICATION_TEMPLATE, 7, DSLParsingLogicException)

    def test_node_without_name(self):
        yaml = """
application_template:
    name: testApp
    topology:
        -   type: test_type
            properties:
                key: "val"
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_node_without_type_declaration(self):
        yaml = """
application_template:
    name: testApp
    topology:
        -   name: testNode
            properties:
                key: "val"
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_single_node_application_template(self):
        result = parse(self.MINIMAL_APPLICATION_TEMPLATE)
        self.assertEquals('testApp', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('testApp.testNode', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])

    def test_type_without_interface(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE
        result = parse(yaml)
        self.assertEquals('testApp', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('testApp.testNode', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])


    def test_explicit_interface_with_missing_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "missing_plugin"
        properties:
            install_agent: 'false'
"""
        self.assert_dsl_parsing_exception_error_code(yaml, 10, DSLParsingLogicException)

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
        self.assert_dsl_parsing_exception_error_code(yaml, 9, DSLParsingLogicException)

    def test_interface_with_no_operations(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_interface_with_empty_operations_list(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
interfaces:
    test_interface1:
        operations:
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_import_from_path(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_APPLICATION_TEMPLATE])
        result = parse(yaml)
        self.assertEquals('testApp', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('testApp.testNode', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])

    def test_type_with_single_explicit_interface_and_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
        properties:
            install_agent: 'false'
            """

        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])

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
        self.assert_dsl_parsing_exception_error_code(yaml, 6, DSLParsingLogicException)


    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
                some_other_property: "meh"

            """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1:
                    explicit_plugin1: "test_plugin1"
                    explicit_plugin2: "test_plugin2"
            """
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


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
        self.assert_dsl_parsing_exception_error_code(yaml, 11, DSLParsingLogicException)

    def test_implicit_interface_with_ambiguous_matches(self):
        yaml = self.create_yaml_with_imports([self.APPLICATION_TEMPLATE]) + """
plugins:
    other_test_plugin:
        properties:
            interface: "test_interface1"
            url: "http://other_test_url.zip"
"""
        self.assert_dsl_parsing_exception_error_code(yaml, 12, DSLParsingLogicException)

    def test_type_with_single_implicit_interface_and_plugin(self):
        yaml = self.APPLICATION_TEMPLATE
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])

    def test_dsl_with_explicit_interface_mapped_to_two_plugins(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_INTERFACE_AND_PLUGIN + """
types:
    test_type:
        interfaces:
            -   test_interface1:
                    -   "test_plugin"
                    -   "test_plugin2"
        properties:
            install_agent: 'false'
"""
        self.assert_dsl_parsing_exception_error_code(yaml, 1, DSLParsingFormatException)


    def test_dsl_with_type_with_both_explicit_and_implicit_interfaces_declarations(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
            -   test_interface2

interfaces:
    test_interface2:
        operations:
            -   "start"
            -   "shutdown"

plugins:
    other_test_plugin:
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
"""
        result = parse(yaml)
        node = result['nodes'][0]

        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])

        plugin_props = node['plugins']['other_test_plugin']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('other_test_plugin', operations['start'])
        self.assertEquals('other_test_plugin', operations['test_interface2.start'])
        self.assertEquals('other_test_plugin', operations['shutdown'])
        self.assertEquals('other_test_plugin', operations['test_interface2.shutdown'])


    def test_dsl_with_interface_without_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + self.BASIC_TYPE + """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"
        """
        self.assert_dsl_parsing_exception_error_code(yaml, 5, DSLParsingLogicException)


    def test_merge_plugins_and_interfaces_imports(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
plugins:
    other_test_plugin:
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
        result = parse(yaml)
        node = result['nodes'][0]

        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])

        plugin_props = node['plugins']['other_test_plugin']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('other_test_plugin', operations['start'])
        self.assertEquals('other_test_plugin', operations['test_interface2.start'])
        self.assertEquals('other_test_plugin', operations['shutdown'])
        self.assertEquals('other_test_plugin', operations['test_interface2.shutdown'])

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
        self.assert_dsl_parsing_exception_error_code(yaml, 3, DSLParsingLogicException)

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
        self.assert_dsl_parsing_exception_error_code(yaml, 4, DSLParsingLogicException)


    def test_recursive_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}""".format(mid_file_name)
        result = parse(top_level_yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])


    def test_recursive_imports_with_inner_circular(self):
        bottom_level_yaml = """
imports:
    -   {0}/mid_level.yaml
        """.format(self._temp_dir) + self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file_with_name(mid_level_yaml, 'mid_level.yaml')

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}""".format(mid_file_name)

        self.assert_dsl_parsing_exception_error_code(top_level_yaml, 8, DSLParsingLogicException)

    def test_parse_dsl_from_file(self):
        filename = self.make_yaml_file(self.MINIMAL_APPLICATION_TEMPLATE)
        result = parse_from_file(filename)
        self.assertEquals('testApp', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('testApp.testNode', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])

#     def test_recursive_imports_with_complete_circle(self):
#         bottom_level_yaml = """
# imports:
#     -   top_level.yaml
#
# types:
#     test_type:
#         interfaces:
#             -   test_interface1
#             """
#         bottom_file_name = self.make_yaml_file(bottom_level_yaml)
#
#         mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
# imports:
#     -   {0}""".format(bottom_file_name)
#         mid_file_name = self.make_yaml_file(mid_level_yaml)
#
#         top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
# imports:
#     -   {0}""".format(mid_file_name)
#                                             #'mid_level.yaml'
#         self.assert_dsl_parsing_exception_error_code(top_level_yaml, 8, DSLParsingLogicException)


#test for diamond
#tests for non-existent dsl file path?
#test for relative import