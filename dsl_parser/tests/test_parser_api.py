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

from urllib import pathname2url
import os

from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser.parser import parse, parse_from_path, parse_from_url
from dsl_parser.parser import TYPE_HIERARCHY


def op_struct(plugin_name, operation_mapping, properties=None):
    result = {'plugin': plugin_name, 'operation': operation_mapping}
    if properties:
        result['properties'] = properties
    return result


class TestParserApi(AbstractTestParser):
    def _assert_minimal_blueprint(self, result, expected_type='test_type',
                                  expected_declared_type='test_type'):
        self.assertEquals('test_app', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals(expected_type, node['type'])
        self.assertEquals(expected_declared_type, node['declared_type'])
        self.assertEquals('val', node['properties']['key'])
        self.assertEquals(1, node['instances']['deploy'])

    def _get_plugin_to_install_from_node(self, node, plugin_name):
        return next(plugin for plugin in node['plugins_to_install']
                    if plugin['name'] == plugin_name)

    def test_single_node_blueprint(self):
        result = parse(self.MINIMAL_BLUEPRINT)
        self._assert_minimal_blueprint(result)

    def test_type_without_interface(self):
        yaml = self.MINIMAL_BLUEPRINT
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_import_from_path(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT])
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def _assert_blueprint(self, result):
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        operations = node['operations']
        self.assertEquals(op_struct('test_plugin', 'install'),
                          operations['install'])
        self.assertEquals(op_struct('test_plugin', 'install'),
                          operations['test_interface1.install'])
        self.assertEquals(op_struct('test_plugin', 'terminate'),
                          operations['terminate'])
        self.assertEquals(op_struct('test_plugin', 'terminate'),
                          operations['test_interface1.terminate'])

    def test_type_with_single_explicit_interface_and_plugin(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
                - start: test_plugin.start
        properties:
            - install_agent: 'false'
            - key
            - number: 80
            - boolean: false
            - complex:
                key1: value1
                key2: value2
            """

        result = parse(yaml)
        self._assert_blueprint(result)

    def test_type_with_single_implicit_interface_and_plugin(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS
        result = parse(yaml)
        self._assert_blueprint(result)

    def test_dsl_with_type_with_operation_mappings(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
            test_interface2:
                - start: other_test_plugin.start
                - shutdown: other_test_plugin.shutdown

plugins:
    other_test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
"""
        result = parse(yaml)
        node = result['nodes'][0]
        self._assert_blueprint(result)

        plugin_props = node['plugins']['other_test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('other_test_plugin', plugin_props['name'])
        operations = node['operations']
        self.assertEquals(op_struct('other_test_plugin', 'start'),
                          operations['start'])
        self.assertEquals(op_struct('other_test_plugin', 'start'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['test_interface2.shutdown'])

    def test_merge_plugins_and_interfaces_imports(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
plugins:
    other_test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
            test_interface2:
                - start: other_test_plugin.start
                - shutdown: other_test_plugin.shutdown
        """
        result = parse(yaml)
        node = result['nodes'][0]
        self._assert_blueprint(result)

        plugin_props = node['plugins']['other_test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('other_test_plugin', plugin_props['name'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        operations = node['operations']
        self.assertEquals(op_struct('other_test_plugin', 'start'),
                          operations['start'])
        self.assertEquals(op_struct('other_test_plugin', 'start'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['test_interface2.shutdown'])

    def test_workflows_recursive_imports(self):
        bottom_level_yaml = self.MINIMAL_BLUEPRINT + """
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
        self._assert_minimal_blueprint(result)
        self.assertEquals(3, len(result['workflows']))
        self.assertEquals('bottom radial install1',
                          result['workflows']['install1'])
        self.assertEquals('mid radial install2',
                          result['workflows']['install2'])
        self.assertEquals('top radial install3',
                          result['workflows']['install3'])

    def test_recursive_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_parse_dsl_from_file(self):
        filename = self.make_yaml_file(self.MINIMAL_BLUEPRINT)
        result = parse_from_path(filename)
        self._assert_minimal_blueprint(result)

    def test_parse_dsl_from_url(self):
        filename_url = self.make_yaml_file(self.MINIMAL_BLUEPRINT, True)
        result = parse_from_url(filename_url)
        self._assert_minimal_blueprint(result)

    def test_import_empty_list(self):
        yaml = self.MINIMAL_BLUEPRINT + """
imports: []
        """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_diamond_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        mid_level_yaml2 = """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name2 = self.make_yaml_file(mid_level_yaml2)

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}
    -   {1}""".format(mid_file_name, mid_file_name2)
        result = parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_node_get_type_properties_including_overriding_properties(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key: "not_val"
            - key2: "val2"
    """
        result = parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])

    def test_alias_mapping_imports(self):
        imported_yaml = self.MINIMAL_BLUEPRINT
        imported_filename = self.make_yaml_file(imported_yaml)
        imported_alias = 'imported_alias'
        yaml = """
imports:
    -   {0}""".format(imported_alias)
        result = parse(yaml,
                       alias_mapping_dict={'{0}'.format(imported_alias):
                                           '{0}'.format(imported_filename)})
        self._assert_minimal_blueprint(result)

    def test_alias_mapping_imports_using_path(self):
        imported_yaml = self.MINIMAL_BLUEPRINT
        imported_filename = self.make_yaml_file(imported_yaml)
        imported_alias = 'imported_alias'
        yaml = """
imports:
    -   {0}""".format(imported_alias)
        alias_path = self.make_alias_yaml_file({
            '{0}'.format(imported_alias): '{0}'.format(imported_filename)})
        result = parse(yaml, alias_mapping_url=alias_path)
        self._assert_minimal_blueprint(result)

    def test_empty_first_level_workflows(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows: {}
        """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_first_level_workflows_radial(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
        install:
            radial: "my custom radial"
        """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertEquals('my custom radial', result['workflows']['install'])

    def test_first_level_workflows_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('my custom radial',
                                                    'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
        install:
            ref: {0}
        """.format(ref_alias)
        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_blueprint(result)
        self.assertEquals('my custom radial', result['workflows']['install'])

    def test_first_level_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref',
                                                    'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
        install:
            radial: "my custom radial"
        uninstall:
            ref: {0}
        """.format(ref_alias)
        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_blueprint(result)
        self.assertEquals('my custom radial', result['workflows']['install'])
        self.assertEquals('custom ref', result['workflows']['uninstall'])

    def test_type_empty_workflows(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        workflows: {}
    """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_type_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref',
                                                    'radial_file.radial')

        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        workflows:
            install:
                radial: "my custom radial"
            uninstall:
                ref: {0}
            """.format(ref_alias)
        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('my custom radial', node['workflows']['install'])
        self.assertEquals('custom ref', node['workflows']['uninstall'])
        self.assertEquals(2, len(node['workflows']))

    def test_instance_empty_workflows(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            workflows: {}
    """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_instance_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref',
                                                    'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
            workflows:
                install:
                    radial: "my custom radial"
                uninstall:
                    ref: {0}""".format(ref_alias)

        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('my custom radial', node['workflows']['install'])
        self.assertEquals('custom ref', node['workflows']['uninstall'])
        self.assertEquals(2, len(node['workflows']))

    def test_relationship_empty_workflows(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflows: {}
"""
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        relationships = result['relationships']
        self.assertEquals(1, len(relationships))
        test_relationship = relationships['test_relationship']
        self.assertEquals(0, len(test_relationship['workflows']))

    def test_relationship_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref',
                                                    'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        workflows:
            unlink:
                radial: "my custom radial"
            establish:
                ref: {0}""".format(ref_alias)

        result = parse(yaml, alias_mapping_dict={ref_alias: radial_file_path})
        self._assert_minimal_blueprint(result)
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('my custom radial',
                          test_relationship['workflows']['unlink'])
        self.assertEquals('custom ref',
                          test_relationship['workflows']['establish'])
        self.assertEquals(2, len(test_relationship['workflows']))

    def test_instance_relationship_empty_workflows(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                - type: test_relationship
                  target: test_node
                  workflows: {}
relationships:
    test_relationship: {}
"""
        result = parse(yaml)
        source_node = result['nodes'][1]
        self.assertEquals(1, len(source_node['relationships']))
        node_relationship = source_node['relationships'][0]
        self.assertEquals(0, len(node_relationship['workflows']))

    def test_instance_relationship_workflows_both_radial_and_ref(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('custom ref',
                                                    'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                - type: test_relationship
                  target: test_node
                  workflows:
                      unlink:
                          radial: "my custom radial"
                      establish:
                          ref: ref_alias
relationships:
    test_relationship: {}

"""

        result = parse(yaml, alias_mapping_dict={ref_alias: radial_file_path})
        source_node = result['nodes'][1]
        self.assertEquals(1, len(source_node['relationships']))
        node_relationship = source_node['relationships'][0]
        self.assertEquals(2, len(node_relationship['workflows']))
        self.assertEquals('my custom radial',
                          node_relationship['workflows']['unlink'])
        self.assertEquals('custom ref',
                          node_relationship['workflows']['establish'])

    def test_instance_relationship_base_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                - type: cloudify.relationships.depends_on
                  target: test_node
        -   name: test_node3
            type: test_type
            relationships:
                - type: cloudify.relationships.connected_to
                  target: test_node
        -   name: test_node4
            type: test_type
            relationships:
                - type: derived_from_connected_to
                  target: test_node
        -   name: test_node5
            type: test_type
            relationships:
                - type: cloudify.relationships.contained_in
                  target: test_node
        -   name: test_node6
            type: test_type
            relationships:
                - type: derived_from_contained_in
                  target: test_node
        -   name: test_node7
            type: test_type
            relationships:
                - type: test_relationship
                  target: test_node
relationships:
    test_relationship: {}
    cloudify.relationships.depends_on: {}
    cloudify.relationships.connected_to: {}
    cloudify.relationships.contained_in: {}
    derived_from_connected_to:
        derived_from: cloudify.relationships.connected_to
    derived_from_contained_in:
        derived_from: cloudify.relationships.contained_in
"""
        result = parse(yaml)
        n2_relationship = result['nodes'][1]['relationships'][0]
        n3_relationship = result['nodes'][2]['relationships'][0]
        n4_relationship = result['nodes'][3]['relationships'][0]
        n5_relationship = result['nodes'][4]['relationships'][0]
        n6_relationship = result['nodes'][5]['relationships'][0]
        n7_relationship = result['nodes'][6]['relationships'][0]
        self.assertEquals('depends', n2_relationship['base'])
        self.assertEquals('connected', n3_relationship['base'])
        self.assertEquals('connected', n4_relationship['base'])
        self.assertEquals('contained', n5_relationship['base'])
        self.assertEquals('contained', n6_relationship['base'])
        self.assertEquals('undefined', n7_relationship['base'])

    def test_type_workflows_recursive_inheritance(self):
        # tests for multiple-hierarchy workflows inheritance between types,
        # including back and forth switches between radial and ref overrides,
        # as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('ref install2',
                                                     'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('parent ref install5',
                                                     'radial_file2.radial')
        ref_file_3 = self.make_file_with_name('some radial code',
                                              'ref_3.radial')

        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
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
                ref: "{0}"
            install2:
                radial: "parent radial install2"
            install5:
                ref: {1}""".format(ref_file_3, ref_alias2) + """
    test_type_grandparent:
        workflows:
            install1:
                radial: "grandparent radial install1"
            install2:
                ref: "{0}"
            install3:
                radial: "grandparent radial install3"
            install4:
                ref: "{1}"
            """.format(ref_file_3, ref_file_3)

        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('radial install1', node['workflows']['install1'])
        self.assertEquals('ref install2', node['workflows']['install2'])
        self.assertEquals('grandparent radial install3',
                          node['workflows']['install3'])
        self.assertEquals('radial install4', node['workflows']['install4'])
        self.assertEquals('parent ref install5', node['workflows']['install5'])
        self.assertEquals(5, len(node['workflows']))

    def test_type_and_node_workflows_recursive_inheritance(self):
        # tests for multiple-hierarchy workflows inheritance between types and
        #  an instance,
        # including back and forth switches between radial and ref overrides,
        # as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('node ref install2',
                                                     'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('ref install5',
                                                     'radial_file2.radial')
        ref_file_3 = self.make_file_with_name('some radial code',
                                              'ref_3.radial')
        ref_file_4 = self.make_file_with_name('some radial code',
                                              'ref_4.radial')

        yaml = self.BASIC_BLUEPRINT_SECTION + """
            workflows:
                install1:
                    radial: "node radial install1"
                install2:
                    ref: {0}""".format(ref_alias1) + """
                install4:
                    radial: "node radial install4"
types:
    test_type:
        properties:
            - key
        derived_from: "test_type_parent"
        workflows:
            install1:
                ref: "{0}"
            install2:
                radial: "radial install2"
            install5:
                ref: {1}""".format(ref_file_3, ref_alias2) + """

    test_type_parent:
        workflows:
            install1:
                radial: "parent radial install1"
            install2:
                ref: "{0}"
            install3:
                radial: "parent radial install3"
            install4:
                ref: "{1}"
            """.format(ref_file_4, ref_file_4)

        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('node radial install1',
                          node['workflows']['install1'])
        self.assertEquals('node ref install2',
                          node['workflows']['install2'])
        self.assertEquals('parent radial install3',
                          node['workflows']['install3'])
        self.assertEquals('node radial install4',
                          node['workflows']['install4'])
        self.assertEquals('ref install5', node['workflows']['install5'])
        self.assertEquals(5, len(node['workflows']))

    def test_relationship_workflows_recursive_inheritance(self):
        # tests for multiple-hierarchy workflows inheritance between
        # relationships, including back and forth switches between radial and
        # ref overrides, as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('ref install2',
                                                     'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('parent ref install5',
                                                     'radial_file2.radial')
        ref_file_3 = self.make_file_with_name('some radial code',
                                              'ref_3.radial')

        yaml = self.BASIC_BLUEPRINT_SECTION + """
        -   name: test_node2
            type: test_type
            relationships:
                - target: test_node
                  type: test_relationship
types:
    test_type:
        properties:
            - key: default

relationships:
    test_relationship:
        derived_from: "test_parent_relationships"
        workflows:
            install1:
                radial: "radial install1"
            install2:
                ref: {0}""".format(ref_alias1) + """
            install4:
                radial: "radial install4"

    test_parent_relationships:
        derived_from: "test_grandparent_relationships"
        workflows:
            install1:
                ref: "{0}"
            install2:
                radial: "parent radial install2"
            install5:
                ref: {1}""".format(ref_file_3, ref_alias2) + """
    test_grandparent_relationships:
        workflows:
            install1:
                radial: "grandparent radial install1"
            install2:
                ref: "{0}"
            install3:
                radial: "grandparent radial install3"
            install4:
                ref: "{1}"
            """.format(ref_file_3, ref_file_3)

        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        relationship = result['nodes'][1]['relationships'][0]
        self.assertEquals('radial install1',
                          relationship['workflows']['install1'])
        self.assertEquals('ref install2',
                          relationship['workflows']['install2'])
        self.assertEquals('grandparent radial install3',
                          relationship['workflows']['install3'])
        self.assertEquals('radial install4',
                          relationship['workflows']['install4'])
        self.assertEquals('parent ref install5',
                          relationship['workflows']['install5'])
        self.assertEquals(5, len(relationship['workflows']))

    def test_relationship_and_instance_workflows_recursive_inheritance(self):
        # tests for multiple-hierarchy workflows inheritance between
        # relationships, including back and forth switches between radial and
        # ref overrides, as well as overridden non-existent ref values
        ref_alias1 = 'ref_alias1'
        radial_file1_path = self.make_file_with_name('ref install2',
                                                     'radial_file1.radial')
        ref_alias2 = 'ref_alias2'
        radial_file2_path = self.make_file_with_name('parent ref install5',
                                                     'radial_file2.radial')
        ref_file_3 = self.make_file_with_name('some radial code',
                                              'ref_3.radial')

        yaml = self.BASIC_BLUEPRINT_SECTION + """
        -   name: test_node2
            type: test_type
            relationships:
                - target: test_node
                  type: test_relationship
                  workflows:
                      install1:
                          radial: "node radial install1"
                      install2:
                          ref: {0}""".format(ref_alias1) + """
                      install4:
                          radial: "node radial install4"
types:
    test_type:
        properties:
            - key: default

relationships:
    test_relationship:
        derived_from: "test_parent_relationships"
        workflows:
            install1:
                radial: "radial install1"
            install2:
                ref: {0}""".format(ref_alias1) + """
            install4:
                radial: "radial install4"

    test_parent_relationships:
        derived_from: "test_grandparent_relationships"
        workflows:
            install1:
                ref: "{0}"
            install2:
                radial: "parent radial install2"
            install5:
                ref: {1}""".format(ref_file_3, ref_alias2) + """
    test_grandparent_relationships:
        workflows:
            install1:
                radial: "grandparent radial install1"
            install2:
                ref: "{0}"
            install3:
                radial: "grandparent radial install3"
            install4:
                ref: "{1}"
            """.format(ref_file_3, ref_file_3)

        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias1): '{0}'.format(radial_file1_path),
            '{0}'.format(ref_alias2): '{0}'.format(radial_file2_path)
        })

        relationship = result['nodes'][1]['relationships'][0]
        self.assertEquals('node radial install1',
                          relationship['workflows']['install1'])
        self.assertEquals('ref install2',
                          relationship['workflows']['install2'])
        self.assertEquals('grandparent radial install3',
                          relationship['workflows']['install3'])
        self.assertEquals('node radial install4',
                          relationship['workflows']['install4'])
        self.assertEquals('parent ref install5',
                          relationship['workflows']['install5'])
        self.assertEquals(5, len(relationship['workflows']))

    def test_type_properties_derivation(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key: "not_val"
            - key2: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            - key: "val1_parent"
            - key2: "val2_parent"
            - key3: "val3_parent"
    """
        result = parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_parent', node['properties']['key3'])

    def test_empty_types_hierarchy_in_node(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key: "not_val"
            - key2: "val2"
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(1, len(node[TYPE_HIERARCHY]))
        self.assertEqual('test_type', node[TYPE_HIERARCHY][0])

    def test_types_hierarchy_in_node(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        derived_from: "test_type_parent"
        properties:
            - key: "not_val"
            - key2: "val2"
    test_type_parent: {}
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(2, len(node[TYPE_HIERARCHY]))
        self.assertEqual('test_type_parent', node[TYPE_HIERARCHY][0])
        self.assertEqual('test_type', node[TYPE_HIERARCHY][1])

    def test_types_hierarchy_order_in_node(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        derived_from: "test_type_parent"
        properties:
            - key: "not_val"
            - key2: "val2"
    test_type_parent:
        derived_from: "parent_type"

    parent_type: {}
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(3, len(node[TYPE_HIERARCHY]))
        self.assertEqual('parent_type', node[TYPE_HIERARCHY][0])
        self.assertEqual('test_type_parent', node[TYPE_HIERARCHY][1])
        self.assertEqual('test_type', node[TYPE_HIERARCHY][2])

    def test_types_hierarchy_with_node_type_impl(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific_test_type:
        derived_from: test_type

type_implementations:
    implementation_of_specific_test_type:
        type: specific_test_type
        node_ref: test_node
"""
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(2, len(node[TYPE_HIERARCHY]))
        self.assertEqual('test_type', node[TYPE_HIERARCHY][0])
        self.assertEqual('specific_test_type', node[TYPE_HIERARCHY][1])

    def test_type_properties_recursive_derivation(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key: "not_val"
            - key2: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            - key: "val_parent"
            - key2: "val2_parent"
            - key4: "val4_parent"
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        properties:
            - key: "val1_grandparent"
            - key2: "val2_grandparent"
            - key3: "val3_grandparent"
        derived_from: "test_type_grandgrandparent"

    test_type_grandgrandparent: {}
    """
        result = parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_grandparent', node['properties']['key3'])
        self.assertEquals('val4_parent', node['properties']['key4'])

    def test_type_interface_derivation(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
            test_interface2:
                - start: test_plugin2.start
                - stop: test_plugin2.stop
            test_interface3:
                - op1: test_plugin3.op
        derived_from: "test_type_parent"

    test_type_parent:
        interfaces:
            test_interface1:
                - install: nop_plugin.install
                - terminate: nop_plugin.install
            test_interface2:
                - start: test_plugin2.start
                - stop: test_plugin2.stop
            test_interface3:
                 - op1: test_plugin3.op
            test_interface4:
                - op2: test_plugin4.op2

plugins:
    test_plugin2:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
    test_plugin3:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url3.zip"
    test_plugin4:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url4.zip"
    """

        result = parse(yaml)
        self._assert_blueprint(result)
        node = result['nodes'][0]
        plugin_props = node['plugins']['test_plugin2']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('test_plugin2', plugin_props['name'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        operations = node['operations']
        self.assertEquals(12, len(operations))
        self.assertEquals(op_struct('test_plugin2', 'start'),
                          operations['start'])
        self.assertEquals(op_struct('test_plugin2', 'start'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('test_plugin2', 'stop'),
                          operations['stop'])
        self.assertEquals(op_struct('test_plugin2', 'stop'),
                          operations['test_interface2.stop'])
        self.assertEquals(op_struct('test_plugin3', 'op'),
                          operations['op1'])
        self.assertEquals(op_struct('test_plugin3', 'op'),
                          operations['test_interface3.op1'])
        self.assertEquals(op_struct('test_plugin4', 'op2'),
                          operations['op2'])
        self.assertEquals(op_struct('test_plugin4', 'op2'),
                          operations['test_interface4.op2'])
        self.assertEquals(4, len(node['plugins']))

    def test_type_interface_recursive_derivation(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
        derived_from: "test_type_parent"

    test_type_parent:
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        interfaces:
            test_interface1:
                - install: non_plugin.install
                - terminate: non_plugin.terminate
            test_interface2:
                - start: test_plugin2.start
                - stop: test_plugin2.stop

plugins:
    test_plugin2:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
        """

        result = parse(yaml)
        self._assert_blueprint(result)
        node = result['nodes'][0]
        plugin_props = node['plugins']['test_plugin2']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('test_plugin2', plugin_props['name'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        operations = node['operations']
        self.assertEquals(8, len(operations))
        self.assertEquals(op_struct('test_plugin2', 'start'),
                          operations['start'])
        self.assertEquals(op_struct('test_plugin2', 'start'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('test_plugin2', 'stop'),
                          operations['stop'])
        self.assertEquals(op_struct('test_plugin2', 'stop'),
                          operations['test_interface2.stop'])
        self.assertEquals(2, len(node['plugins']))

    def test_two_explicit_interfaces_with_same_operation_name(self):
        yaml = self.create_yaml_with_imports([self.BASIC_BLUEPRINT_SECTION,
                                              self.BASIC_PLUGIN]) + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin.install
                - terminate: test_plugin.terminate
            test_interface2:
                - install: other_test_plugin.install
                - shutdown: other_test_plugin.shutdown
plugins:
    other_test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        operations = node['operations']
        self.assertEquals(op_struct('test_plugin', 'install'),
                          operations['test_interface1.install'])
        self.assertEquals(op_struct('test_plugin', 'terminate'),
                          operations['terminate'])
        self.assertEquals(op_struct('test_plugin', 'terminate'),
                          operations['test_interface1.terminate'])
        plugin_props = node['plugins']['other_test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('http://test_url2.zip', plugin_props['url'])
        self.assertEquals('other_test_plugin', plugin_props['name'])
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals(op_struct('other_test_plugin', 'install'),
                          operations['test_interface2.install'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown'),
                          operations['test_interface2.shutdown'])
        self.assertEquals(6, len(operations))

    def test_plugins_derived_from_field(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
types:
    test_type:
        properties:
            - key
        interfaces:
            test_interface1:
                - install: test_plugin1.install
            test_interface2:
                - install: test_plugin2.install

plugins:
    test_plugin1:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url1.zip"
    test_plugin2:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
    """
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('false',
                          node['plugins']['test_plugin1']['agent_plugin'])
        self.assertEquals('false',
                          node['plugins']['test_plugin2']['agent_plugin'])

    def test_relative_path_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}""".format(mid_file_name)
        result = parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_import_from_file_uri(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT], True)
        result = parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_relative_file_uri_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}""".format('file:///' + pathname2url(mid_file_name))
        result = parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_empty_top_level_relationships(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships: {}
                        """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertEquals(0, len(result['relationships']))

    def test_empty_top_level_relationships_empty_relationship(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship: {}
                        """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertDictEqual({'name': 'test_relationship',
                              'workflows': {}},
                             result['relationships']['test_relationship'])

    def test_top_level_relationships_single_complete_relationship(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    empty_rel: {}
    test_relationship:
        derived_from: "empty_rel"
        source_interfaces:
            test_interface3:
                - test_interface3_op1
        target_interfaces:
            test_interface4:
                - test_interface4_op1: test_plugin.task_name
        """
        result = parse(yaml)
        self._assert_blueprint(result)
        self.assertDictEqual({'name': 'empty_rel',
                              'workflows': {}},
                             result['relationships']['empty_rel'])
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('test_relationship', test_relationship['name'])

        result_test_interface_3 = \
            test_relationship['source_interfaces']['test_interface3']
        self.assertEquals('test_interface3_op1', result_test_interface_3[0])
        result_test_interface_4 = \
            test_relationship['target_interfaces']['test_interface4']
        self.assertEquals({'test_interface4_op1': 'test_plugin.task_name'},
                          result_test_interface_4[0])

    def _test_top_level_relationships_relationship_with_ref_workflow(self):
        ref_alias = 'ref_alias'
        radial_file_path = self.make_file_with_name('ref custom radial',
                                                    'radial_file.radial')

        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    test_relationship:
        workflow:
            ref: "{0}\"""".format(ref_alias)
        result = parse(yaml, alias_mapping_dict={
            '{0}'.format(ref_alias): '{0}'.format(radial_file_path)})
        self._assert_blueprint(result)
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('ref custom radial', test_relationship['workflow'])

    def test_top_level_relationships_recursive_imports(self):
        bottom_level_yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    empty_rel: {}
    test_relationship:
        derived_from: "empty_rel"
        source_interfaces:
            test_interface2:
                -   install: test_plugin.install
                -   terminate: test_plugin.terminate
        """

        bottom_file_name = self.make_yaml_file(bottom_level_yaml)
        mid_level_yaml = """
relationships:
    test_relationship2:
        derived_from: "test_relationship3"
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)
        top_level_yaml = """
relationships:
    test_relationship3:
        target_interfaces:
            test_interface2:
                -   install: test_plugin.install
                -   terminate: test_plugin.terminate

imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_blueprint(result)
        self.assertDictEqual({'name': 'empty_rel',
                              'workflows': {}},
                             result['relationships']['empty_rel'])
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('test_relationship',
                          test_relationship['name'])
        self.assertDictEqual({'install': 'test_plugin.install'},
                             test_relationship['source_interfaces']
                             ['test_interface2'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             test_relationship['source_interfaces']
                             ['test_interface2'][1])
        self.assertEquals(
            2, len(test_relationship['source_interfaces']['test_interface2']))
        self.assertEquals(4, len(test_relationship))

        test_relationship2 = result['relationships']['test_relationship2']
        self.assertEquals('test_relationship2', test_relationship2['name'])
        self.assertDictEqual({'install': 'test_plugin.install'},
                             test_relationship2['target_interfaces']
                             ['test_interface2'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             test_relationship2['target_interfaces']
                             ['test_interface2'][1])
        self.assertEquals(
            2, len(test_relationship2['target_interfaces']['test_interface2']))
        self.assertEquals(4, len(test_relationship2))

        test_relationship3 = result['relationships']['test_relationship3']
        self.assertEquals('test_relationship3', test_relationship3['name'])
        self.assertDictEqual({'install': 'test_plugin.install'},
                             test_relationship3['target_interfaces']
                             ['test_interface2'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             test_relationship3['target_interfaces']
                             ['test_interface2'][1])
        self.assertEquals(
            2, len(test_relationship3['target_interfaces']['test_interface2']))
        self.assertEquals(3, len(test_relationship3))

    def test_top_level_relationship_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            - without_default_value
            - with_simple_default_value: 1
            - with_object_default_value:
                comp1: 1
                comp2: 2
"""
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        relationships = result['relationships']
        self.assertEquals(1, len(relationships))
        test_relationship = relationships['test_relationship']
        properties = test_relationship['properties']
        self.assertIn('without_default_value', properties)
        self.assertIn({'with_simple_default_value': 1}, properties)
        self.assertIn({'with_object_default_value': {
            'comp1': 1, 'comp2': 2
        }}, properties)

    def test_top_level_relationship_properties_inheritance(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship1:
        properties:
            - prop1
            - prop2
            - prop3: prop3_value_1
            - derived1: derived1_value
    test_relationship2:
        derived_from: test_relationship1
        properties:
            - prop2: prop2_value_2
            - prop3: prop3_value_2
            - prop4
            - prop5
            - prop6: prop6_value_2
            - derived2: derived2_value
    test_relationship3:
        derived_from: test_relationship2
        properties:
            - prop5: prop5_value_3
            - prop6: prop6_value_3
            - prop7
"""
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        relationships = result['relationships']
        self.assertEquals(3, len(relationships))
        r1_properties = relationships['test_relationship1']['properties']
        r2_properties = relationships['test_relationship2']['properties']
        r3_properties = relationships['test_relationship3']['properties']
        self.assertEquals(4, len(r1_properties))
        self.assertIn('prop1', r1_properties)
        self.assertIn('prop2', r1_properties)
        self.assertIn({'prop3': 'prop3_value_1'}, r1_properties)
        self.assertIn({'derived1': 'derived1_value'}, r1_properties)
        self.assertEquals(8, len(r2_properties))
        self.assertIn('prop1', r2_properties)
        self.assertIn({'prop2': 'prop2_value_2'}, r2_properties)
        self.assertIn({'prop3': 'prop3_value_2'}, r2_properties)
        self.assertIn('prop4', r2_properties)
        self.assertIn('prop5', r2_properties)
        self.assertIn({'prop6': 'prop6_value_2'}, r2_properties)
        self.assertIn({'derived1': 'derived1_value'}, r2_properties)
        self.assertIn({'derived2': 'derived2_value'}, r2_properties)
        self.assertEquals(9, len(r3_properties))
        self.assertIn('prop1', r3_properties)
        self.assertIn({'prop2': 'prop2_value_2'}, r3_properties)
        self.assertIn({'prop3': 'prop3_value_2'}, r3_properties)
        self.assertIn('prop4', r3_properties)
        self.assertIn({'prop5': 'prop5_value_3'}, r3_properties)
        self.assertIn({'prop6': 'prop6_value_3'}, r3_properties)
        self.assertIn('prop7', r3_properties)
        self.assertIn({'derived1': 'derived1_value'}, r3_properties)
        self.assertIn({'derived2': 'derived2_value'}, r3_properties)

    def test_instance_relationships_empty_relationships_section(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            relationships: []
                    """
        result = parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertListEqual([], result['nodes'][0]['relationships'])

    def test_instance_relationships_standard_relationship(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    source_interfaces:
                        test_interface1:
                            - install: test_plugin.install
relationships:
    test_relationship: {}
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
                    """
        result = parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        self.assertEquals('test_node2', result['nodes'][1]['id'])
        self.assertEquals(1, len(result['nodes'][1]['relationships']))
        relationship = result['nodes'][1]['relationships'][0]
        self.assertEquals('test_relationship', relationship['type'])
        self.assertEquals('test_node', relationship['target_id'])
        self.assertDictEqual({'install': 'test_plugin.install'},
                             relationship['source_interfaces']
                             ['test_interface1'][0])
        self.assertEquals('reachable', relationship['state'])
        relationship_source_operations = relationship['source_operations']
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             relationship_source_operations['install'])
        self.assertDictEqual(
            op_struct('test_plugin', 'install'),
            relationship_source_operations['test_interface1.install'])
        self.assertEqual(2, len(relationship_source_operations))

        self.assertEquals(8, len(relationship))
        plugin_def = result['nodes'][1]['plugins']['test_plugin']
        self.assertEquals('test_plugin', plugin_def['name'])
        self.assertEquals('false', plugin_def['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_def['url'])
        dependents = result['nodes'][0]['dependents']
        self.assertListEqual(['test_node2'], dependents)

    def test_instance_relationships_duplicate_relationship(self):
        # right now, having two relationships with the same (type,target)
        # under one node is valid
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node
                -   type: test_relationship
                    target: test_node
relationships:
    test_relationship: {}
                    """
        result = parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        self.assertEquals('test_node2', result['nodes'][1]['id'])
        self.assertEquals(2, len(result['nodes'][1]['relationships']))
        self.assertEquals('test_relationship',
                          result['nodes'][1]['relationships'][0]['type'])
        self.assertEquals('test_relationship',
                          result['nodes'][1]['relationships'][1]['type'])
        self.assertEquals('test_node',
                          result['nodes'][1]['relationships'][0]['target_id'])
        self.assertEquals('test_node',
                          result['nodes'][1]['relationships'][1]['target_id'])
        self.assertEquals('reachable',
                          result['nodes'][1]['relationships'][0]['state'])
        self.assertEquals('reachable',
                          result['nodes'][1]['relationships'][1]['state'])
        self.assertEquals(6, len(result['nodes'][1]['relationships'][0]))
        self.assertEquals(6, len(result['nodes'][1]['relationships'][1]))
        dependents = result['nodes'][0]['dependents']
        self.assertListEqual(['test_node2'], dependents)

    def test_instance_relationships_relationship_inheritance(self):
        # possibly 'inheritance' is the wrong term to use here,
        # the meaning is for checking that the relationship properties from the
        # top-level relationships
        # section are used for instance-relationships which declare their types
        # note there are no overrides in this case; these are tested in the
        # next, more thorough test
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: test_relationship
                    target: test_node
                    source_interfaces:
                        interface1:
                            - op1: test_plugin.task_name1
relationships:
    relationship: {}
    test_relationship:
        derived_from: "relationship"
        target_interfaces:
            interface2:
                - op2: test_plugin.task_name2
plugins:
    test_plugin:
        derived_from: cloudify.plugins.remote_plugin
        properties:
            url: some_url
                    """
        result = parse(yaml)
        relationship = result['nodes'][1]['relationships'][0]
        self.assertEquals('test_relationship', relationship['type'])
        self.assertEquals('test_node', relationship['target_id'])
        self.assertEquals('reachable', relationship['state'])
        self.assertDictEqual({'op1': 'test_plugin.task_name1'},
                             relationship['source_interfaces']
                             ['interface1'][0])
        self.assertDictEqual({'op2': 'test_plugin.task_name2'},
                             relationship['target_interfaces']
                             ['interface2'][0])

        rel_source_ops = relationship['source_operations']

        self.assertDictEqual(op_struct('test_plugin', 'task_name1'),
                             rel_source_ops['op1'])
        self.assertDictEqual(op_struct('test_plugin', 'task_name1'),
                             rel_source_ops['interface1.op1'])
        self.assertEquals(2, len(rel_source_ops))

        rel_target_ops = relationship['target_operations']
        self.assertDictEqual(op_struct('test_plugin', 'task_name2'),
                             rel_target_ops['op2'])
        self.assertDictEqual(op_struct('test_plugin', 'task_name2'),
                             rel_target_ops['interface2.op2'])
        self.assertEquals(2, len(rel_target_ops))

        self.assertEquals(10, len(relationship))
        dependents = result['nodes'][0]['dependents']
        self.assertListEqual(['test_node2'], dependents)

    def test_instance_relationship_properties_inheritance(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            properties:
                key: "val"
            relationships:
                -   type: empty_relationship
                    target: test_node
                    properties:
                        prop1: prop1_value_new
                        prop2: prop2_value_new
                        prop7: prop7_value_new_instance
relationships:
    empty_relationship:
        properties:
            - prop1
            - prop2
            - prop7
    test_relationship:
        derived_from: empty_relationship
        properties:
            - prop1
            - prop2: prop2_value
            - prop3: prop3_value
            - prop4
            - prop5: prop5_value
            - prop6: prop6_value
relationship_implementations:
    impl1:
        type: test_relationship
        source_node_ref: test_node2
        target_node_ref: test_node
        properties:
            prop4: prop4_value_new
            prop5: prop5_value_new
            prop7: prop7_value_new_impl
"""
        result = parse(yaml)
        relationships = result['relationships']
        self.assertEquals(2, len(relationships))
        r_properties = relationships['test_relationship']['properties']
        self.assertEquals(7, len(r_properties))
        i_properties = result['nodes'][1]['relationships'][0]['properties']
        self.assertEquals(7, len(i_properties))
        self.assertEquals('prop1_value_new', i_properties['prop1'])
        self.assertEquals('prop2_value_new', i_properties['prop2'])
        self.assertEquals('prop3_value', i_properties['prop3'])
        self.assertEquals('prop4_value_new', i_properties['prop4'])
        self.assertEquals('prop5_value_new', i_properties['prop5'])
        self.assertEquals('prop6_value', i_properties['prop6'])
        self.assertEquals('prop7_value_new_impl', i_properties['prop7'])

    def test_relationships_and_node_recursive_inheritance(self):
        # testing for a complete inheritance path for relationships
        # from top-level relationships to a relationship instance
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: relationship
                    target: test_node
                    source_interfaces:
                        test_interface3:
                            - install: test_plugin.install
                    target_interfaces:
                        test_interface1:
                            - install: test_plugin.install
relationships:
    relationship:
        derived_from: "parent_relationship"
        source_interfaces:
            test_interface2:
                -   install: test_plugin.install
                -   terminate: test_plugin.terminate
    parent_relationship:
        target_interfaces:
            test_interface3:
                - install
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"

        """
        result = parse(yaml)
        node_relationship = result['nodes'][1]['relationships'][0]
        relationship = result['relationships']['relationship']
        parent_relationship = result['relationships']['parent_relationship']
        self.assertEquals(2, len(result['relationships']))
        self.assertEquals(3, len(parent_relationship))
        self.assertEquals(5, len(relationship))
        self.assertEquals(10, len(node_relationship))
        dependents = result['nodes'][0]['dependents']
        self.assertListEqual(['test_node2'], dependents)

        self.assertEquals('parent_relationship', parent_relationship['name'])
        self.assertEquals(1, len(parent_relationship['target_interfaces']))
        self.assertEquals(1, len(parent_relationship['target_interfaces']
                                                    ['test_interface3']))
        self.assertEquals('install',
                          parent_relationship['target_interfaces']
                                             ['test_interface3'][0])

        self.assertEquals('relationship', relationship['name'])
        self.assertEquals('parent_relationship', relationship['derived_from'])
        self.assertEquals(1, len(relationship['target_interfaces']))
        self.assertEquals(1, len(relationship['target_interfaces']
                                             ['test_interface3']))
        self.assertEquals('install', relationship['target_interfaces']
                                                 ['test_interface3'][0])
        self.assertEquals(1, len(relationship['source_interfaces']))
        self.assertEquals(2, len(relationship['source_interfaces']
                                             ['test_interface2']))
        self.assertDictEqual({'install': 'test_plugin.install'},
                             relationship['source_interfaces']
                                         ['test_interface2'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             relationship['source_interfaces']
                                         ['test_interface2'][1])

        self.assertEquals('relationship', node_relationship['type'])
        self.assertEquals('test_node', node_relationship['target_id'])
        self.assertEquals('reachable', node_relationship['state'])
        self.assertEquals(2, len(node_relationship['target_interfaces']))
        self.assertEquals(1, len(node_relationship['target_interfaces']
                                                  ['test_interface3']))
        self.assertEquals('install', node_relationship['target_interfaces']
                                                      ['test_interface3'][0])
        self.assertEquals(1, len(node_relationship['target_interfaces']
                                                  ['test_interface1']))
        self.assertDictEqual({'install': 'test_plugin.install'},
                             node_relationship['target_interfaces']
                                              ['test_interface1'][0])
        self.assertEquals(2, len(node_relationship['source_interfaces']))
        self.assertEquals(1, len(node_relationship['source_interfaces']
                                                  ['test_interface3']))
        self.assertEquals({'install': 'test_plugin.install'},
                          node_relationship['source_interfaces']
                                           ['test_interface2'][0])
        self.assertEquals(2, len(node_relationship['source_interfaces']
                                                  ['test_interface2']))
        self.assertEquals({'install': 'test_plugin.install'},
                          node_relationship['source_interfaces']
                                           ['test_interface2'][0])
        self.assertEquals({'terminate': 'test_plugin.terminate'},
                          node_relationship['source_interfaces']
                                           ['test_interface2'][1])

        rel_source_ops = node_relationship['source_operations']
        self.assertEquals(4, len(rel_source_ops))
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_source_ops['test_interface2.install'])
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_source_ops['test_interface3.install'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_source_ops['terminate'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_source_ops['test_interface2.terminate'])

        rel_target_ops = node_relationship['target_operations']
        self.assertEquals(2, len(rel_target_ops))
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_target_ops['install'])
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_target_ops['test_interface1.install'])

    def test_relationship_interfaces_inheritance_merge(self):
        # testing for a complete inheritance path for relationships
        # from top-level relationships to a relationship instance
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: relationship
                    target: test_node
                    target_interfaces:
                        test_interface:
                            - destroy: test_plugin.destroy1
                    source_interfaces:
                        test_interface:
                            - install2: test_plugin.install2
                            - destroy2: test_plugin.destroy2
relationships:
    relationship:
        derived_from: "parent_relationship"
        target_interfaces:
            test_interface:
                -   install: test_plugin.install
                -   terminate: test_plugin.terminate
        source_interfaces:
            test_interface:
                -   install2: test_plugin.install
                -   terminate2: test_plugin.terminate
    parent_relationship:
        target_interfaces:
            test_interface:
                - install
        source_interfaces:
            test_interface:
                - install2
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"

        """
        result = parse(yaml)
        node_relationship = result['nodes'][1]['relationships'][0]
        relationship = result['relationships']['relationship']
        parent_relationship = result['relationships']['parent_relationship']
        self.assertEquals(2, len(result['relationships']))
        self.assertEquals(4, len(parent_relationship))
        self.assertEquals(5, len(relationship))
        self.assertEquals(10, len(node_relationship))
        dependents = result['nodes'][0]['dependents']
        self.assertListEqual(['test_node2'], dependents)

        self.assertEquals('parent_relationship', parent_relationship['name'])
        self.assertEquals(1, len(parent_relationship['target_interfaces']))
        self.assertEquals(1, len(parent_relationship['target_interfaces']
                                                    ['test_interface']))
        self.assertEquals('install', parent_relationship['target_interfaces']
                                                        ['test_interface'][0])
        self.assertEquals(1, len(parent_relationship['source_interfaces']))
        self.assertEquals(1, len(parent_relationship['source_interfaces']
                                                    ['test_interface']))
        self.assertEquals('install2',
                          parent_relationship['source_interfaces']
                                             ['test_interface'][0])

        self.assertEquals('relationship', relationship['name'])
        self.assertEquals('parent_relationship', relationship['derived_from'])
        self.assertEquals(1, len(relationship['target_interfaces']))
        self.assertEquals(2, len(relationship['target_interfaces']
                                             ['test_interface']))
        self.assertDictEqual({'install': 'test_plugin.install'},
                             relationship['target_interfaces']
                                         ['test_interface'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             relationship['target_interfaces']
                                         ['test_interface'][1])
        self.assertEquals(1, len(relationship['source_interfaces']))
        self.assertEquals(
            2, len(relationship['source_interfaces']['test_interface']))
        self.assertDictEqual({'install2': 'test_plugin.install'},
                             relationship['source_interfaces']
                                         ['test_interface'][0])
        self.assertDictEqual({'terminate2': 'test_plugin.terminate'},
                             relationship['source_interfaces']
                                         ['test_interface'][1])

        self.assertEquals('relationship', node_relationship['type'])
        self.assertEquals('test_node', node_relationship['target_id'])
        self.assertEquals('reachable', node_relationship['state'])
        self.assertEquals(1, len(node_relationship['target_interfaces']))
        self.assertEquals(
            3, len(node_relationship['target_interfaces']['test_interface']))
        self.assertDictEqual({'install': 'test_plugin.install'},
                             node_relationship['target_interfaces']
                                              ['test_interface'][0])
        self.assertDictEqual({'terminate': 'test_plugin.terminate'},
                             relationship['target_interfaces']
                                         ['test_interface'][1])
        self.assertDictEqual({'destroy': 'test_plugin.destroy1'},
                             node_relationship['target_interfaces']
                                              ['test_interface'][2])
        self.assertEquals(1, len(node_relationship['source_interfaces']))
        self.assertEquals(
            3, len(node_relationship['source_interfaces']['test_interface']))
        self.assertEquals({'install2': 'test_plugin.install2'},
                          node_relationship['source_interfaces']
                                           ['test_interface'][0])
        self.assertDictEqual({'terminate2': 'test_plugin.terminate'},
                             relationship['source_interfaces']
                                         ['test_interface'][1])
        self.assertEquals({'destroy2': 'test_plugin.destroy2'},
                          node_relationship['source_interfaces']
                                           ['test_interface'][2])

        rel_source_ops = node_relationship['source_operations']
        self.assertDictEqual(op_struct('test_plugin', 'install2'),
                             rel_source_ops['install2'])
        self.assertDictEqual(op_struct('test_plugin', 'install2'),
                             rel_source_ops['test_interface.install2'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_source_ops['terminate2'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_source_ops['test_interface.terminate2'])
        self.assertDictEqual(op_struct('test_plugin', 'destroy2'),
                             rel_source_ops['destroy2'])
        self.assertDictEqual(op_struct('test_plugin', 'destroy2'),
                             rel_source_ops['test_interface.destroy2'])
        self.assertEquals(6, len(rel_source_ops))

        rel_target_ops = node_relationship['target_operations']
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_target_ops['install'])
        self.assertDictEqual(op_struct('test_plugin', 'install'),
                             rel_target_ops['test_interface.install'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_target_ops['terminate'])
        self.assertDictEqual(op_struct('test_plugin', 'terminate'),
                             rel_target_ops['test_interface.terminate'])
        self.assertDictEqual(op_struct('test_plugin', 'destroy1'),
                             rel_target_ops['destroy'])
        self.assertDictEqual(op_struct('test_plugin', 'destroy1'),
                             rel_target_ops['test_interface.destroy'])
        self.assertEquals(6, len(rel_source_ops))

    def test_node_host_id_field(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node
            type: cloudify.types.host
            properties:
                key: "val"
types:
    cloudify.types.host:
        properties:
            - key
            """
        result = parse(yaml)
        self.assertEquals('test_node', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
        -   name: test_node2
            type: another_type
            relationships:
                -   type: cloudify.relationships.contained_in
                    target: test_node1
        -   name: test_node3
            type: another_type
            relationships:
                -   type: cloudify.relationships.contained_in
                    target: test_node2
types:
    cloudify.types.host: {}
    another_type: {}

relationships:
    cloudify.relationships.contained_in: {}
            """
        result = parse(yaml)
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])
        self.assertEquals('test_node1', result['nodes'][2]['host_id'])

    def test_node_host_id_field_via_node_supertype(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: another_type
types:
    cloudify.types.host: {}
    another_type:
        derived_from: cloudify.types.host
            """
        result = parse(yaml)
        self.assertEquals('test_node1', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship_derived_from_inheritance(
            self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
        -   name: test_node2
            type: another_type
            relationships:
                -   type: test_relationship
                    target: test_node1
types:
    cloudify.types.host: {}
    another_type: {}
relationships:
    cloudify.relationships.contained_in: {}
    test_relationship:
        derived_from: cloudify.relationships.contained_in
            """
        result = parse(yaml)
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])

    def test_node_plugins_to_install_field(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
            """
        result = parse(yaml)
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals('true', plugin['agent_plugin'])
        self.assertEquals('http://test_plugin.zip', plugin['url'])
        self.assertEquals(1, len(result['nodes'][0]['plugins_to_install']))

    def test_plugin_with_folder_as_only_property(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            folder: "test-folder"
            """
        parse(yaml)

    def test_node_plugins_to_install_field_installer_plugin(self):
        # testing to ensure the installer plugin is treated differently and
        # is not
        # put on the plugins_to_install dict like the rest of the plugins
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: plugin_installer.start
plugins:
    plugin_installer:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
        """
        # note that we're expecting an empty dict since every node which
        # is a host should have one
        result = parse(yaml)
        self.assertEquals([], result['nodes'][0]['plugins_to_install'])

    def test_node_plugins_to_install_field_remote_plugin(self):
        # testing to ensure that only plugins of type agent_plugin are put
        # on the plugins_to_install field
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_plugin.zip"
        """

        result = parse(yaml)
        self.assertEquals([], result['nodes'][0]['plugins_to_install'])

    def test_node_plugins_to_install_field_plugins_from_contained_nodes(self):
        # testing to ensure plugins from nodes with contained_in relationships
        #  to a host node (whether direct
        # or recursive) also get added to the plugins_to_install field.
        # this test also ensures there's no problem with a "duplicate" plugin
        # on the plugins_to_install field,
        # as test_plugin should be added from both test_node2 and test_node4
        # [only one should remain in the end]
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
        -   name: test_node2
            type: test_type
            relationships:
                -   type: 'cloudify.relationships.contained_in'
                    target: test_node1
        -   name: test_node3
            type: test_type2
            relationships:
                -   type: 'cloudify.relationships.contained_in'
                    target: test_node2
        -   name: test_node4
            type: test_type
            relationships:
                -   type: 'cloudify.relationships.contained_in'
                    target: test_node3
types:
    cloudify.types.host: {}
    test_type:
        interfaces:
            test_interface:
                - start: test_plugin.start
    test_type2:
        interfaces:
            test_interface2:
                - install: test_plugin2.install
relationships:
    cloudify.relationships.contained_in: {}
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
    test_plugin2:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin2.zip"
        """

        result = parse(yaml)
        # ensuring non-host nodes don't have this field
        self.assertTrue('plugins_to_install' not in result['nodes'][1])

        node = result['nodes'][0]
        test_plugin = self._get_plugin_to_install_from_node(
            node, 'test_plugin')
        test_plugin2 = self._get_plugin_to_install_from_node(
            node, 'test_plugin2')
        self.assertEquals('test_plugin', test_plugin['name'])
        self.assertEquals('true', test_plugin['agent_plugin'])
        self.assertEquals('http://test_plugin.zip', test_plugin['url'])
        self.assertEquals('test_plugin2', test_plugin2['name'])
        self.assertEquals('true', test_plugin2['agent_plugin'])
        self.assertEquals('http://test_plugin2.zip', test_plugin2['url'])
        self.assertEquals(2, len(result['nodes'][0]['plugins_to_install']))

    def test_node_cloudify_runtime_property(self):
        yaml = self.MINIMAL_BLUEPRINT
        result = parse(yaml)
        self.assertEquals(
            {},
            result['nodes'][0]['properties']['cloudify_runtime'])

    def test_import_resources(self):
        resource_file_name = 'resource_file.yaml'
        file_name = self.make_file_with_name(
            self.MINIMAL_BLUEPRINT, resource_file_name, 'resources')
        file_url = self._path2url(file_name)
        yaml = """
imports:
    -   {0}""".format(resource_file_name)
        result = parse(yaml,
                       resources_base_url=file_url[:-len(resource_file_name)])
        self._assert_minimal_blueprint(result)

    def test_import_resources_from_url(self):
        resource_file_name = 'resource_file.yaml'
        file_name = self.make_file_with_name(
            self.MINIMAL_BLUEPRINT, resource_file_name, 'resources')
        file_url = self._path2url(file_name)
        yaml = """
imports:
    -   {0}""".format(resource_file_name)
        top_file = self.make_yaml_file(yaml, True)
        result = parse_from_url(
            top_file, resources_base_url=file_url[:-len(resource_file_name)])
        self._assert_minimal_blueprint(result)

    def test_recursive_imports_with_inner_circular(self):
        bottom_level_yaml = """
imports:
    -   {0}
        """.format(
            os.path.join(self._temp_dir, "mid_level.yaml")) + self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_file_with_name(mid_level_yaml,
                                                 'mid_level.yaml')

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}""".format(mid_file_name)

        result = parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_recursive_imports_with_complete_circle(self):
        bottom_level_yaml = """
imports:
    -   {0}
            """.format(
            os.path.join(self._temp_dir, "top_level.yaml")) + self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_BLUEPRINT_SECTION + """
imports:
    -   {0}""".format(mid_file_name)
        top_file_name = self.make_file_with_name(
            top_level_yaml, 'top_level.yaml')
        result = parse_from_path(top_file_name)
        self._assert_blueprint(result)

    def test_plugins_with_root_plugin(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_TYPE + \
            self.BASIC_PLUGIN + """
    cloudify.plugins.plugin: {}
    cloudify.plugins.remote_plugin:
        derived_from: "cloudify.plugins.plugin"

        """
        result = parse(yaml)
        self._assert_blueprint(result)

    def test_relative_ref(self):
        self.make_file_with_name('my custom radial', 'radial_file.radial')

        yaml = self.MINIMAL_BLUEPRINT + """
workflows:
        install:
            ref: {0}
        """.format('radial_file.radial')
        file_path = self.make_yaml_file(yaml)
        result = parse_from_path(file_path)
        self._assert_minimal_blueprint(result)
        self.assertEquals('my custom radial', result['workflows']['install'])

    def test_node_interfaces_operation_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_BLUEPRINT_SECTION + """
            interfaces:
                test_interface1:
                    - install: test_plugin.install
                    - terminate: test_plugin.terminate
types:
    test_type:
        properties:
            - key
            """
        result = parse(yaml)
        self._assert_blueprint(result)

    def test_node_without_host_id(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + """
        -   name: test_node2
            type: cloudify.types.host
types:
    cloudify.types.host: {}
    test_type:
        properties:
            - key
        """
        result = parse(yaml)
        self.assertFalse('host_id' in result['nodes'][0])
        self.assertEquals('test_node2', result['nodes'][1]['host_id'])

    def test_instance_relationships_target_node_plugins(self):
        # tests that plugins defined on instance relationships as
        # "run_on_node"="target" will
        # indeed appear in the output on the target node's plugins section
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    source_interfaces:
                        test_interface1:
                            - install: test_plugin1.install
                -   type: "test_relationship"
                    target: "test_node"
                    target_interfaces:
                        test_interface1:
                            - install: test_plugin2.install
relationships:
    test_relationship: {}
plugins:
    test_plugin1:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url1.zip"
    test_plugin2:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url2.zip"
                """

        result = parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        self.assertEquals('test_node2', result['nodes'][1]['id'])
        self.assertEquals(2, len(result['nodes'][1]['relationships']))

        relationship1 = result['nodes'][1]['relationships'][0]
        self.assertEquals('test_relationship', relationship1['type'])
        self.assertEquals('test_node', relationship1['target_id'])
        self.assertEquals('reachable', relationship1['state'])
        rel1_source_ops = relationship1['source_operations']
        self.assertDictEqual(op_struct('test_plugin1', 'install'),
                             rel1_source_ops['install'])
        self.assertDictEqual(op_struct('test_plugin1', 'install'),
                             rel1_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel1_source_ops))
        self.assertEquals(8, len(relationship1))
        plugin1_def = result['nodes'][1]['plugins']['test_plugin1']
        self.assertEquals('test_plugin1', plugin1_def['name'])
        self.assertEquals('false', plugin1_def['agent_plugin'])
        self.assertEquals('http://test_url1.zip', plugin1_def['url'])

        relationship2 = result['nodes'][1]['relationships'][1]
        self.assertEquals('test_relationship', relationship2['type'])
        self.assertEquals('test_node', relationship2['target_id'])
        self.assertEquals('reachable', relationship2['state'])
        rel2_source_ops = relationship2['target_operations']
        self.assertDictEqual(op_struct('test_plugin2', 'install'),
                             rel2_source_ops['install'])
        self.assertDictEqual(op_struct('test_plugin2', 'install'),
                             rel2_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel2_source_ops))
        self.assertEquals(8, len(relationship2))

        # expecting the other plugin to be under test_node rather than
        # test_node2:
        plugin2_def = result['nodes'][0]['plugins']['test_plugin2']
        self.assertEquals('test_plugin2', plugin2_def['name'])
        self.assertEquals('false', plugin2_def['agent_plugin'])
        self.assertEquals('http://test_url2.zip', plugin2_def['url'])

    def test_multiple_instances(self):
        yaml = self.MINIMAL_BLUEPRINT + """
            instances:
                deploy: 2
                """
        result = parse(yaml)
        self.assertEquals('test_app', result['name'])
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])
        self.assertEquals(2, node['instances']['deploy'])

    def test_import_types_combination(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type2
            """]) + """
types:
    test_type2: {}
        """

        result = parse(yaml)
        self.assertEquals('test_app', result['name'])
        self.assertEquals(2, len(result['nodes']))
        node1 = result['nodes'][0]
        node2 = result['nodes'][1]
        self.assertEquals('test_node', node1['id'])
        self.assertEquals('test_type', node1['type'])
        self.assertEquals('val', node1['properties']['key'])
        self.assertEquals(1, node1['instances']['deploy'])
        self.assertEquals('test_node2', node2['id'])
        self.assertEquals('test_type2', node2['type'])
        self.assertEquals(1, node2['instances']['deploy'])

    def test_node_plugins_to_install_field_plugin_installer_plugin(self):
        # testing to ensure plugin installer is treated differently and is not
        # put on the plugins_to_install dict like the rest of the plugins
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: plugin_installer.start
plugins:
    plugin_installer:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
        """
        # note that we're expecting an empty dict since every node which
        # is a host should have one
        result = parse(yaml)
        self.assertEquals([], result['nodes'][0]['plugins_to_install'])

    def test_operation_mapping_with_properties_injection(self):
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
                        key: "value"
"""
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        operations = node['operations']
        self.assertEquals(
            op_struct('test_plugin', 'install', {'key': 'value'}),
            operations['install'])
        self.assertEquals(
            op_struct('test_plugin', 'install', {'key': 'value'}),
            operations['test_interface1.install'])

    def test_relationship_operation_mapping_with_properties_injection(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    source_interfaces:
                        test_interface1:
                            - install:
                                mapping: test_plugin.install
                                properties:
                                    key: "value"
relationships:
    test_relationship: {}
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
                """

        result = parse(yaml)
        relationship1 = result['nodes'][1]['relationships'][0]
        rel1_source_ops = relationship1['source_operations']
        self.assertDictEqual(
            op_struct('test_plugin', 'install', {'key': 'value'}),
            rel1_source_ops['install'])
        self.assertDictEqual(
            op_struct('test_plugin', 'install', {'key': 'value'}),
            rel1_source_ops['test_interface1.install'])

    def test_operation_mapping_with_get_property(self):
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
                        delegated_key: { get_property: "key" }
                        nested_key:
                            prop1: "value1"
                            prop2: { get_property: "key" }


"""
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        operations = node['operations']
        expected_props = {'delegated_key': 'val',
                          'nested_key': {'prop1': 'value1', 'prop2': 'val'}}
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['install'])
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['test_interface1.install'])

    def test_relationship_operation_mapping_with_properties_injection_get_property(self):  # NOQA
        yaml = self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            properties:
                key: "val"
            relationships:
                -   type: "test_relationship"
                    target: "test_node"
                    source_interfaces:
                        test_interface1:
                            - install:
                                mapping: test_plugin.install
                                properties:
                                    delegated_key: { get_property: "key" }
                                    nested_key:
                                        prop1: "value1"
                                        prop2: { get_property: "key" }
relationships:
    test_relationship: {}
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://test_url.zip"
                """

        result = parse(yaml)
        relationship1 = result['nodes'][1]['relationships'][0]
        rel1_source_ops = relationship1['source_operations']
        expected_props = {'delegated_key': 'val',
                          'nested_key': {'prop1': 'value1', 'prop2': 'val'}}
        self.assertDictEqual(
            op_struct('test_plugin', 'install', expected_props),
            rel1_source_ops['install'])
        self.assertDictEqual(
            op_struct('test_plugin', 'install', expected_props),
            rel1_source_ops['test_interface1.install'])

    def test_type_implementation(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific_test_type:
        derived_from: test_type

type_implementations:
    implementation_of_specific_test_type:
        type: specific_test_type
        node_ref: test_node
"""
        result = parse(yaml)
        self._assert_minimal_blueprint(result,
                                       expected_type='specific_test_type',
                                       expected_declared_type='test_type')

    def test_type_implementation_with_new_properties(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT]) + """
types:
    specific_test_type:
        derived_from: test_type
        properties:
            - mandatory
            - new_prop: default

type_implementations:
    implementation_of_specific_test_type:
        type: specific_test_type
        node_ref: test_node
        properties:
            mandatory: mandatory_value
"""
        result = parse(yaml)
        self._assert_minimal_blueprint(result,
                                       expected_type='specific_test_type',
                                       expected_declared_type='test_type')
        node = result['nodes'][0]
        self.assertEquals('mandatory_value', node['properties']['mandatory'])
        self.assertEquals('default', node['properties']['new_prop'])

    def test_relationship_implementations(self):

        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                - type: test_relationship
                  target: test_node
                  workflows: {}
relationships:
    test_relationship: {} """]) + """

relationships:
    specific_test_relationship:
        derived_from: test_relationship

relationship_implementations:
    specific_test_relationship_impl:
        type: specific_test_relationship
        source_node_ref: test_node2
        target_node_ref: test_node
"""
        result = parse(yaml)
        source_node = result['nodes'][1]
        self.assertEquals(1, len(source_node['relationships']))
        node_relationship = source_node['relationships'][0]
        self.assertEquals('specific_test_relationship',
                          node_relationship['type'])

    def test_relationship_two_types_implementations(self):

        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
        -   name: test_node2
            type: test_type
            relationships:
                - type: test_relationship1
                  target: test_node
                - type: test_relationship2
                  target: test_node
relationships:
    test_relationship1: {}
    test_relationship2: {} """]) + """

relationships:
    specific_test_relationship1:
        derived_from: test_relationship1
    specific_test_relationship2:
        derived_from: test_relationship2

relationship_implementations:
    specific_test_relationship1_impl:
        type: specific_test_relationship1
        source_node_ref: test_node2
        target_node_ref: test_node
    specific_test_relationship2_impl:
        type: specific_test_relationship2
        source_node_ref: test_node2
        target_node_ref: test_node
"""
        result = parse(yaml)
        source_node = result['nodes'][1]
        self.assertEquals(2, len(source_node['relationships']))
        node_relationship1 = source_node['relationships'][0]
        self.assertEquals('specific_test_relationship1',
                          node_relationship1['type'])
        node_relationship2 = source_node['relationships'][1]
        self.assertEquals('specific_test_relationship2',
                          node_relationship2['type'])

    def test_operation_mapping_with_nested_get_property(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            - key
            - some_prop:
                nested: 'nested_value'
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        mapped: { get_property: "some_prop.nested" }

"""
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        operations = node['operations']
        expected_props = {'mapped': 'nested_value'}
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['install'])
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['test_interface1.install'])

    def test_operation_mapping_with_array_index(self):
        yaml = self.BASIC_BLUEPRINT_SECTION + self.BASIC_PLUGIN + """
types:
    test_type:
        properties:
            - key
            - some_prop:
                -   nested_value
        interfaces:
            test_interface1:
                - install:
                    mapping: test_plugin.install
                    properties:
                        mapped: { get_property: "some_prop[0]" }

"""
        result = parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = node['plugins']['test_plugin']
        self.assertEquals(4, len(plugin_props))
        self.assertEquals('false', plugin_props['agent_plugin'])
        self.assertEquals('http://test_url.zip', plugin_props['url'])
        self.assertEquals('test_plugin', plugin_props['name'])
        operations = node['operations']
        expected_props = {'mapped': 'nested_value'}
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['install'])
        self.assertEquals(op_struct('test_plugin', 'install', expected_props),
                          operations['test_interface1.install'])


class ManagementPluginsToInstallTest(AbstractTestParser):
    def test_one_manager_one_agent_plugin_on_same_node(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start
                - create: test_management_plugin.create
plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
    test_management_plugin:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin.zip"
            """
        result = parse(yaml)
        management_plugins_to_install_for_node = \
            result['nodes'][0]['management_plugins_to_install']
        self.assertEquals(1, len(management_plugins_to_install_for_node))
        plugin = management_plugins_to_install_for_node[0]
        self.assertEquals('test_management_plugin', plugin['name'])
        self.assertEquals('false', plugin['agent_plugin'])
        self.assertEquals('true', plugin['manager_plugin'])
        self.assertEquals('http://test_management_plugin.zip', plugin['url'])

        # check the property on the plan is correct
        management_plugins_to_install_for_plan = \
            result["management_plugins_to_install"]
        self.assertEquals(1, len(management_plugins_to_install_for_plan))

        # check the boolean flag is correct
        is_management_plugins_to_install = \
            result["is_management_plugins_to_install"]
        self.assertTrue(is_management_plugins_to_install)

    def test_agent_installer_plugin_is_ignored(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_management_interface:
                - start: worker_installer.start
plugins:
    worker_installer:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://worker_installer.zip"
            """
        result = parse(yaml)
        self.assertEquals([], result['nodes'][0]
                          ['management_plugins_to_install'])

    def test_plugin_installer_plugin_is_ignored(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
types:
    cloudify.types.host:
        interfaces:
            test_management_interface:
                - start: plugin_installer.start
plugins:
    plugin_installer:
        derived_from: "cloudify.plugins.remote_plugin"
        properties:
            url: "http://worker_installer.zip"
            """
        result = parse(yaml)
        self.assertEquals([], result['nodes'][0]
                          ['management_plugins_to_install'])

    def test_same_plugin_one_two_nodes(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
            interfaces:
                test_interface:
                    - create: test_management_plugin.create
        -   name: test_node2
            type: cloudify.types.host
            interfaces:
                test_interface:
                    - create: test_management_plugin.create

types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
    test_management_plugin:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin.zip"
            """
        result = parse(yaml)
        for node in result['nodes']:
            management_plugins_to_install_for_node = \
                node['management_plugins_to_install']
            self.assertEquals(1, len(management_plugins_to_install_for_node))
            plugin = management_plugins_to_install_for_node[0]
            self.assertEquals('test_management_plugin', plugin['name'])
            self.assertEquals('false', plugin['agent_plugin'])
            self.assertEquals('true', plugin['manager_plugin'])
            self.assertEquals('http://test_management_plugin.zip',
                              plugin['url'])

        # check the property on the plan is correct
        management_plugins_to_install_for_plan = \
            result["management_plugins_to_install"]
        self.assertEquals(1, len(management_plugins_to_install_for_plan))

        # check the boolean flag is correct
        is_management_plugins_to_install = \
            result["is_management_plugins_to_install"]
        self.assertTrue(is_management_plugins_to_install)

    def test_two_plugins_on_one_node(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host
            interfaces:
                test_interface:
                    - start: test_management_plugin1.start
                    - create: test_management_plugin2.create

types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start

plugins:
    test_management_plugin1:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin1.zip"
    test_management_plugin2:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin2.zip"
            """
        result = parse(yaml)
        management_plugins_to_install_for_node = \
            result['nodes'][0]['management_plugins_to_install']
        self.assertEquals(2, len(management_plugins_to_install_for_node))

        # check the property on the plan is correct
        management_plugins_to_install_for_plan = \
            result["management_plugins_to_install"]
        self.assertEquals(2, len(management_plugins_to_install_for_plan))

        # check the boolean flag is correct
        is_management_plugins_to_install = \
            result["is_management_plugins_to_install"]
        self.assertTrue(is_management_plugins_to_install)

    def test_no_operation_mapping_no_plugin(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host

types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_plugin.start

plugins:
    test_management_plugin:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin1.zip"
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            url: "http://test_plugin.zip"
            """
        result = parse(yaml)
        management_plugins_to_install_for_node = \
            result['nodes'][0]['management_plugins_to_install']
        self.assertEquals(0, len(management_plugins_to_install_for_node))

        # check the property on the plan is correct
        management_plugins_to_install_for_plan = \
            result["management_plugins_to_install"]
        self.assertEquals(0, len(management_plugins_to_install_for_plan))

        # check the boolean flag is correct
        is_management_plugins_to_install = \
            result["is_management_plugins_to_install"]
        self.assertFalse(is_management_plugins_to_install)

    def test_two_identical_plugins_on_node(self):
        yaml = """
blueprint:
    name: test_app
    nodes:
        -   name: test_node1
            type: cloudify.types.host

types:
    cloudify.types.host:
        interfaces:
            test_interface:
                - start: test_management_plugin.start
                - create: test_management_plugin.create

plugins:
    test_management_plugin:
        derived_from: "cloudify.plugins.manager_plugin"
        properties:
            url: "http://test_management_plugin1.zip"
            """
        result = parse(yaml)
        management_plugins_to_install_for_node = \
            result['nodes'][0]['management_plugins_to_install']
        self.assertEquals(1, len(management_plugins_to_install_for_node))

        # check the property on the plan is correct
        management_plugins_to_install_for_plan = \
            result["management_plugins_to_install"]
        self.assertEquals(1, len(management_plugins_to_install_for_plan))

        # check the boolean flag is correct
        is_management_plugins_to_install = \
            result["is_management_plugins_to_install"]
        self.assertTrue(is_management_plugins_to_install)
