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
        self.assertEquals('test_app', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_app.test_node', node['id'])
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
        self.assertEquals(True, node['plugins']['test_plugin']['agent_plugin'])
        plugin_props = node['plugins']['test_plugin']['properties']
        self.assertEquals('test_interface1', plugin_props['interface'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        operations = node['operations']
        self.assertEquals('test_plugin', operations['install'])
        self.assertEquals('test_plugin', operations['test_interface1.install'])
        self.assertEquals('test_plugin', operations['terminate'])
        self.assertEquals('test_plugin', operations['test_interface1.terminate'])

    def test_type_with_single_explicit_interface_and_plugin(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + self.BASIC_INTERFACE_AND_PLUGIN + """
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
        yaml = self.APPLICATION_TEMPLATE_WITH_INTERFACES_AND_PLUGINS
        result = parse(yaml)
        self._assert_application_template(result)

    def test_dsl_with_type_with_both_explicit_and_implicit_interfaces_declarations(self):
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
plugins:
    other_test_plugin:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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
            policy: "bottom clojure policy1"
    rules:
        rule1:
            message: "bottom rule1"
            rule: "bottom clojure rule1"
        """

        bottom_file_name = self.make_yaml_file(bottom_level_yaml)
        mid_level_yaml = """
policies:
    types:
        policy2:
            message: "mid policy2"
            policy: "mid clojure policy2"
        policy3:
            message: "mid policy3"
            policy: "mid clojure policy3"
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)
        top_level_yaml = """
policies:
    rules:
        rule2:
            message: "top rule2"
            rule: "top clojure rule2"
        rule3:
            message: "top rule3"
            rule: "top clojure rule3"
imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals(3, len(result['policies_events']))
        self.assertEquals(3, len(result['rules']))
        self.assertEquals('bottom policy1', result['policies_events']['policy1']['message'])
        self.assertEquals('bottom clojure policy1', result['policies_events']['policy1']['policy'])
        self.assertEquals('mid policy2', result['policies_events']['policy2']['message'])
        self.assertEquals('mid clojure policy2', result['policies_events']['policy2']['policy'])
        self.assertEquals('mid policy3', result['policies_events']['policy3']['message'])
        self.assertEquals('mid clojure policy3', result['policies_events']['policy3']['policy'])
        self.assertEquals('bottom rule1', result['rules']['rule1']['message'])
        self.assertEquals('bottom clojure rule1', result['rules']['rule1']['rule'])
        self.assertEquals('top rule2', result['rules']['rule2']['message'])
        self.assertEquals('top clojure rule2', result['rules']['rule2']['rule'])
        self.assertEquals('top rule3', result['rules']['rule3']['message'])
        self.assertEquals('top clojure rule3', result['rules']['rule3']['rule'])

    def test_recursive_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
imports:
    -   {0}
    -   {1}""".format(mid_file_name, mid_file_name2)
        result = parse(top_level_yaml)
        self._assert_application_template(result)

    def test_node_get_type_properties_including_overriding_properties(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        workflows: {}
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_type_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref', 'radial_file.radial')

        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            workflows: {}
    """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_instance_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref', 'radial_file.radial')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
            workflows:
                install:
                    radial: "my custom radial"
                uninstall:
                    ref: {0}""".format(ref_alias)

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

        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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

        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
    test_plugin3:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
        properties:
            interface: "test_interface3"
            url: "http://test_url3.zip"
    test_plugin4:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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
        yaml = self.create_yaml_with_imports([self.BASIC_APPLICATION_TEMPLATE_SECTION, self.BASIC_INTERFACE_AND_PLUGIN]) + """
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
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
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

    def test_plugins_derived_from_field(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        interfaces:
            -   test_interface1: "test_plugin1"
            -   test_interface2: "test_plugin2"

interfaces:
    test_interface1:
        operations:
            -   "install"
    test_interface2:
        operations:
            -   "install"

plugins:
    test_plugin1:
        derived_from: "cloudify.tosca.artifacts.agent_plugin"
        properties:
            interface: "test_interface1"
            url: "http://test_url1.zip"
    test_plugin2:
        derived_from: "cloudify.tosca.artifacts.remote_plugin"
        properties:
            interface: "test_interface2"
            url: "http://test_url2.zip"
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals(True, node['plugins']['test_plugin1']['agent_plugin'])
        self.assertEquals(False, node['plugins']['test_plugin2']['agent_plugin'])

    def test_relative_path_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_INTERFACE_AND_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
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
            policy: "custom clojure code"
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom clojure code', result['policies_events']['custom_policy']['policy'])

    def test_top_level_policies_with_ref(self):
        ref_alias = 'ref_alias'
        clojure_file_path = self.make_file_with_name('custom clojure code', 'clojure_file.clj')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        custom_policy:
            message: "custom message"
            ref: {0}
            """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(clojure_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom clojure code', result['policies_events']['custom_policy']['policy'])

    def test_top_level_policies_with_both_ref_and_inline_policy(self):
        ref_alias = 'ref_alias'
        clojure_file_path = self.make_file_with_name('custom clojure code 2', 'clojure_file.clj')

        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    types:
        custom_policy:
            message: "custom message"
            policy: "custom clojure code"
        custom_policy2:
            message: "custom message 2"
            ref: "{0}"
        """.format(ref_alias)
        result = parse(yaml, {'{0}'.format(ref_alias): '{0}'.format(clojure_file_path)})
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['policies_events']['custom_policy']['message'])
        self.assertEquals('custom clojure code', result['policies_events']['custom_policy']['policy'])
        self.assertEquals('custom message 2', result['policies_events']['custom_policy2']['message'])
        self.assertEquals('custom clojure code 2', result['policies_events']['custom_policy2']['policy'])

    def test_top_level_rules(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
policies:
    rules:
        custom_rule:
            message: "custom message"
            rule: "custom clojure code"
        custom_rule2:
            message: "custom message 2"
            rule: "custom clojure code 2"
        """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        self.assertEquals('custom message', result['rules']['custom_rule']['message'])
        self.assertEquals('custom clojure code', result['rules']['custom_rule']['rule'])
        self.assertEquals('custom message 2', result['rules']['custom_rule2']['message'])
        self.assertEquals('custom clojure code 2', result['rules']['custom_rule2']['rule'])

    def test_instance_empty_policies(self):
        yaml = self.MINIMAL_APPLICATION_TEMPLATE + """
                policies: {}
                """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_type_empty_policies(self):
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies: {}
                """
        result = parse(yaml)
        self._assert_minimal_application_template(result)

    def test_instance_policies(self):
        yaml = self.POLICIES_SECTION + self.MINIMAL_APPLICATION_TEMPLATE + """
            policies:
                test_policy:
                    rules:
                        -   type: "test_rule"
                            properties:
                                state: "custom state"
                                value: "custom value"
                """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        node_rule = node['policies']['test_policy']['rules'][0]
        self.assertEquals('test_rule', node_rule['type'])
        self.assertEquals('custom state', node_rule['properties']['state'])
        self.assertEquals('custom value', node_rule['properties']['value'])
        #verifying the top-level policies section in the response also contains the same values
        self.assertDictEqual(node['policies'], result['policies']['test_app.test_node'])

    def test_type_policies(self):
        yaml = self.POLICIES_SECTION + self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        policies:
            test_policy:
                rules:
                    -   type: "test_rule"
                        properties:
                            state: "custom state"
                            value: "custom value"
                """
        result = parse(yaml)
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        node_rule = node['policies']['test_policy']['rules'][0]
        self.assertEquals('test_rule', node_rule['type'])
        self.assertEquals('custom state', node_rule['properties']['state'])
        self.assertEquals('custom value', node_rule['properties']['value'])
        #verifying the top-level policies section in the response also contains the same values
        self.assertDictEqual(node['policies'], result['policies']['test_app.test_node'])

    def test_type_policies_recursive_inheritance(self):
        #policies 1,5,6 will come from each type separately,
        #2 is a direct override, 3 is an indirect override, and 4 is a double override
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        derived_from: "test_type_parent"
        policies:
            policy1:
                rules:
                    -   type: "rule1"
                        properties:
                            state: "state1"
                            value: "value1"
            policy2:
                rules:
                    -   type: "rule2"
                        properties:
                            state: "state2"
                            value: "value2"
            policy3:
                rules:
                    -   type: "rule3"
                        properties:
                            state: "state3"
                            value: "value3"
            policy4:
                rules:
                    -   type: "rule4"
                        properties:
                            state: "state4"
                            value: "value4"

    test_type_parent:
        derived_from: "test_type_grandparent"
        policies:
            policy2:
                rules:
                    -   type: "parent_rule2"
                        properties:
                            state: "parent_state2"
                            value: "parent_value2"
            policy4:
                rules:
                    -   type: "parent_rule4"
                        properties:
                            state: "parent_state4"
                            value: "parent_value4"
            policy5:
                rules:
                    -   type: "parent_rule5"
                        properties:
                            state: "parent_state5"
                            value: "parent_value5"


    test_type_grandparent:
        policies:
            policy3:
                rules:
                    -   type: "grandparent_rule3"
                        properties:
                            state: "grandparent_state3"
                            value: "grandparent_value3"
            policy4:
                rules:
                    -   type: "grandparent_rule4"
                        properties:
                            state: "grandparent_state4"
                            value: "grandparent_value4"
            policy6:
                rules:
                    -   type: "grandparent_rule6"
                        properties:
                            state: "grandparent_state6"
                            value: "grandparent_value6"

policies:
    types:
        policy1:
            message: "policy1 message"
            policy: "policy1 code"
        policy2:
            message: "policy2 message"
            policy: "policy2 code"
        policy3:
            message: "policy3 message"
            policy: "policy3 code"
        policy4:
            message: "policy4 message"
            policy: "policy4 code"
        policy5:
            message: "policy5 message"
            policy: "policy5 code"
        policy6:
            message: "policy6 message"
            policy: "policy6 code"

    rules:
        rule1:
            message: "rule1 message"
            rule: "rule1 code"
        rule2:
            message: "rule2 message"
            rule: "rule2 code"
        rule3:
            message: "rule3 message"
            rule: "rule3 code"
        rule4:
            message: "rule4 message"
            rule: "rule4 code"
        parent_rule2:
            message: "parent_rule2 message"
            rule: "parent_rule2 code"
        parent_rule4:
            message: "parent_rule4 message"
            rule: "parent_rule4 code"
        parent_rule5:
            message: "parent_rule5 message"
            rule: "parent_rule5 code"
        grandparent_rule3:
            message: "grandparent_rule3 message"
            rule: "grandparent_rule3 code"
        grandparent_rule4:
            message: "grandparent_rule4 message"
            rule: "grandparent_rule4 code"
        grandparent_rule6:
            message: "grandparent_rule6 message"
            rule: "grandparent_rule6 code"
            """

        result = parse(yaml)
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        node_policies = node['policies']
        self.assertEquals(6, len(node_policies))
        self.assertEquals('rule1', node_policies['policy1']['rules'][0]['type'])
        self.assertEquals('rule2', node_policies['policy2']['rules'][0]['type'])
        self.assertEquals('rule3', node_policies['policy3']['rules'][0]['type'])
        self.assertEquals('rule4', node_policies['policy4']['rules'][0]['type'])
        self.assertEquals('parent_rule5', node_policies['policy5']['rules'][0]['type'])
        self.assertEquals('grandparent_rule6', node_policies['policy6']['rules'][0]['type'])
        #verifying the top-level policies section in the response also contains the same values
        self.assertDictEqual(node['policies'], result['policies']['test_app.test_node'])

    def test_type_and_node_policies_recursive_inheritance(self):
        #policies 1,5,6 will come from each type separately,
        #2 is a direct override, 3 is an indirect override, and 4 is a double override
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
            policies:
                policy1:
                    rules:
                        -   type: "rule1"
                            properties:
                                state: "state1"
                                value: "value1"
                policy2:
                    rules:
                        -   type: "rule2"
                            properties:
                                state: "state2"
                                value: "value2"
                policy3:
                    rules:
                        -   type: "rule3"
                            properties:
                                state: "state3"
                                value: "value3"
                policy4:
                    rules:
                        -   type: "rule4"
                            properties:
                                state: "state4"
                                value: "value4"
types:
    test_type:
        derived_from: "test_type_parent"
        policies:
            policy2:
                rules:
                    -   type: "parent_rule2"
                        properties:
                            state: "parent_state2"
                            value: "parent_value2"
            policy4:
                rules:
                    -   type: "parent_rule4"
                        properties:
                            state: "parent_state4"
                            value: "parent_value4"
            policy5:
                rules:
                    -   type: "parent_rule5"
                        properties:
                            state: "parent_state5"
                            value: "parent_value5"

    test_type_parent:
        policies:
            policy3:
                rules:
                    -   type: "grandparent_rule3"
                        properties:
                            state: "grandparent_state3"
                            value: "grandparent_value3"
            policy4:
                rules:
                    -   type: "grandparent_rule4"
                        properties:
                            state: "grandparent_state4"
                            value: "grandparent_value4"
            policy6:
                rules:
                    -   type: "grandparent_rule6"
                        properties:
                            state: "grandparent_state6"
                            value: "grandparent_value6"

policies:
    types:
        policy1:
            message: "policy1 message"
            policy: "policy1 code"
        policy2:
            message: "policy2 message"
            policy: "policy2 code"
        policy3:
            message: "policy3 message"
            policy: "policy3 code"
        policy4:
            message: "policy4 message"
            policy: "policy4 code"
        policy5:
            message: "policy5 message"
            policy: "policy5 code"
        policy6:
            message: "policy6 message"
            policy: "policy6 code"

    rules:
        rule1:
            message: "rule1 message"
            rule: "rule1 code"
        rule2:
            message: "rule2 message"
            rule: "rule2 code"
        rule3:
            message: "rule3 message"
            rule: "rule3 code"
        rule4:
            message: "rule4 message"
            rule: "rule4 code"
        parent_rule2:
            message: "parent_rule2 message"
            rule: "parent_rule2 code"
        parent_rule4:
            message: "parent_rule4 message"
            rule: "parent_rule4 code"
        parent_rule5:
            message: "parent_rule5 message"
            rule: "parent_rule5 code"
        grandparent_rule3:
            message: "grandparent_rule3 message"
            rule: "grandparent_rule3 code"
        grandparent_rule4:
            message: "grandparent_rule4 message"
            rule: "grandparent_rule4 code"
        grandparent_rule6:
            message: "grandparent_rule6 message"
            rule: "grandparent_rule6 code"
            """

        result = parse(yaml)
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        node_policies = node['policies']
        self.assertEquals(6, len(node_policies))
        self.assertEquals('rule1', node_policies['policy1']['rules'][0]['type'])
        self.assertEquals('rule2', node_policies['policy2']['rules'][0]['type'])
        self.assertEquals('rule3', node_policies['policy3']['rules'][0]['type'])
        self.assertEquals('rule4', node_policies['policy4']['rules'][0]['type'])
        self.assertEquals('parent_rule5', node_policies['policy5']['rules'][0]['type'])
        self.assertEquals('grandparent_rule6', node_policies['policy6']['rules'][0]['type'])
        #verifying the top-level policies section in the response also contains the same values
        self.assertDictEqual(node['policies'], result['policies']['test_app.test_node'])

    def test_type_policies_multiple_and_same_name_rules(self):
        #a test to verify same-name rules don't cause any problem in inheritance,
        #as well as verifying multiple rules under the same policy are inherited correctly
        yaml = self.BASIC_APPLICATION_TEMPLATE_SECTION + """
types:
    test_type:
        derived_from: "test_type_parent"
        policies:
            policy1:
                rules:
                    -   type: "rule1"
                        properties:
                            state: "state1"
                            value: "value1"
            policy2:
                rules:
                    -   type: "rule2"
                        properties:
                            state: "state2"
                            value: "value2"
                    -   type: "rule3"
                        properties:
                            state: "state3"
                            value: "value3"

    test_type_parent:
        policies:
            policy1:
                rules:
                    -   type: "rule1"
                        properties:
                            state: "parent_state2"
                            value: "parent_value2"
            policy2:
                rules:
                    -   type: "rule4"
                        properties:
                            state: "parent_state4"
                            value: "parent_value4"

policies:
    types:
        policy1:
            message: "policy1 message"
            policy: "policy1 code"
        policy2:
            message: "policy2 message"
            policy: "policy2 code"
    rules:
        rule1:
            message: "rule1 message"
            rule: "rule1 code"
        rule2:
            message: "rule2 message"
            rule: "rule2 code"
        rule3:
            message: "rule3 message"
            rule: "rule3 code"
        rule4:
            message: "rule4 message"
            rule: "rule4 code"
                """

        result = parse(yaml)
        self._assert_minimal_application_template(result)
        node = result['nodes'][0]
        node_policies = node['policies']
        self.assertEquals(2, len(node_policies))
        self.assertEquals(1, len(node_policies['policy1']['rules']))
        self.assertEquals('rule1', node_policies['policy1']['rules'][0]['type'])
        self.assertEquals('state1', node_policies['policy1']['rules'][0]['properties']['state'])
        self.assertEquals('value1', node_policies['policy1']['rules'][0]['properties']['value'])
        self.assertEquals(2, len(node_policies['policy2']['rules']))
        self.assertEquals('rule2', node_policies['policy2']['rules'][0]['type'])
        self.assertEquals('state2', node_policies['policy2']['rules'][0]['properties']['state'])
        self.assertEquals('value2', node_policies['policy2']['rules'][0]['properties']['value'])
        self.assertEquals('rule3', node_policies['policy2']['rules'][1]['type'])
        self.assertEquals('state3', node_policies['policy2']['rules'][1]['properties']['state'])
        self.assertEquals('value3', node_policies['policy2']['rules'][1]['properties']['value'])
        #verifying the top-level policies section in the response also contains the same values
        self.assertDictEqual(node['policies'], result['policies']['test_app.test_node'])