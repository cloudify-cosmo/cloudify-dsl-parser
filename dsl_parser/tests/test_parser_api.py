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

from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser.parser import parse, parse_from_file, _get_default_alias_mapping


class TestParserApi(AbstractTestParser):

    def _assert_minimal_application_template(self, result):
        self.assertEquals('testApp', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('testApp.testNode', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])

    def test_single_node_application_template(self):
        result = parse(self.MINIMAL_APPLICATION_TEMPLATE)
        self._assert_minimal_application_template(result)

    def test_type_without_interface(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_import_from_path(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_APPLICATION_TEMPLATE])
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def _assert_application_template(self, result):
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
        self._assert_application_template(result)

    def test_type_with_single_implicit_interface_and_plugin(self):
        yaml = self.APPLICATION_TEMPLATE
        result = parse(yaml)
        self._assert_application_template(result)

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
        self._assert_application_template(result)

        plugin_props = node['plugins']['other_test_plugin']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('other_test_plugin', operations['start'])
        self.assertEquals('other_test_plugin', operations['test_interface2.start'])
        self.assertEquals('other_test_plugin', operations['shutdown'])
        self.assertEquals('other_test_plugin', operations['test_interface2.shutdown'])

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
        self._assert_application_template(result)

        plugin_props = node['plugins']['other_test_plugin']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('other_test_plugin', operations['start'])
        self.assertEquals('other_test_plugin', operations['test_interface2.start'])
        self.assertEquals('other_test_plugin', operations['shutdown'])
        self.assertEquals('other_test_plugin', operations['test_interface2.shutdown'])

    def test_workflows_recursive_imports(self):
        bottom_level_yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
    install1:
        radial: "bottom radial install1"
        """

        bottom_file_name = self.make_yaml_file(bottom_level_yaml)
        mid_level_yaml = """
workflows:
    install2:
        radial: "mid radial install2"
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)
        top_level_yaml = """
workflows:
    install3:
        radial: "top radial install3"
imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals(3, len(result['workflows']))
        self.assertEquals('bottom radial install1', result['workflows']['install1'])
        self.assertEquals('mid radial install2', result['workflows']['install2'])
        self.assertEquals('top radial install3', result['workflows']['install3'])

    def test_policies_and_rules_recursive_imports(self):
        bottom_level_yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        policy1:
            message: "bottom policy1"
            policy: "bottom closure policy1"
    rules:
        rule1:
            message: "bottom rule1"
            rule: "bottom closure rule1"
        """

        bottom_file_name = self.make_yaml_file(bottom_level_yaml)
        mid_level_yaml = """
policies:
    types:
        policy2:
            message: "mid policy2"
            policy: "mid closure policy2"
        policy3:
            message: "mid policy3"
            policy: "mid closure policy3"
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)
        top_level_yaml = """
policies:
    rules:
        rule2:
            message: "top rule2"
            rule: "top closure rule2"
        rule3:
            message: "top rule3"
            rule: "top closure rule3"
imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals(3, len(result['policies_events']))
        self.assertEquals(3, len(result['rules']))
        self.assertEquals('bottom policy1', result['policies_events']['policy1']['message'])
        self.assertEquals('bottom closure policy1', result['policies_events']['policy1']['policy'])
        self.assertEquals('mid policy2', result['policies_events']['policy2']['message'])
        self.assertEquals('mid closure policy2', result['policies_events']['policy2']['policy'])
        self.assertEquals('mid policy3', result['policies_events']['policy3']['message'])
        self.assertEquals('mid closure policy3', result['policies_events']['policy3']['policy'])
        self.assertEquals('bottom rule1', result['rules']['rule1']['message'])
        self.assertEquals('bottom closure rule1', result['rules']['rule1']['rule'])
        self.assertEquals('top rule2', result['rules']['rule2']['message'])
        self.assertEquals('top closure rule2', result['rules']['rule2']['rule'])
        self.assertEquals('top rule3', result['rules']['rule3']['message'])
        self.assertEquals('top closure rule3', result['rules']['rule3']['rule'])

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
        self._assert_application_template(result)

    def test_parse_dsl_from_file(self):
        filename = self.make_yaml_file(self.MINIMAL_APPLICATION_TEMPLATE)
        result = parse_from_file(filename)
        self._assert_minimal_application_template(result)

    def test_parse_dsl_from_file_bad_path(self):
        self.assertRaises(EnvironmentError, parse_from_file, 'fake-file.yaml')

    def test_import_empty_list(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
imports: []
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_diamond_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        mid_level_yaml2 = """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name2 = self.make_yaml_file(mid_level_yaml2)

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}
    -   {1}""".format(mid_file_name, mid_file_name2)
        result = parse(top_level_yaml)
        self._assert_application_template(result)

    def test_node_get_type_properties_including_overriding_properties(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        properties:
            key: "not_val"
            key2: "val2"
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result) #this will also check property "key" = "val"
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])

    def test_alias_mapping_imports(self):
        imported_yaml = self.MINIMAL_APPLICATION_TEMPLATE
        imported_filename = self.make_yaml_file(imported_yaml)
        imported_alias = 'imported_alias'
        yaml = """
imports:
    -   {0}""".format(imported_alias)
        result = parse(yaml, {'{0}'.format(imported_alias): '{0}'.format(imported_filename)})
        self._assert_minimal_application_template(result)

    def test_default_alias_mapping_file(self):
        self.assertTrue(len(_get_default_alias_mapping()) > 0)

    def test_empty_first_level_workflows(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows: {}
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_first_level_workflows_radial(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
        install:
            radial: "my custom radial"
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals('my custom radial', result['workflows']['install'])

    def test_first_level_workflows_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('my custom radial', 'radial_file.radial')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
        install:
            ref: {0}
        """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('my custom radial', result['workflows']['install'])

    def test_first_level_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref', 'radial_file.radial')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
workflows:
        install:
            radial: "my custom radial"
        uninstall:
            ref: {0}
        """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('my custom radial', result['workflows']['install'])
        self.assertEquals('custom ref', result['workflows']['uninstall'])

    def test_type_empty_workflows(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        workflows: {}
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_type_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref', 'radial_file.radial')

        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        workflows:
            install:
                radial: "my custom radial"
            uninstall:
                ref: {0}
            """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        self.assertEquals('my custom radial', node['workflows']['install'])
        self.assertEquals('custom ref', node['workflows']['uninstall'])
        self.assertEquals(2, len(node['workflows']))

    def test_instance_empty_workflows(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
            workflows: {}
types:
    test_type: {}
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_instance_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref', 'radial_file.radial')

        yaml = self.BASIC_APPLICATION_TEMPLATE + """
            workflows:
                install:
                    radial: "my custom radial"
                uninstall:
                    ref: {0}""".format(ref_alias) + """
types:
    test_type: {}
    """

        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        self.assertEquals('my custom radial', node['workflows']['install'])
        self.assertEquals('custom ref', node['workflows']['uninstall'])
        self.assertEquals(2, len(node['workflows']))

    def test_type_workflows_recursive_inheritance(self):
        #tests for multiple-hierarchy workflows inheritance between types,
        #including back and forth switches between radial and ref overrides,
        #as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('ref install2', 'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('parent ref install5', 'radial_file2.radial')

        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        derived_from: "test_type_parent"
        workflows:
            install1:
                radial: "radial install1"
            install2:
                ref: {0}""".format(ref_alias1) + """
            install4:
                radial: "radial install4"

    test_type_parent:
        derived_from: "test_type_grandparent"
        workflows:
            install1:
                ref: "parent ref install1"
            install2:
                radial: "parent radial install2"
            install5:
                ref: {0}""".format(ref_alias2) + """
    test_type_grandparent:
        workflows:
            install1:
                radial: "grandparent radial install1"
            install2:
                ref: "grandparent ref install2"
            install3:
                radial: "grandparent radial install3"
            install4:
                ref: "grandparent ref install4"
            """

        result = parse(yaml, {
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        self.assertEquals('radial install1', node['workflows']['install1'])
        self.assertEquals('ref install2', node['workflows']['install2'])
        self.assertEquals('grandparent radial install3', node['workflows']['install3'])
        self.assertEquals('radial install4', node['workflows']['install4'])
        self.assertEquals('parent ref install5', node['workflows']['install5'])
        self.assertEquals(5, len(node['workflows']))

    def test_type_and_node_workflows_recursive_inheritance(self):
        #tests for multiple-hierarchy workflows inheritance between types and an instance,
        #including back and forth switches between radial and ref overrides,
        #as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('node ref install2', 'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('ref install5', 'radial_file2.radial')

        yaml = self.BASIC_APPLICATION_TEMPLATE + """
            workflows:
                install1:
                    radial: "node radial install1"
                install2:
                    ref: {0}""".format(ref_alias1) + """
                install4:
                    radial: "node radial install4"
types:
    test_type:
        derived_from: "test_type_parent"
        workflows:
            install1:
                ref: "ref install1"
            install2:
                radial: "radial install2"
            install5:
                ref: {0}""".format(ref_alias2) + """

    test_type_parent:
        workflows:
            install1:
                radial: "parent radial install1"
            install2:
                ref: "parent ref install2"
            install3:
                radial: "parent radial install3"
            install4:
                ref: "parent ref install4"
            """

        result = parse(yaml, {
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        self.assertEquals('node radial install1', node['workflows']['install1'])
        self.assertEquals('node ref install2', node['workflows']['install2'])
        self.assertEquals('parent radial install3', node['workflows']['install3'])
        self.assertEquals('node radial install4', node['workflows']['install4'])
        self.assertEquals('ref install5', node['workflows']['install5'])
        self.assertEquals(5, len(node['workflows']))

    def test_type_properties_derivation(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        properties:
            key: "not_val"
            key2: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            key: "val1_parent"
            key2: "val2_parent"
            key3: "val3_parent"
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result) #this will also check property "key" = "val"
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_parent', node['properties']['key3'])

    def test_type_properties_recursive_derivation(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE + """
types:
    test_type:
        properties:
            key: "not_val"
            key2: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            key: "val_parent"
            key2: "val2_parent"
            key4: "val4_parent"
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        properties:
            key: "val1_grandparent"
            key2: "val2_grandparent"
            key3: "val3_grandparent"
        derived_from: "test_type_grandgrandparent"

    test_type_grandgrandparent: {}
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result) #this will also check property "key" = "val"
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_grandparent', node['properties']['key3'])
        self.assertEquals('val4_parent', node['properties']['key4'])

    def test_type_interface_derivation(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
types:
    test_type:
        interfaces:
            -   test_interface1
            -   test_interface2: test_plugin2
            -   test_interface3
        derived_from: "test_type_parent"

    test_type_parent:
        interfaces:
            -   test_interface1: nop-plugin
            -   test_interface2
            -   test_interface3
            -   test_interface4

interfaces:
    test_interface2:
        operations:
            -   "start"
            -   "stop"
    test_interface3:
        operations:
            -   "op1"
    test_interface4:
        operations:
            -   "op2"

plugins:
    test_plugin2:
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
    test_plugin3:
        properties:
            interface: "test_interface3"
            url: "http://test_url3.zip"
    test_plugin4:
        properties:
            interface: "test_interface4"
            url: "http://test_url4.zip"
    """

        result = parse(yaml)
        self._assert_application_template(result)
        node = result['nodes'][0]
        plugin_props = node['plugins']['test_plugin2']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals(12, len(operations))
        self.assertEquals('test_plugin2', operations['start'])
        self.assertEquals('test_plugin2', operations['test_interface2.start'])
        self.assertEquals('test_plugin2', operations['stop'])
        self.assertEquals('test_plugin2', operations['test_interface2.stop'])
        self.assertEquals('test_plugin3', operations['op1'])
        self.assertEquals('test_plugin3', operations['test_interface3.op1'])
        self.assertEquals('test_plugin4', operations['op2'])
        self.assertEquals('test_plugin4', operations['test_interface4.op2'])
        self.assertEquals(4, len(node['plugins']))

    def test_type_interface_recursive_derivation(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
types:
    test_type:
        interfaces:
            -   test_interface1
        derived_from: "test_type_parent"

    test_type_parent:
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        interfaces:
            -   test_interface1: "non_plugin"
            -   test_interface2: "test_plugin2"

interfaces:
    test_interface2:
        operations:
            -   "start"
            -   "stop"

plugins:
    test_plugin2:
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
        """

        result = parse(yaml)
        self._assert_application_template(result)
        node = result['nodes'][0]
        plugin_props = node['plugins']['test_plugin2']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals(8, len(operations))
        self.assertEquals('test_plugin2', operations['start'])
        self.assertEquals('test_plugin2', operations['test_interface2.start'])
        self.assertEquals('test_plugin2', operations['stop'])
        self.assertEquals('test_plugin2', operations['test_interface2.stop'])
        self.assertEquals(2, len(node['plugins']))

    def test_two_explicit_interfaces_with_same_operation_name(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE, self.BASIC_INTERFACE_AND_PLUGIN]) + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin"
            -   test_interface2: "other_test_plugin"

interfaces:
    test_interface2:
        operations:
            -   "install"
            -   "shutdown"

plugins:
    other_test_plugin:
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])
        plugin_props = node['plugins']['other_test_plugin']['properties']
        self.assertEquals('test_interface2', plugin_props['interface'])
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('other_test_plugin', operations['test_interface2.install'])
        self.assertEquals('other_test_plugin', operations['shutdown'])
        self.assertEquals('other_test_plugin', operations['test_interface2.shutdown'])
        self.assertEquals(6, len(operations))

    def test_relative_path_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE + """
imports:
    -   {0}""".format(mid_file_name)
        result = parse(top_level_yaml)
        self._assert_application_template(result)

    def test_empty_top_level_policies(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies: {}
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals(0, len(result['policies_events']))
        self.assertEquals(0, len(result['rules']))

    def test_empty_top_level_policies_events_and_rules(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types: {}
    rules: {}
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals(0, len(result['policies_events']))
        self.assertEquals(0, len(result['rules']))

    def test_top_level_policies_with_inline_policy(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom closure code"
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom closure code', result['policies_events']['custom_policy']['policy'])

    def test_top_level_policies_with_ref(self):
        ref_alias = 'ref_alias'
        closure_file_path = self.make_file_with_name('custom closure code', 'closure_file.clj')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        custom_policy:
            message: "custom message"
            ref: {0}
            """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(closure_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom closure code', result['policies_events']['custom_policy']['policy'])

    def test_top_level_policies_with_both_ref_and_inline_policy(self):
        ref_alias = 'ref_alias'
        closure_file_path = self.make_file_with_name('custom closure code 2', 'closure_file.clj')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom closure code"
        custom_policy2:
            message: "custom message 2"
            ref: "{0}"
        """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(closure_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom closure code', result['policies_events']['custom_policy']['policy'])
        self.assertEquals('custom message 2', result['policies_events']['custom_policy2']['message'])
        self.assertEquals('custom closure code 2', result['policies_events']['custom_policy2']['policy'])

    def test_top_level_rules(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    rules:
        custom_rule:
            message: "custom message"
            rule: "custom closure code"
        custom_rule2:
            message: "custom message 2"
            rule: "custom closure code 2"
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['rules']['custom_rule']['message'])
        self.assertEquals('custom closure code', result['rules']['custom_rule']['rule'])
        self.assertEquals('custom message 2', result['rules']['custom_rule2']['message'])
        self.assertEquals('custom closure code 2', result['rules']['custom_rule2']['rule'])


# policies = same as node policies + inheritance
# node/type policies/rules ref stuff from policies section