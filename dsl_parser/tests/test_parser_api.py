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

import os
import yaml as yml
from urllib import pathname2url

from dsl_parser import exceptions
from dsl_parser import constants
from dsl_parser import version
from dsl_parser import models
from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser.parser import parse_from_path
from dsl_parser.parser import parse as dsl_parse
from dsl_parser.interfaces.constants import NO_OP
from dsl_parser.interfaces.utils import operation_mapping
from dsl_parser.constants import TYPE_HIERARCHY


def op_struct(plugin_name,
              mapping,
              inputs=None,
              executor=None,
              max_retries=None,
              retry_interval=None):
    if not inputs:
        inputs = {}
    result = {
        'plugin': plugin_name,
        'operation': mapping,
        'inputs': inputs,
        'executor': executor,
        'has_intrinsic_functions': False,
        'max_retries': max_retries,
        'retry_interval': retry_interval
    }
    return result


def workflow_op_struct(plugin_name,
                       mapping,
                       parameters=None):

    if not parameters:
        parameters = {}
    return {
        'plugin': plugin_name,
        'operation': mapping,
        'parameters': parameters
    }


class TestParserApi(AbstractTestParser):
    def _assert_minimal_blueprint(self, result, expected_type='test_type'):
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals(expected_type, node['type'])
        self.assertEquals('val', node['properties']['key'])
        # self.assertEquals(1, node['instances']['deploy'])

    def test_minimal_blueprint(self):
        result = self.parse(self.MINIMAL_BLUEPRINT)
        self._assert_minimal_blueprint(result)

    def test_import_from_path(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT])
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)

    def _assert_blueprint(self, result):
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        plugin_props = [p for p in node['plugins']
                        if p['name'] == 'test_plugin'][0]
        self.assertEquals(11, len(plugin_props))
        self.assertEquals('test_plugin',
                          plugin_props[constants.PLUGIN_NAME_KEY])
        operations = node['operations']
        self.assertEquals(op_struct('test_plugin', 'install',
                                    executor='central_deployment_agent'),
                          operations['install'])
        self.assertEquals(op_struct('test_plugin', 'install',
                                    executor='central_deployment_agent'),
                          operations['test_interface1.install'])
        self.assertEquals(op_struct('test_plugin', 'terminate',
                                    executor='central_deployment_agent'),
                          operations['terminate'])
        self.assertEquals(op_struct('test_plugin', 'terminate',
                                    executor='central_deployment_agent'),
                          operations['test_interface1.terminate'])

    def test_type_with_single_explicit_interface_and_plugin(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
                start:
                    implementation: test_plugin.start
                    inputs: {}
        properties:
            install_agent:
                default: false
            key: {}
            number:
                default: 80
            boolean:
                default: false
            complex:
                default:
                    key1: value1
                    key2: value2
            """

        result = self.parse(yaml)
        self._assert_blueprint(result)

    def test_type_with_interfaces_and_basic_plugin(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS
        result = self.parse(yaml)
        self._assert_blueprint(result)
        first_node = result['nodes'][0]
        parsed_plugins = first_node['plugins']
        expected_plugins = [{
            constants.PLUGIN_NAME_KEY: 'test_plugin',
            constants.PLUGIN_SOURCE_KEY: 'dummy',
            constants.PLUGIN_INSTALL_KEY: True,
            constants.PLUGIN_EXECUTOR_KEY: constants.CENTRAL_DEPLOYMENT_AGENT,
            constants.PLUGIN_INSTALL_ARGUMENTS_KEY: None,
            constants.PLUGIN_PACKAGE_NAME: None,
            constants.PLUGIN_PACKAGE_VERSION: None,
            constants.PLUGIN_SUPPORTED_PLATFORM: None,
            constants.PLUGIN_DISTRIBUTION: None,
            constants.PLUGIN_DISTRIBUTION_VERSION: None,
            constants.PLUGIN_DISTRIBUTION_RELEASE: None
        }]
        self.assertEquals(parsed_plugins, expected_plugins)

    def test_type_with_interface_and_plugin_with_install_args(self):
        yaml = self.PLUGIN_WITH_INTERFACES_AND_PLUGINS_WITH_INSTALL_ARGS
        result = self.parse(yaml,
                            dsl_version=self.BASIC_VERSION_SECTION_DSL_1_1)
        self._assert_blueprint(result)
        first_node = result['nodes'][0]
        parsed_plugins = first_node['plugins']
        expected_plugins = [{
            constants.PLUGIN_NAME_KEY: 'test_plugin',
            constants.PLUGIN_SOURCE_KEY: 'dummy',
            constants.PLUGIN_INSTALL_KEY: True,
            constants.PLUGIN_EXECUTOR_KEY: constants.CENTRAL_DEPLOYMENT_AGENT,
            constants.PLUGIN_INSTALL_ARGUMENTS_KEY: '-r requirements.txt',
            constants.PLUGIN_PACKAGE_NAME: None,
            constants.PLUGIN_PACKAGE_VERSION: None,
            constants.PLUGIN_SUPPORTED_PLATFORM: None,
            constants.PLUGIN_DISTRIBUTION: None,
            constants.PLUGIN_DISTRIBUTION_VERSION: None,
            constants.PLUGIN_DISTRIBUTION_RELEASE: None
        }]
        self.assertEquals(parsed_plugins, expected_plugins)

    def test_dsl_with_type_with_operation_mappings(self):
        yaml = self.create_yaml_with_imports(
            [self.BASIC_NODE_TEMPLATES_SECTION, self.BASIC_PLUGIN]) + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
            test_interface2:
                start:
                    implementation: other_test_plugin.start
                    inputs: {}
                shutdown:
                    implementation: other_test_plugin.shutdown
                    inputs: {}

plugins:
    other_test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        node = result['nodes'][0]
        self._assert_blueprint(result)

        operations = node['operations']
        self.assertEquals(op_struct('other_test_plugin', 'start',
                                    executor='central_deployment_agent'),
                          operations['start'])
        self.assertEquals(op_struct('other_test_plugin', 'start',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.shutdown'])

    def test_recursive_imports(self):
        bottom_level_yaml = self.BASIC_TYPE
        bottom_file_name = self.make_yaml_file(bottom_level_yaml)

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   {0}""".format(bottom_file_name)
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
imports:
    -   {0}""".format(mid_file_name)

        result = self.parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_parse_dsl_from_file(self):
        filename = self.make_yaml_file(self.BASIC_VERSION_SECTION_DSL_1_0 +
                                       self.MINIMAL_BLUEPRINT)
        result = parse_from_path(filename)
        self._assert_minimal_blueprint(result)

    def test_import_empty_list(self):
        yaml = self.MINIMAL_BLUEPRINT + """
imports: []
        """
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_blueprint_description_field(self):
        yaml = self.MINIMAL_BLUEPRINT + self.BASIC_VERSION_SECTION_DSL_1_2 +\
            """
description: sample description
        """
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertIn('description', result)
        self.assertEquals('sample description', result['description'])

    def test_blueprint_description_field_omitted(self):
        yaml = self.MINIMAL_BLUEPRINT + self.BASIC_VERSION_SECTION_DSL_1_2
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertIn('description', result)
        self.assertEquals(None, result['description'])

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

        top_level_yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
imports:
    -   {0}
    -   {1}""".format(mid_file_name, mid_file_name2)
        result = self.parse(top_level_yaml)
        self._assert_blueprint(result)

    def _create_importable_yaml_for_version_1_3_and_above(self, importable):
        imported_yaml = self.make_yaml_file(
            self.BASIC_TYPE +
            self.BASIC_PLUGIN +
            importable)
        main_yaml = """
imports:
    -   {0}""".format(imported_yaml) + \
            self.BASIC_NODE_TEMPLATES_SECTION + \
            self.BASIC_INPUTS + \
            self.BASIC_OUTPUTS

        return main_yaml

    def _verify_1_2_and_below_non_mergeable_imports(self,
                                                    importable,
                                                    import_type):
        main_yaml = self._create_importable_yaml_for_version_1_3_and_above(
            importable)
        ex = self.assertRaises(
            exceptions.DSLParsingLogicException,
            self.parse_1_2, main_yaml)
        self.assertIn("Import failed: non-mergeable field: '{0}'".format(
            import_type), str(ex))

    def _verify_1_3_and_above_mergeable_imports(self, importable):
        main_yaml = self._create_importable_yaml_for_version_1_3_and_above(
            importable)
        result = self.parse_1_3(main_yaml)
        self._assert_blueprint(result)

    def test_version_1_2_and_above_input_imports(self):
        importable = """
inputs:
    test_input2:
        default: value
"""
        self._verify_1_2_and_below_non_mergeable_imports(
            importable, 'inputs')
        self._verify_1_3_and_above_mergeable_imports(importable)

    def test_version_1_2_and_above_node_template_imports(self):
        importable = """
node_templates:
    test_node2:
        type: test_type
        properties:
            key: "val"
"""
        self._verify_1_2_and_below_non_mergeable_imports(
            importable, 'node_templates')
        self._verify_1_3_and_above_mergeable_imports(importable)

    def test_version_1_2_and_above_output_imports(self):
        importable = """
outputs:
    test_output2:
        value: value
"""
        self._verify_1_2_and_below_non_mergeable_imports(
            importable, 'outputs')
        self._verify_1_3_and_above_mergeable_imports(importable)

    def test_node_get_type_properties_including_overriding_properties(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
    """
        result = self.parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])

    def test_type_properties_empty_properties(self):
        yaml = """
node_templates:
    test_node:
        type: test_type
node_types:
    test_type:
        properties: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals('test_type', node['type'])

    def test_type_properties_empty_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])
        # TODO: assert node-type's default and description values once
        # 'node_types' is part of the parser's output

    def test_type_properties_property_with_description_only(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                description: property_desc
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])
        # TODO: assert type's default and description values once 'type' is
        # part of the parser's output

    def test_type_properties_standard_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: val
                description: property_desc
                type: string
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_node', node['name'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])
        # TODO: assert type's default and description values once 'type' is
        # part of the parser's output

    def test_type_properties_derivation(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            key:
                default: "val1_parent"
            key2:
                default: "val2_parent"
            key3:
                default: "val3_parent"
    """
        result = self.parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_parent', node['properties']['key3'])

    def test_empty_types_hierarchy_in_node(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
    """
        result = self.parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(1, len(node[TYPE_HIERARCHY]))
        self.assertEqual('test_type', node[TYPE_HIERARCHY][0])

    def test_types_hierarchy_in_node(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        derived_from: "test_type_parent"
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
    test_type_parent: {}
    """
        result = self.parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(2, len(node[TYPE_HIERARCHY]))
        self.assertEqual('test_type_parent', node[TYPE_HIERARCHY][0])
        self.assertEqual('test_type', node[TYPE_HIERARCHY][1])

    def test_types_hierarchy_order_in_node(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        derived_from: "test_type_parent"
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
    test_type_parent:
        derived_from: "parent_type"

    parent_type: {}
    """
        result = self.parse(yaml)
        node = result['nodes'][0]
        self.assertEqual(3, len(node[TYPE_HIERARCHY]))
        self.assertEqual('parent_type', node[TYPE_HIERARCHY][0])
        self.assertEqual('test_type_parent', node[TYPE_HIERARCHY][1])
        self.assertEqual('test_type', node[TYPE_HIERARCHY][2])

    def test_type_properties_recursive_derivation(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
            key2:
                default: "val2"
        derived_from: "test_type_parent"

    test_type_parent:
        properties:
            key:
                default: "val_parent"
            key2:
                default: "val2_parent"
            key4:
                default: "val4_parent"
        derived_from: "test_type_grandparent"

    test_type_grandparent:
        properties:
            key:
                default: "val1_grandparent"
            key2:
                default: "val2_grandparent"
            key3:
                default: "val3_grandparent"
        derived_from: "test_type_grandgrandparent"

    test_type_grandgrandparent: {}
    """
        result = self.parse(yaml)
        # this will also check property "key" = "val"
        self._assert_minimal_blueprint(result)
        node = result['nodes'][0]
        self.assertEquals('val2', node['properties']['key2'])
        self.assertEquals('val3_grandparent', node['properties']['key3'])
        self.assertEquals('val4_parent', node['properties']['key4'])

    def test_type_interface_derivation(self):
        yaml = self.create_yaml_with_imports(
            [self.BASIC_NODE_TEMPLATES_SECTION, self.BASIC_PLUGIN]) + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
            test_interface2:
                start:
                    implementation: test_plugin2.start
                    inputs: {}
                stop:
                    implementation: test_plugin2.stop
                    inputs: {}
            test_interface3:
                op1:
                    implementation: test_plugin3.op
                    inputs: {}
        derived_from: test_type_parent

    test_type_parent:
        interfaces:
            test_interface1:
                install:
                    implementation: nop_plugin.install
                    inputs: {}
                terminate:
                    implementation: nop_plugin.install
                    inputs: {}
            test_interface2:
                start:
                    implementation: test_plugin2.start
                    inputs: {}
                stop:
                    implementation: test_plugin2.stop
                    inputs: {}
            test_interface3:
                op1:
                    implementation: test_plugin3.op
                    inputs: {}
            test_interface4:
                op2:
                    implementation: test_plugin4.op2
                    inputs: {}

plugins:
    test_plugin2:
        executor: central_deployment_agent
        source: dummy
    test_plugin3:
        executor: central_deployment_agent
        source: dummy
    test_plugin4:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self._assert_blueprint(result)
        node = result['nodes'][0]
        operations = node['operations']
        self.assertEquals(12, len(operations))
        self.assertEquals(op_struct('test_plugin2', 'start',
                                    executor='central_deployment_agent'),
                          operations['start'])
        self.assertEquals(op_struct('test_plugin2', 'start',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('test_plugin2', 'stop',
                                    executor='central_deployment_agent'),
                          operations['stop'])
        self.assertEquals(op_struct('test_plugin2', 'stop',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.stop'])
        self.assertEquals(op_struct('test_plugin3', 'op',
                                    executor='central_deployment_agent'),
                          operations['op1'])
        self.assertEquals(op_struct('test_plugin3', 'op',
                                    executor='central_deployment_agent'),
                          operations['test_interface3.op1'])
        self.assertEquals(op_struct('test_plugin4', 'op2',
                                    executor='central_deployment_agent'),
                          operations['op2'])
        self.assertEquals(op_struct('test_plugin4', 'op2',
                                    executor='central_deployment_agent'),
                          operations['test_interface4.op2'])
        self.assertEquals(4, len(node['plugins']))

    def test_type_interface_recursive_derivation(self):
        yaml = self.create_yaml_with_imports(
            [self.BASIC_NODE_TEMPLATES_SECTION, self.BASIC_PLUGIN]) + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
        derived_from: test_type_parent

    test_type_parent:
        derived_from: test_type_grandparent

    test_type_grandparent:
        interfaces:
            test_interface1:
                install:
                    implementation: non_plugin.install
                    inputs: {}
                terminate:
                    implementation: non_plugin.terminate
                    inputs: {}
            test_interface2:
                start:
                    implementation: test_plugin2.start
                    inputs: {}
                stop:
                    implementation: test_plugin2.stop
                    inputs: {}

plugins:
    test_plugin2:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self._assert_blueprint(result)
        node = result['nodes'][0]
        operations = node['operations']
        self.assertEquals(8, len(operations))
        self.assertEquals(op_struct('test_plugin2', 'start',
                                    executor='central_deployment_agent'),
                          operations['start'])
        self.assertEquals(op_struct('test_plugin2', 'start',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('test_plugin2', 'stop',
                                    executor='central_deployment_agent'),
                          operations['stop'])
        self.assertEquals(op_struct('test_plugin2', 'stop',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.stop'])
        self.assertEquals(2, len(node['plugins']))

    def test_two_explicit_interfaces_with_same_operation_name(self):
        yaml = self.create_yaml_with_imports(
            [self.BASIC_NODE_TEMPLATES_SECTION, self.BASIC_PLUGIN]) + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
            test_interface2:
                install:
                    implementation: other_test_plugin.install
                    inputs: {}
                shutdown:
                    implementation: other_test_plugin.shutdown
                    inputs: {}
plugins:
    other_test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        operations = node['operations']
        self.assertEquals(op_struct('test_plugin', 'install',
                                    executor='central_deployment_agent'),
                          operations['test_interface1.install'])
        self.assertEquals(op_struct('test_plugin', 'terminate',
                                    executor='central_deployment_agent'),
                          operations['terminate'])
        self.assertEquals(op_struct('test_plugin', 'terminate',
                                    executor='central_deployment_agent'),
                          operations['test_interface1.terminate'])
        self.assertEquals(op_struct('other_test_plugin', 'install',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.install'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.shutdown'])
        self.assertEquals(6, len(operations))

    def test_relative_path_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
imports:
    -   {0}""".format(mid_file_name)
        result = self.parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_import_from_file_uri(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT], True)
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_relative_file_uri_import(self):
        bottom_level_yaml = self.BASIC_TYPE
        self.make_file_with_name(bottom_level_yaml, 'bottom_level.yaml')

        mid_level_yaml = self.BASIC_PLUGIN + """
imports:
    -   \"bottom_level.yaml\""""
        mid_file_name = self.make_yaml_file(mid_level_yaml)

        top_level_yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
imports:
    -   {0}""".format('file:///' + pathname2url(mid_file_name))
        result = self.parse(top_level_yaml)
        self._assert_blueprint(result)

    def test_empty_top_level_relationships(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships: {}
                        """
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertEquals(0, len(result['relationships']))

    def test_empty_top_level_relationships_empty_relationship(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship: {}
                        """
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertEqual({'name': 'test_relationship', 'properties': {},
                          'source_interfaces': {}, 'target_interfaces': {},
                          'type_hierarchy': ['test_relationship']},
                         result['relationships']['test_relationship'])

    def test_top_level_relationships_single_complete_relationship(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    empty_rel: {}
    test_relationship:
        derived_from: empty_rel
        source_interfaces:
            test_interface3:
                test_interface3_op1: {}
        target_interfaces:
            test_interface4:
                test_interface4_op1:
                    implementation: test_plugin.task_name
                    inputs: {}
        """
        result = self.parse(yaml)
        self._assert_blueprint(result)
        self.assertEqual({'name': 'empty_rel', 'properties': {},
                          'source_interfaces': {},
                          'target_interfaces': {},
                          'type_hierarchy': ['empty_rel']},
                         result['relationships']['empty_rel'])
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('test_relationship', test_relationship['name'])
        self.assertEquals(test_relationship['type_hierarchy'],
                          ['empty_rel', 'test_relationship'])
        result_test_interface_3 = \
            test_relationship['source_interfaces']['test_interface3']
        self.assertEquals(NO_OP,
                          result_test_interface_3['test_interface3_op1'])
        result_test_interface_4 = \
            test_relationship['target_interfaces']['test_interface4']
        self.assertEquals(
            operation_mapping(implementation='test_plugin.task_name',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            result_test_interface_4['test_interface4_op1'])

    def test_top_level_relationships_recursive_imports(self):
        bottom_level_yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
relationships:
    empty_rel: {}
    test_relationship:
        derived_from: empty_rel
        source_interfaces:
            test_interface2:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
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
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}

imports:
    - """ + mid_file_name

        result = self.parse(top_level_yaml)
        self._assert_blueprint(result)
        self.assertEqual({'name': 'empty_rel', 'properties': {},
                          'source_interfaces': {}, 'target_interfaces': {},
                          'type_hierarchy': ['empty_rel']},
                         result['relationships']['empty_rel'])
        test_relationship = result['relationships']['test_relationship']
        self.assertEquals('test_relationship',
                          test_relationship['name'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship['source_interfaces'][
                'test_interface2']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship['source_interfaces'][
                'test_interface2']['terminate'])
        self.assertEquals(
            2, len(test_relationship['source_interfaces'][
                'test_interface2']))
        self.assertEquals(6, len(test_relationship))

        test_relationship2 = result['relationships']['test_relationship2']
        self.assertEquals('test_relationship2',
                          test_relationship2['name'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship2['target_interfaces'][
                'test_interface2']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship2['target_interfaces'][
                'test_interface2']['terminate'])
        self.assertEquals(
            2, len(test_relationship2['target_interfaces'][
                'test_interface2']))
        self.assertEquals(6, len(test_relationship2))

        test_relationship3 = result['relationships']['test_relationship3']
        self.assertEquals('test_relationship3', test_relationship3['name'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship3['target_interfaces'][
                'test_interface2']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            test_relationship3['target_interfaces'][
                'test_interface2']['terminate'])
        self.assertEquals(
            2, len(test_relationship3['target_interfaces'][
                'test_interface2']))
        self.assertEquals(5, len(test_relationship3))

    def test_top_level_relationship_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            without_default_value: {}
            with_simple_default_value:
                default: 1
            with_object_default_value:
                default:
                    comp1: 1
                    comp2: 2
"""
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        relationships = result['relationships']
        self.assertEquals(1, len(relationships))
        test_relationship = relationships['test_relationship']
        properties = test_relationship['properties']
        self.assertIn('without_default_value', properties)
        self.assertIn('with_simple_default_value', properties)
        self.assertEquals({'default': 1}, properties[
            'with_simple_default_value'])
        self.assertEquals({'default': {'comp1': 1, 'comp2': 2}}, properties[
            'with_object_default_value'])

    def test_top_level_relationship_properties_inheritance(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship1:
        properties:
            prop1: {}
            prop2: {}
            prop3:
                default: prop3_value_1
            derived1:
                default: derived1_value
    test_relationship2:
        derived_from: test_relationship1
        properties:
            prop2:
                default: prop2_value_2
            prop3:
                default: prop3_value_2
            prop4: {}
            prop5: {}
            prop6:
                default: prop6_value_2
            derived2:
                default: derived2_value
    test_relationship3:
        derived_from: test_relationship2
        properties:
            prop5:
                default: prop5_value_3
            prop6:
                default: prop6_value_3
            prop7: {}
"""
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        relationships = result['relationships']
        self.assertEquals(3, len(relationships))
        r1_properties = relationships['test_relationship1']['properties']
        r2_properties = relationships['test_relationship2']['properties']
        r3_properties = relationships['test_relationship3']['properties']
        self.assertEquals(4, len(r1_properties))
        self.assertIn('prop1', r1_properties)
        self.assertIn('prop2', r1_properties)
        self.assertIn('prop3', r1_properties)
        self.assertIn('derived1', r1_properties)
        self.assertEquals({'default': 'prop3_value_1'}, r1_properties['prop3'])
        self.assertEquals({'default': 'derived1_value'}, r1_properties[
            'derived1'])
        self.assertEquals(8, len(r2_properties))
        self.assertIn('prop1', r2_properties)
        self.assertIn('prop2', r2_properties)
        self.assertIn('prop3', r2_properties)
        self.assertIn('prop4', r2_properties)
        self.assertIn('prop5', r2_properties)
        self.assertIn('prop6', r2_properties)
        self.assertIn('derived1', r2_properties)
        self.assertIn('derived2', r2_properties)
        self.assertEquals({'default': 'prop2_value_2'}, r2_properties[
            'prop2'])
        self.assertEquals({'default': 'prop3_value_2'}, r2_properties[
            'prop3'])
        self.assertEquals({'default': 'prop6_value_2'}, r2_properties[
            'prop6'])
        self.assertEquals({'default': 'derived1_value'}, r2_properties[
            'derived1'])
        self.assertEquals({'default': 'derived2_value'}, r2_properties[
            'derived2'])
        self.assertEquals(9, len(r3_properties))
        self.assertIn('prop1', r3_properties)
        self.assertIn('prop2', r3_properties)
        self.assertIn('prop3', r3_properties)
        self.assertIn('prop4', r3_properties)
        self.assertIn('prop5', r3_properties)
        self.assertIn('prop6', r3_properties)
        self.assertIn('prop7', r3_properties)
        self.assertIn('derived1', r3_properties)
        self.assertIn('derived2', r3_properties)
        self.assertEquals({'default': 'prop2_value_2'}, r3_properties[
            'prop2'])
        self.assertEquals({'default': 'prop3_value_2'}, r3_properties[
            'prop3'])
        self.assertEquals({'default': 'prop5_value_3'}, r3_properties[
            'prop5'])
        self.assertEquals({'default': 'prop6_value_3'}, r3_properties[
            'prop6'])
        self.assertEquals({'default': 'derived1_value'}, r3_properties[
            'derived1'])
        self.assertEquals({'default': 'derived2_value'}, r3_properties[
            'derived2'])

    def test_instance_relationships_empty_relationships_section(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships: []
                """
        result = self.parse(yaml)
        self._assert_minimal_blueprint(result)
        self.assertTrue(isinstance(result['nodes'][0]['relationships'], list))
        self.assertEqual(0, len(result['nodes'][0]['relationships']))

    def test_instance_relationships_standard_relationship(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
                source_interfaces:
                    test_interface1:
                        install: test_plugin.install
relationships:
    test_relationship: {}
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        self.assertEquals('test_node2', nodes[1]['id'])
        self.assertEquals(1, len(nodes[1]['relationships']))
        relationship = nodes[1]['relationships'][0]
        self.assertEquals('test_relationship', relationship['type'])
        self.assertEquals('test_node', relationship['target_id'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces']['test_interface1']['install'])
        relationship_source_operations = relationship['source_operations']
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         relationship_source_operations['install'])
        self.assertEqual(
            op_struct('test_plugin', 'install',
                      executor='central_deployment_agent'),
            relationship_source_operations['test_interface1.install'])
        self.assertEqual(2, len(relationship_source_operations))

        self.assertEquals(8, len(relationship))
        plugin_def = nodes[1]['plugins'][0]
        self.assertEquals('test_plugin', plugin_def['name'])

    def test_instance_relationships_duplicate_relationship(self):
        # right now, having two relationships with the same (type,target)
        # under one node is valid
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
            -   type: test_relationship
                target: test_node
relationships:
    test_relationship: {}
                    """
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        self.assertEquals('test_node2', nodes[1]['id'])
        self.assertEquals(2, len(nodes[1]['relationships']))
        self.assertEquals('test_relationship',
                          nodes[1]['relationships'][0]['type'])
        self.assertEquals('test_relationship',
                          nodes[1]['relationships'][1]['type'])
        self.assertEquals('test_node',
                          nodes[1]['relationships'][0]['target_id'])
        self.assertEquals('test_node',
                          nodes[1]['relationships'][1]['target_id'])
        self.assertEquals(8, len(nodes[1]['relationships'][0]))
        self.assertEquals(8, len(nodes[1]['relationships'][1]))

    def test_instance_relationships_relationship_inheritance(self):
        # possibly 'inheritance' is the wrong term to use here,
        # the meaning is for checking that the relationship properties from the
        # top-level relationships
        # section are used for instance-relationships which declare their types
        # note there are no overrides in this case; these are tested in the
        # next, more thorough test
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
                source_interfaces:
                    interface1:
                        op1: test_plugin.task_name1
relationships:
    relationship: {}
    test_relationship:
        derived_from: relationship
        target_interfaces:
            interface2:
                op2:
                    implementation: test_plugin.task_name2
                    inputs: {}
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationship = nodes[1]['relationships'][0]
        self.assertEquals('test_relationship', relationship['type'])
        self.assertEquals('test_node', relationship['target_id'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.task_name1',
                              inputs={}, executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces']['interface1']['op1'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.task_name2',
                              inputs={}, executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['target_interfaces']['interface2']['op2'])

        rel_source_ops = relationship['source_operations']

        self.assertEqual(op_struct('test_plugin', 'task_name1',
                                   executor='central_deployment_agent'),
                         rel_source_ops['op1'])
        self.assertEqual(op_struct('test_plugin', 'task_name1',
                                   executor='central_deployment_agent'),
                         rel_source_ops['interface1.op1'])
        self.assertEquals(2, len(rel_source_ops))

        rel_target_ops = relationship['target_operations']
        self.assertEqual(op_struct('test_plugin', 'task_name2',
                                   executor='central_deployment_agent'),
                         rel_target_ops['op2'])
        self.assertEqual(op_struct('test_plugin', 'task_name2',
                                   executor='central_deployment_agent'),
                         rel_target_ops['interface2.op2'])
        self.assertEquals(2, len(rel_target_ops))

        self.assertEquals(8, len(relationship))

    def test_instance_relationship_properties_inheritance(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
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
            prop1: {}
            prop2: {}
            prop7: {}
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationships = result['relationships']
        self.assertEquals(1, len(relationships))
        i_properties = nodes[1]['relationships'][0]['properties']
        self.assertEquals(3, len(i_properties))
        self.assertEquals('prop1_value_new', i_properties['prop1'])
        self.assertEquals('prop2_value_new', i_properties['prop2'])
        self.assertEquals('prop7_value_new_instance', i_properties['prop7'])

    def test_relationships_and_node_recursive_inheritance(self):
        # testing for a complete inheritance path for relationships
        # from top-level relationships to a relationship instance
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: relationship
                target: test_node
                source_interfaces:
                    test_interface3:
                        install: test_plugin.install
                target_interfaces:
                    test_interface1:
                        install: test_plugin.install
relationships:
    relationship:
        derived_from: parent_relationship
        source_interfaces:
            test_interface2:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
    parent_relationship:
        target_interfaces:
            test_interface3:
                install: {}
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        node_relationship = nodes[1]['relationships'][0]
        relationship = result['relationships']['relationship']
        parent_relationship = result['relationships']['parent_relationship']
        self.assertEquals(2, len(result['relationships']))
        self.assertEquals(5, len(parent_relationship))
        self.assertEquals(6, len(relationship))
        self.assertEquals(8, len(node_relationship))

        self.assertEquals('parent_relationship', parent_relationship['name'])
        self.assertEquals(1, len(parent_relationship['target_interfaces']))
        self.assertEquals(1, len(parent_relationship['target_interfaces']
                                                    ['test_interface3']))
        self.assertEquals(
            {'implementation': '', 'inputs': {}, 'executor': None,
             'max_retries': None, 'retry_interval': None},
            parent_relationship['target_interfaces'][
                'test_interface3']['install'])

        self.assertEquals('relationship', relationship['name'])
        self.assertEquals('parent_relationship', relationship['derived_from'])
        self.assertEquals(1, len(relationship['target_interfaces']))
        self.assertEquals(1, len(relationship['target_interfaces']
                                             ['test_interface3']))
        self.assertEquals(
            NO_OP,
            relationship['target_interfaces']['test_interface3']['install'])
        self.assertEquals(1, len(relationship['source_interfaces']))
        self.assertEquals(2, len(relationship['source_interfaces']
                                             ['test_interface2']))
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces']['test_interface2']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces'][
                'test_interface2']['terminate'])

        self.assertEquals('relationship', node_relationship['type'])
        self.assertEquals('test_node', node_relationship['target_id'])
        self.assertEquals(2, len(node_relationship['target_interfaces']))
        self.assertEquals(1, len(node_relationship['target_interfaces']
                                                  ['test_interface3']))
        self.assertEquals(
            NO_OP,
            node_relationship['target_interfaces'][
                'test_interface3']['install'])
        self.assertEquals(1, len(node_relationship['target_interfaces']
                                                  ['test_interface1']))
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['target_interfaces'][
                'test_interface1']['install'])
        self.assertEquals(2, len(node_relationship['source_interfaces']))
        self.assertEquals(1, len(node_relationship['source_interfaces']
                                                  ['test_interface3']))
        self.assertEquals(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['source_interfaces'][
                'test_interface2']['install'])
        self.assertEquals(2, len(node_relationship['source_interfaces']
                                                  ['test_interface2']))
        self.assertEquals(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['source_interfaces'][
                'test_interface2']['install'])
        self.assertEquals(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['source_interfaces'][
                'test_interface2']['terminate'])

        rel_source_ops = node_relationship['source_operations']
        self.assertEquals(4, len(rel_source_ops))
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface2.install'])
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface3.install'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_source_ops['terminate'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface2.terminate'])

        rel_target_ops = node_relationship['target_operations']
        self.assertEquals(2, len(rel_target_ops))
        self.assertEqual(op_struct('', '', {}),
                         rel_target_ops['test_interface3.install'])
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         rel_target_ops['test_interface1.install'])

    def test_relationship_interfaces_inheritance_merge(self):
        # testing for a complete inheritance path for relationships
        # from top-level relationships to a relationship instance
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: relationship
                target: test_node
                target_interfaces:
                    test_interface:
                        destroy: test_plugin.destroy1
                source_interfaces:
                    test_interface:
                        install2: test_plugin.install2
                        destroy2: test_plugin.destroy2
relationships:
    parent_relationship:
        target_interfaces:
            test_interface:
                install: {}
        source_interfaces:
            test_interface:
                install2: {}
    relationship:
        derived_from: parent_relationship
        target_interfaces:
            test_interface:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
        source_interfaces:
            test_interface:
                install2:
                    implementation: test_plugin.install
                    inputs: {}
                terminate2:
                    implementation: test_plugin.terminate
                    inputs: {}

plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        node_relationship = nodes[1]['relationships'][0]
        relationship = result['relationships']['relationship']
        parent_relationship = result['relationships']['parent_relationship']
        self.assertEquals(2, len(result['relationships']))
        self.assertEquals(5, len(parent_relationship))
        self.assertEquals(6, len(relationship))
        self.assertEquals(8, len(node_relationship))

        self.assertEquals('parent_relationship', parent_relationship['name'])
        self.assertEquals(1, len(parent_relationship['target_interfaces']))
        self.assertEquals(1, len(parent_relationship['target_interfaces']
                                                    ['test_interface']))
        self.assertIn('install', parent_relationship['target_interfaces']
                                                    ['test_interface'])
        self.assertEquals(1, len(parent_relationship['source_interfaces']))
        self.assertEquals(1, len(parent_relationship['source_interfaces']
                                                    ['test_interface']))
        self.assertIn('install2', parent_relationship[
            'source_interfaces']['test_interface'])

        self.assertEquals('relationship', relationship['name'])
        self.assertEquals('parent_relationship', relationship['derived_from'])
        self.assertEquals(1, len(relationship['target_interfaces']))
        self.assertEquals(2, len(relationship['target_interfaces']
                                             ['test_interface']))
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['target_interfaces']['test_interface']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={}, executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['target_interfaces'][
                'test_interface']['terminate'])
        self.assertEquals(1, len(relationship['source_interfaces']))
        self.assertEquals(
            2, len(relationship['source_interfaces']['test_interface']))
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install', inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces']['test_interface']['install2'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces'][
                'test_interface']['terminate2'])

        self.assertEquals('relationship', node_relationship['type'])
        self.assertEquals('test_node', node_relationship['target_id'])
        self.assertEquals(1, len(node_relationship['target_interfaces']))
        self.assertEquals(
            3, len(node_relationship['target_interfaces']['test_interface']))
        self.assertEqual(
            operation_mapping(implementation='test_plugin.install',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['target_interfaces'][
                'test_interface']['install'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['target_interfaces'][
                'test_interface']['terminate'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.destroy1',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['target_interfaces'][
                'test_interface']['destroy'])
        self.assertEquals(1, len(node_relationship['source_interfaces']))
        self.assertEquals(
            3, len(node_relationship['source_interfaces'][
                'test_interface']))
        self.assertEquals(
            operation_mapping(implementation='test_plugin.install2',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['source_interfaces'][
                'test_interface']['install2'])
        self.assertEqual(
            operation_mapping(implementation='test_plugin.terminate',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            relationship['source_interfaces']['test_interface']['terminate2'])
        self.assertEquals(
            operation_mapping(implementation='test_plugin.destroy2',
                              inputs={},
                              executor=None,
                              max_retries=None,
                              retry_interval=None),
            node_relationship['source_interfaces'][
                'test_interface']['destroy2'])

        rel_source_ops = node_relationship['source_operations']
        self.assertEqual(op_struct('test_plugin', 'install2',
                                   executor='central_deployment_agent'),
                         rel_source_ops['install2'])
        self.assertEqual(op_struct('test_plugin', 'install2',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface.install2'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_source_ops['terminate2'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface.terminate2'])
        self.assertEqual(op_struct('test_plugin', 'destroy2',
                                   executor='central_deployment_agent'),
                         rel_source_ops['destroy2'])
        self.assertEqual(op_struct('test_plugin', 'destroy2',
                                   executor='central_deployment_agent'),
                         rel_source_ops['test_interface.destroy2'])
        self.assertEquals(6, len(rel_source_ops))

        rel_target_ops = node_relationship['target_operations']
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         rel_target_ops['install'])
        self.assertEqual(op_struct('test_plugin', 'install',
                                   executor='central_deployment_agent'),
                         rel_target_ops['test_interface.install'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_target_ops['terminate'])
        self.assertEqual(op_struct('test_plugin', 'terminate',
                                   executor='central_deployment_agent'),
                         rel_target_ops['test_interface.terminate'])
        self.assertEqual(op_struct('test_plugin', 'destroy1',
                                   executor='central_deployment_agent'),
                         rel_target_ops['destroy'])
        self.assertEqual(op_struct('test_plugin', 'destroy1',
                                   executor='central_deployment_agent'),
                         rel_target_ops['test_interface.destroy'])
        self.assertEquals(6, len(rel_source_ops))

    def test_relationship_no_type_hierarchy(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: relationship
                target: test_node
relationships:
    relationship: {}
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationship = nodes[1]['relationships'][0]
        self.assertTrue('type_hierarchy' in relationship)
        type_hierarchy = relationship['type_hierarchy']
        self.assertEqual(1, len(type_hierarchy))
        self.assertEqual('relationship', type_hierarchy[0])

    def test_relationship_type_hierarchy(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: rel2
                target: test_node
relationships:
    relationship: {}
    rel2:
        derived_from: relationship
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationship = nodes[1]['relationships'][0]
        self.assertTrue('type_hierarchy' in relationship)
        type_hierarchy = relationship['type_hierarchy']
        self.assertEqual(2, len(type_hierarchy))
        self.assertEqual('relationship', type_hierarchy[0])
        self.assertEqual('rel2', type_hierarchy[1])

    def test_relationship_3_types_hierarchy(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: rel3
                target: test_node
relationships:
    relationship: {}
    rel2:
        derived_from: relationship
    rel3:
        derived_from: rel2
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationship = nodes[1]['relationships'][0]
        self.assertTrue('type_hierarchy' in relationship)
        type_hierarchy = relationship['type_hierarchy']
        self.assertEqual(3, len(type_hierarchy))
        self.assertEqual('relationship', type_hierarchy[0])
        self.assertEqual('rel2', type_hierarchy[1])
        self.assertEqual('rel3', type_hierarchy[2])

    def test_agent_plugin_in_node_contained_in_host_contained_in_container(self):  # noqa
        yaml = """
plugins:
  plugin:
    executor: host_agent
    source: source
node_templates:
  compute:
    type: cloudify.nodes.Compute
    relationships:
      - target: container
        type: cloudify.relationships.contained_in
  container:
    type: container
  app:
    type: app
    interfaces:
      interface:
        operation: plugin.operation
    relationships:
      - target: compute
        type: cloudify.relationships.contained_in
node_types:
  cloudify.nodes.Compute: {}
  container: {}
  app: {}
relationships:
  cloudify.relationships.contained_in: {}
"""
        result = self.parse(yaml)
        self.assertEqual('compute',
                         self.get_node_by_name(result, 'compute')['host_id'])

    def test_node_host_id_field(self):
        yaml = """
node_templates:
    test_node:
        type: cloudify.nodes.Compute
        properties:
            key: "val"
node_types:
    cloudify.nodes.Compute:
        properties:
            key: {}
            """
        result = self.parse(yaml)
        self.assertEquals('test_node', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
    test_node2:
        type: another_type
        relationships:
            -   type: cloudify.relationships.contained_in
                target: test_node1
    test_node3:
        type: another_type
        relationships:
            -   type: cloudify.relationships.contained_in
                target: test_node2
node_types:
    cloudify.nodes.Compute: {}
    another_type: {}

relationships:
    cloudify.relationships.contained_in: {}
            """
        result = self.parse(yaml)
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])
        self.assertEquals('test_node1', result['nodes'][2]['host_id'])

    def test_node_host_id_field_via_node_supertype(self):
        yaml = """
node_templates:
    test_node1:
        type: another_type
node_types:
    cloudify.nodes.Compute: {}
    another_type:
        derived_from: cloudify.nodes.Compute
            """
        result = self.parse(yaml)
        self.assertEquals('test_node1', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship_derived_from_inheritance(
            self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
    test_node2:
        type: another_type
        relationships:
            -   type: test_relationship
                target: test_node1
node_types:
    cloudify.nodes.Compute: {}
    another_type: {}
relationships:
    cloudify.relationships.contained_in: {}
    test_relationship:
        derived_from: cloudify.relationships.contained_in
            """
        result = self.parse(yaml)
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])

    def test_node_type_operation_override(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.MyCompute
node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start: test_plugin.start
    cloudify.nodes.MyCompute:
        derived_from: cloudify.nodes.Compute
        interfaces:
            test_interface:
                start: test_plugin.overriding_start

plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        start_operation = result['nodes'][0]['operations']['start']
        self.assertEqual('overriding_start', start_operation['operation'])

    def test_node_type_node_template_operation_override(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
        interfaces:
            test_interface:
                start: test_plugin.overriding_start

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start: test_plugin.start

plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        start_operation = result['nodes'][0]['operations']['start']
        self.assertEqual('overriding_start', start_operation['operation'])

    def test_executor_override_node_types(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.MyCompute
node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    executor: central_deployment_agent
                    implementation: test_plugin.start
                    inputs: {}
    cloudify.nodes.MyCompute:
        derived_from: cloudify.nodes.Compute
        interfaces:
            test_interface:
                start:
                    executor: host_agent
                    implementation: test_plugin.start
                    inputs: {}

plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0]['plugins_to_install']))

    def test_executor_override_plugin_declaration(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    executor: central_deployment_agent
                    implementation: test_plugin.start
                    inputs: {}

plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        plugin = result['nodes'][0]['deployment_plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0][
            'deployment_plugins_to_install']))

    def test_executor_override_type_declaration(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
        interfaces:
            test_interface:
                start:
                    executor: host_agent
                    inputs: {}

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    executor: central_deployment_agent
                    implementation: test_plugin.start
                    inputs: {}

plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0][
            'plugins_to_install']))

    def test_import_resources(self):
        resource_file_name = 'resource_file.yaml'
        file_path = self.make_file_with_name(
            self.MINIMAL_BLUEPRINT, resource_file_name, 'resources')
        resources_base_path = os.path.dirname(file_path)
        yaml = """
imports:
    -   {0}""".format(resource_file_name)
        result = self.parse(yaml, resources_base_path=resources_base_path)
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

        top_level_yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
imports:
    -   {0}""".format(mid_file_name)

        result = self.parse(top_level_yaml)
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

        top_level_yaml = \
            self.BASIC_VERSION_SECTION_DSL_1_0 + \
            self.BASIC_NODE_TEMPLATES_SECTION +\
            """
imports:
    -   {0}""".format(mid_file_name)
        top_file_name = self.make_file_with_name(
            top_level_yaml, 'top_level.yaml')
        result = parse_from_path(top_file_name)
        self._assert_blueprint(result)

    def test_node_without_host_id(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
    test_node2:
        type: cloudify.nodes.Compute
node_types:
    cloudify.nodes.Compute: {}
    test_type:
        properties:
            key: {}
        """
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        self.assertFalse('host_id' in nodes[0])
        self.assertEquals('test_node2', nodes[1]['host_id'])

    def test_multiple_instances(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: 2
            """
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        self.assertEquals('val', node['properties']['key'])
        self.assertEquals(2, node['instances']['deploy'])

    def test_import_types_combination(self):
        yaml = self.create_yaml_with_imports([self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type2
        """]) + """
node_types:
    test_type2: {}
        """

        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        node1 = nodes[0]
        node2 = nodes[1]
        self.assertEquals('test_node', node1['id'])
        self.assertEquals('test_type', node1['type'])
        self.assertEquals('val', node1['properties']['key'])
        # self.assertEquals(1, node1['instances']['deploy'])
        self.assertEquals('test_node2', node2['id'])
        self.assertEquals('test_type2', node2['type'])
        # self.assertEquals(1, node2['instances']['deploy'])

    def test_relationship_operation_mapping_with_properties_injection(self):
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
                source_interfaces:
                    test_interface1:
                        install:
                            implementation: test_plugin.install
                            inputs:
                                key: value
relationships:
    test_relationship: {}
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        relationship1 = nodes[1]['relationships'][0]
        rel1_source_ops = relationship1['source_operations']
        self.assertEqual(
            op_struct('test_plugin', 'install', {'key': 'value'},
                      executor='central_deployment_agent'),
            rel1_source_ops['install'])
        self.assertEqual(
            op_struct('test_plugin', 'install', {'key': 'value'},
                      executor='central_deployment_agent'),
            rel1_source_ops['test_interface1.install'])

    def test_no_workflows(self):
        result = self.parse(self.MINIMAL_BLUEPRINT)
        self.assertEquals(result['workflows'], {})

    def test_empty_workflows(self):
        yaml = self.MINIMAL_BLUEPRINT + """
workflows: {}
"""
        result = self.parse(yaml)
        self.assertEqual(result['workflows'], {})

    def test_workflow_basic_mapping(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1: test_plugin.workflow1
"""
        result = self.parse(yaml)
        workflows = result['workflows']
        self.assertEqual(1, len(workflows))
        self.assertEqual(workflow_op_struct('test_plugin', 'workflow1',),
                         workflows['workflow1'])
        workflow_plugins_to_install = result['workflow_plugins_to_install']
        self.assertEqual(1, len(workflow_plugins_to_install))
        self.assertEqual('test_plugin', workflow_plugins_to_install[0]['name'])

    def test_workflow_advanced_mapping(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            prop1:
                default: value1
            mandatory_prop: {}
            nested_prop:
                default:
                    nested_key: nested_value
                    nested_list:
                        - val1
                        - val2
"""
        result = self.parse(yaml)
        workflows = result['workflows']
        self.assertEqual(1, len(workflows))
        parameters = {
            'prop1': {'default': 'value1'},
            'mandatory_prop': {},
            'nested_prop': {
                'default': {
                    'nested_key': 'nested_value',
                    'nested_list': [
                        'val1',
                        'val2'
                    ]
                }
            }
        }
        self.assertEqual(workflow_op_struct('test_plugin',
                                            'workflow1',
                                            parameters),
                         workflows['workflow1'])
        workflow_plugins_to_install = result['workflow_plugins_to_install']
        self.assertEqual(1, len(workflow_plugins_to_install))
        self.assertEqual('test_plugin', workflow_plugins_to_install[0]['name'])

    def test_workflow_imports(self):
        workflows1 = """
workflows:
    workflow1: test_plugin.workflow1
"""
        workflows2 = """
plugins:
    test_plugin2:
        executor: central_deployment_agent
        source: dummy
workflows:
    workflow2: test_plugin2.workflow2
"""
        yaml = self.create_yaml_with_imports([
            self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS,
            workflows1,
            workflows2
        ])
        result = self.parse(yaml)
        workflows = result['workflows']
        self.assertEqual(2, len(workflows))
        self.assertEqual(workflow_op_struct('test_plugin', 'workflow1'),
                         workflows['workflow1'])
        self.assertEqual(workflow_op_struct('test_plugin2', 'workflow2'),
                         workflows['workflow2'])
        workflow_plugins_to_install = result['workflow_plugins_to_install']
        self.assertEqual(2, len(workflow_plugins_to_install))
        self.assertEqual('test_plugin', workflow_plugins_to_install[0]['name'])
        self.assertEqual('test_plugin2',
                         workflow_plugins_to_install[1]['name'])

    def test_relationship_type_properties_empty_properties(self):
        yaml = """
node_templates:
    test_node:
        type: test_type
node_types:
    test_type: {}
relationships:
    test_relationship:
        properties: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        relationship = result['relationships']['test_relationship']
        self.assertEquals({}, relationship['properties'])

    def test_relationship_type_properties_empty_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        relationship = result['relationships']['test_relationship']
        self.assertEquals({'key': {}}, relationship['properties'])

    def test_relationship_type_properties_property_with_description_only(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                description: property_desc
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        relationship = result['relationships']['test_relationship']
        self.assertEquals({'key': {'description': 'property_desc'}},
                          relationship['properties'])

    def test_relationship_type_properties_standard_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                default: val
                description: property_desc
                type: string
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        relationship = result['relationships']['test_relationship']
        self.assertEquals(
            {'key': {'default': 'val', 'description': 'property_desc',
                     'type': 'string'}},
            relationship['properties'])

    def test_workflow_parameters_empty_parameters(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    test_workflow:
        mapping: test_plugin.workflow1
        parameters: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        workflow = result['workflows']['test_workflow']
        self.assertEquals({}, workflow['parameters'])

    def test_workflow_parameters_empty_parameter(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    test_workflow:
        mapping: test_plugin.workflow1
        parameters:
            key: {}
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        workflow = result['workflows']['test_workflow']
        self.assertEquals({'key': {}}, workflow['parameters'])

    def test_workflow_parameters_parameter_with_description_only(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    test_workflow:
        mapping: test_plugin.workflow1
        parameters:
            key:
                description: parameter_desc
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        workflow = result['workflows']['test_workflow']
        self.assertEquals({'key': {'description': 'parameter_desc'}},
                          workflow['parameters'])

    def test_workflow_parameters_standard_parameter(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    test_workflow:
        mapping: test_plugin.workflow1
        parameters:
            key:
                default: val
                description: parameter_desc
                type: string
"""
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])
        self.assertEquals('test_type', node['type'])
        workflow = result['workflows']['test_workflow']
        self.assertEquals(
            {'key': {'default': 'val', 'description': 'parameter_desc',
                     'type': 'string'}},
            workflow['parameters'])

    def test_policy_type_properties_empty_properties(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict())))
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + '\n' + \
            yml.safe_dump(policy_types)
        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         policy_types['policy_types'])

    def test_policy_type_properties_empty_property(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict()))))
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + '\n' + \
            yml.safe_dump(policy_types)
        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         policy_types['policy_types'])

    def test_policy_type_properties_property_with_description_only(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict(
                            description='property description')))))
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + '\n' + \
            yml.safe_dump(policy_types)
        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         policy_types['policy_types'])

    def test_policy_type_properties_property_with_default_only(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict(
                            default='default_value')))))
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + '\n' + \
            yml.safe_dump(policy_types)
        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         policy_types['policy_types'])

    def test_policy_type_properties_standard_property(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict(
                            default='default_value',
                            description='property description',
                            type='string')))))
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + '\n' + \
            yml.safe_dump(policy_types)
        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         policy_types['policy_types'])

    def test_policy_type_imports(self):
        policy_types = []
        for i in range(2):
            policy_types.append(dict(
                policy_types={
                    'policy_type{0}'.format(i): dict(
                        source='the_source',
                        properties=dict(
                            property=dict(
                                default='default_value',
                                description='property description')))}))

        yaml = self.create_yaml_with_imports([
            self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS,
            yml.safe_dump(policy_types[0]),
            yml.safe_dump(policy_types[1]),
        ])

        expected_result = dict(
            policy_types=policy_types[0]['policy_types'])
        expected_result['policy_types'].update(policy_types[1]['policy_types'])

        result = self.parse(yaml)
        self.assertEqual(result['policy_types'],
                         expected_result['policy_types'])

    def test_policy_trigger_imports(self):
        policy_triggers = []
        for i in range(2):
            policy_triggers.append(dict(
                policy_triggers={
                    'policy_trigger{0}'.format(i): dict(
                        source='the_source',
                        parameters=dict(
                            property=dict(
                                default='default_value',
                                description='property description',
                                type='string')))}))

        yaml = self.create_yaml_with_imports([
            self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS,
            yml.safe_dump(policy_triggers[0]),
            yml.safe_dump(policy_triggers[1]),
        ])

        expected_result = dict(
            policy_triggers=policy_triggers[0]['policy_triggers'])
        expected_result['policy_triggers'].update(policy_triggers[1][
            'policy_triggers'])

        result = self.parse(yaml)
        self.assertEqual(result['policy_triggers'],
                         expected_result['policy_triggers'])

    def test_groups_schema_properties_merge(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
policy_types:
    policy_type:
        properties:
            key1:
                default: value1
            key2:
                description: key2 description
            key3:
                default: value3
        source: source
groups:
    group:
        members: [test_node]
        policies:
            policy:
                type: policy_type
                properties:
                    key2: group_value2
                    key3: group_value3
"""
        result = self.parse(yaml)
        groups = result['groups']
        self.assertEqual(1, len(groups))
        group = groups['group']
        self.assertEqual(['test_node'], group['members'])
        self.assertEqual(1, len(group['policies']))
        policy = group['policies']['policy']
        self.assertEqual('policy_type', policy['type'])
        self.assertEqual({
            'key1': 'value1',
            'key2': 'group_value2',
            'key3': 'group_value3'
        }, policy['properties'])

    def test_groups_imports(self):
        groups = []
        for i in range(2):
            groups.append(dict(
                groups={
                    'group{0}'.format(i): dict(
                        members=['test_node'],
                        policies=dict(
                            policy=dict(
                                type='policy_type',
                                properties={},
                                triggers={})))}))
        policy_types = """
policy_types:
    policy_type:
        properties: {}
        source: source
"""
        yaml = self.create_yaml_with_imports([
            self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS,
            policy_types,
            yml.safe_dump(groups[0]),
            yml.safe_dump(groups[1])])

        expected_result = dict(
            groups=groups[0]['groups'])
        expected_result['groups'].update(groups[1]['groups'])

        result = self.parse(yaml)
        self.assertEqual(result['groups'],
                         expected_result['groups'])

    def test_operation_mapping_with_properties_injection(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs:
                        key:
                            default: value
"""
        result = self.parse(yaml)
        node = result['nodes'][0]
        self.assertEquals('test_type', node['type'])
        operations = node['operations']
        self.assertEquals(
            op_struct('test_plugin', 'install', {'key': 'value'},
                      executor='central_deployment_agent'),
            operations['install'])
        self.assertEquals(
            op_struct('test_plugin', 'install', {'key': 'value'},
                      executor='central_deployment_agent'),
            operations['test_interface1.install'])

    def test_merge_plugins_and_interfaces_imports(self):
        yaml = self.create_yaml_with_imports(
            [self.BASIC_NODE_TEMPLATES_SECTION, self.BASIC_PLUGIN]) + """
plugins:
    other_test_plugin:
        executor: central_deployment_agent
        source: dummy
node_types:
    test_type:
        properties:
            key: {}
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
            test_interface2:
                start:
                    implementation: other_test_plugin.start
                    inputs: {}
                shutdown:
                    implementation: other_test_plugin.shutdown
                    inputs: {}
"""
        result = self.parse(yaml)
        node = result['nodes'][0]
        self._assert_blueprint(result)

        operations = node['operations']
        self.assertEquals(op_struct('other_test_plugin', 'start',
                                    executor='central_deployment_agent'),
                          operations['start'])
        self.assertEquals(op_struct('other_test_plugin', 'start',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.start'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['shutdown'])
        self.assertEquals(op_struct('other_test_plugin', 'shutdown',
                                    executor='central_deployment_agent'),
                          operations['test_interface2.shutdown'])

    def test_node_interfaces_operation_mapping(self):
        yaml = self.BASIC_PLUGIN + self.BASIC_NODE_TEMPLATES_SECTION + """
        interfaces:
            test_interface1:
                install: test_plugin.install
                terminate: test_plugin.terminate
node_types:
    test_type:
        properties:
            key: {}
            """
        result = self.parse(yaml)
        self._assert_blueprint(result)

    def test_property_schema_type_property_with_intrinsic_functions(self):
        yaml = """
node_templates:
    test_node:
        type: test_type
        properties:
            int1: { get_input: x }
node_types:
    test_type:
        properties:
            int1:
                type: integer
inputs:
    x: {}
        """
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])

    def test_property_schema_type_property(self):
        yaml = """
node_templates:
    test_node:
        type: test_type
        properties:
            string1: val
            string2: true
            string3: 5
            string4: 5.7
            boolean1: true
            boolean2: false
            boolean3: False
            boolean4: FALSE
            boolean5: Yes
            boolean6: On
            boolean7: No
            boolean8: Off
            integer1: 5
            integer2: -5
            integer3: 1000000000000
            integer4: 0
            float1: 5.7
            float2: 5.735935
            float3: 5.0
            float4: 5
            float5: -5.7

node_types:
    test_type:
        properties:
            string1:
                type: string
            string2:
                type: string
            string3:
                type: string
            string4:
                type: string
            boolean1:
                type: boolean
            boolean2:
                type: boolean
            boolean3:
                type: boolean
            boolean4:
                type: boolean
            boolean5:
                type: boolean
            boolean6:
                type: boolean
            boolean7:
                type: boolean
            boolean8:
                type: boolean
            integer1:
                type: integer
            integer2:
                type: integer
            integer3:
                type: integer
            integer4:
                type: integer
            float1:
                type: float
            float2:
                type: float
            float3:
                type: float
            float4:
                type: float
            float5:
                type: float
                """
        result = self.parse(yaml)
        self.assertEquals(1, len(result['nodes']))
        node = result['nodes'][0]
        self.assertEquals('test_node', node['id'])

    def test_version_field(self):
        yaml = self.MINIMAL_BLUEPRINT + self.BASIC_VERSION_SECTION_DSL_1_0
        result = dsl_parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_version_field_with_versionless_imports(self):
        imported_yaml = str()
        imported_yaml_filename = self.make_yaml_file(imported_yaml)
        yaml = """
imports:
    -   {0}""".format(imported_yaml_filename) + \
               self.BASIC_VERSION_SECTION_DSL_1_0 + \
               self.MINIMAL_BLUEPRINT
        result = dsl_parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_version_field_with_imports_with_version(self):
        imported_yaml = self.BASIC_VERSION_SECTION_DSL_1_0
        imported_yaml_filename = self.make_yaml_file(imported_yaml)
        yaml = """
imports:
    -   {0}""".format(imported_yaml_filename) + \
               self.BASIC_VERSION_SECTION_DSL_1_0 + \
               self.MINIMAL_BLUEPRINT
        result = dsl_parse(yaml)
        self._assert_minimal_blueprint(result)

    def test_script_mapping(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_0 + """
plugins:
    script:
        executor: central_deployment_agent
        install: false

node_types:
    type:
        interfaces:
            test:
                op:
                    implementation: stub.py
                    inputs: {}
                op2:
                    implementation: stub.py
                    inputs:
                        key:
                            default: value
relationships:
    relationship:
        source_interfaces:
            test:
                op:
                    implementation: stub.py
                    inputs: {}
        target_interfaces:
            test:
                op:
                    implementation: stub.py
                    inputs: {}
workflows:
    workflow: stub.py
    workflow2:
        mapping: stub.py
        parameters:
            key:
                default: value

node_templates:
    node1:
        type: type
        relationships:
            -   target: node2
                type: relationship
    node2:
        type: type

"""
        self.make_file_with_name(content='content',
                                 filename='stub.py')
        yaml_path = self.make_file_with_name(content=yaml,
                                             filename='blueprint.yaml')
        result = self.parse_from_path(yaml_path)
        node = [n for n in result['nodes'] if n['name'] == 'node1'][0]
        relationship = node['relationships'][0]

        operation = node['operations']['test.op']
        operation2 = node['operations']['test.op2']
        source_operation = relationship['source_operations']['test.op']
        target_operation = relationship['target_operations']['test.op']
        workflow = result['workflows']['workflow']
        workflow2 = result['workflows']['workflow2']

        def assert_operation(op, extra_properties=False):
            inputs = {'script_path': 'stub.py'}
            if extra_properties:
                inputs.update({'key': 'value'})
            self.assertEqual(op, op_struct(
                plugin_name=constants.SCRIPT_PLUGIN_NAME,
                mapping=constants.SCRIPT_PLUGIN_RUN_TASK,
                inputs=inputs,
                executor='central_deployment_agent'))

        assert_operation(operation)
        assert_operation(operation2, extra_properties=True)
        assert_operation(source_operation)
        assert_operation(target_operation)

        self.assertEqual(workflow['operation'],
                         constants.SCRIPT_PLUGIN_EXECUTE_WORKFLOW_TASK)
        self.assertEqual(1, len(workflow['parameters']))
        self.assertEqual(workflow['parameters']['script_path']['default'],
                         'stub.py')
        self.assertEqual(workflow['plugin'], constants.SCRIPT_PLUGIN_NAME)

        self.assertEqual(workflow2['operation'],
                         constants.SCRIPT_PLUGIN_EXECUTE_WORKFLOW_TASK)
        self.assertEqual(2, len(workflow2['parameters']))
        self.assertEqual(workflow2['parameters']['script_path']['default'],
                         'stub.py')
        self.assertEqual(workflow2['parameters']['key']['default'], 'value')
        self.assertEqual(workflow['plugin'], constants.SCRIPT_PLUGIN_NAME)

    def test_version(self):
        def assertion(version_str, expected):
            version = self.parse(self.MINIMAL_BLUEPRINT,
                                 dsl_version=version_str)['version']
            version = models.Version(version)
            self.assertEqual(version.raw,
                             version_str.split(' ')[1].strip())
            self.assertEqual(version.definitions_name, 'cloudify_dsl')
            self.assertEqual(version.definitions_version, expected)
        assertion(self.BASIC_VERSION_SECTION_DSL_1_0,
                  expected=(1, 0))
        assertion(self.BASIC_VERSION_SECTION_DSL_1_1,
                  expected=(1, 1))
        assertion(self.BASIC_VERSION_SECTION_DSL_1_2,
                  expected=(1, 2))

    def test_version_comparison(self):

        def parse_version(ver):
            parsed = version.parse_dsl_version('cloudify_dsl_{0}'.format(ver))
            major, minor, micro = parsed
            if micro is None:
                micro = 0
            return major, minor, micro

        versions = [
            (1, '1_0'),
            (1, '1_0_0'),
            (2, '1_0_1'),
            (3, '1_1'),
            (3, '1_1_0'),
            (4, '1_2'),
            (4, '1_2_0'),
            (5, '2_0'),
        ]

        for ord1, ver1 in versions:
            parsed_ver1 = parse_version(ver1)
            for ord2, ver2 in versions:
                parsed_ver2 = parse_version(ver2)
                if ord1 == ord2:
                    comp_func = self.assertEqual
                elif ord1 < ord2:
                    comp_func = self.assertLess
                else:
                    comp_func = self.assertGreater
                comp_func(parsed_ver1, parsed_ver2)

    def test_dsl_definitions(self):
        yaml = """
dsl_definitions:
  def1: &def1
    prop1: val1
    prop2: val2
  def2: &def2
    prop3: val3
    prop4: val4
node_types:
  type1:
    properties:
      prop1:
        default: default_val1
      prop2:
        default: default_val2
      prop3:
        default: default_val3
      prop4:
        default: default_val4
node_templates:
  node1:
    type: type1
    properties:
      <<: *def1
      <<: *def2
  node2:
    type: type1
    properties: *def1
  node3:
    type: type1
    properties: *def2
"""
        plan = self.parse_1_2(yaml)
        self.assertNotIn('dsl_definitions', plan)
        node1 = self.get_node_by_name(plan, 'node1')
        node2 = self.get_node_by_name(plan, 'node2')
        node3 = self.get_node_by_name(plan, 'node3')
        self.assertEqual({
            'prop1': 'val1',
            'prop2': 'val2',
            'prop3': 'val3',
            'prop4': 'val4',
        }, node1['properties'])
        self.assertEqual({
            'prop1': 'val1',
            'prop2': 'val2',
            'prop3': 'default_val3',
            'prop4': 'default_val4',
        }, node2['properties'])
        self.assertEqual({
            'prop1': 'default_val1',
            'prop2': 'default_val2',
            'prop3': 'val3',
            'prop4': 'val4',
        }, node3['properties'])

    def test_dsl_definitions_as_list(self):
        yaml = """
dsl_definitions:
  - &def1
    prop1: val1
    prop2: val2
  - &def2
    prop3: val3
    prop4: val4
node_types:
  type1:
    properties:
      prop1:
        default: default_val1
      prop2:
        default: default_val2
      prop3:
        default: default_val3
      prop4:
        default: default_val4
node_templates:
  node1:
    type: type1
    properties:
      <<: *def1
      <<: *def2
"""
        plan = self.parse_1_2(yaml)
        self.assertNotIn('dsl_definitions', plan)
        node1 = self.get_node_by_name(plan, 'node1')
        self.assertEqual({
            'prop1': 'val1',
            'prop2': 'val2',
            'prop3': 'val3',
            'prop4': 'val4',
        }, node1['properties'])

    def test_dsl_definitions_in_imports(self):
        imported_yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
dsl_definitions:
  - &def1
    prop1:
        default: val1
node_types:
  type1:
    properties: *def1

"""
        imported_yaml_filename = self.make_yaml_file(imported_yaml)
        yaml = """
dsl_definitions:
  - &def1
    prop1: val2
imports:
    - {0}
node_templates:
  node1:
    type: type1
  node2:
    type: type1
    properties: *def1
""".format(imported_yaml_filename)

        plan = self.parse_1_2(yaml)
        self.assertNotIn('dsl_definitions', plan)
        node1 = self.get_node_by_name(plan, 'node1')
        node2 = self.get_node_by_name(plan, 'node2')
        self.assertEqual({
            'prop1': 'val1',
        }, node1['properties'])
        self.assertEqual({
            'prop1': 'val2',
        }, node2['properties'])

    def test_null_default(self):
        yaml = """
plugins:
  p:
    install: false
    executor: central_deployment_agent
node_types:
  type: {}
node_templates:
  node:
    type: type
workflows:
  workflow:
    mapping: p.workflow
    parameters:
      parameter:
        default: null
"""
        workflow = self.parse(yaml)['workflows']['workflow']
        parameter = workflow['parameters']['parameter']
        self.assertIn('default', parameter)

    def test_required_property(self):
        yaml = """
node_types:
  type:
    properties:
      none_required_prop:
        required: false
      required_prop:
        required: true
node_templates:
  node:
    type: type
    properties:
      required_prop: value
"""
        properties = self.parse_1_2(yaml)['nodes'][0]['properties']
        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['required_prop'], 'value')

    def test_null_property_value(self):
        yaml = """
node_types:
  type:
    properties:
      prop1:
        default: null
      prop2:
        default: some_value
      prop3: {}
      prop4:
        required: false
node_templates:
  node:
    type: type
    properties:
      prop1: null
      prop2: null
      prop3: null
      prop4: null
"""
        properties = self.parse_1_2(yaml)['nodes'][0]['properties']
        self.assertEqual(len(properties), 4)
        for value in properties.values():
            self.assertIsNone(value)

    def test_validate_version_false(self):
        yaml = """
description: description
dsl_definitions:
  definition: value
plugins:
  plugin:
    executor: central_deployment_agent
    install: false
    install_arguments: --arg
node_types:
  type:
    interfaces:
      interface:
        op:
          implementation: plugin.task.op
          max_retries: 1
          retry_interval: 1
data_types:
  type:
    properties:
      prop:
        required: false
node_templates:
  node:
    type: type
"""
        self.assertRaises(exceptions.DSLParsingException,
                          self.parse, yaml,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_0,
                          validate_version=True)
        self.parse(yaml,
                   dsl_version=self.BASIC_VERSION_SECTION_DSL_1_0,
                   validate_version=False)

    def test_validate_version_false_different_versions_in_imports(self):
        imported1 = self.BASIC_VERSION_SECTION_DSL_1_0
        imported2 = self.BASIC_VERSION_SECTION_DSL_1_1
        imported3 = self.BASIC_VERSION_SECTION_DSL_1_2
        imported4 = self.BASIC_VERSION_SECTION_DSL_1_3
        yaml = self.create_yaml_with_imports([imported1,
                                              imported2,
                                              imported3,
                                              imported4])
        yaml += """
node_types:
  type: {}
node_templates:
  node:
    type: type
"""
        self.assertRaises(exceptions.DSLParsingException,
                          self.parse, yaml,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_0,
                          validate_version=True)
        self.parse(yaml,
                   dsl_version=self.BASIC_VERSION_SECTION_DSL_1_0,
                   validate_version=False)

    def test_plugin_fields(self):
        yaml = """
tosca_definitions_version: cloudify_dsl_1_2
node_types:
  type:
    properties:
      prop1:
        default: value
  cloudify.nodes.Compute:
    properties:
      prop1:
        default: value
node_templates:
  node1:
    type: type
    interfaces:
     interface:
       op: plugin1.op
  node2:
    type: cloudify.nodes.Compute
    interfaces:
     interface:
       op: plugin2.op
"""
        base_plugin_def = {'distribution': 'dist',
                           'distribution_release': 'release',
                           'distribution_version': 'version',
                           'install': True,
                           'install_arguments': '123',
                           'package_name': 'name',
                           'package_version': 'version',
                           'source': 'source',
                           'supported_platform': 'any'}
        deployment_plugin_def = base_plugin_def.copy()
        deployment_plugin_def['executor'] = 'central_deployment_agent'
        host_plugin_def = base_plugin_def.copy()
        host_plugin_def['executor'] = 'host_agent'
        raw_parsed = yml.safe_load(yaml)
        raw_parsed['plugins'] = {
            'plugin1': deployment_plugin_def,
            'plugin2': host_plugin_def
        }
        parsed = self.parse_1_2(yml.safe_dump(raw_parsed))
        expected_plugin1 = deployment_plugin_def.copy()
        expected_plugin1['name'] = 'plugin1'
        expected_plugin2 = host_plugin_def.copy()
        expected_plugin2['name'] = 'plugin2'
        plugin1 = parsed['deployment_plugins_to_install'][0]
        node2 = self.get_node_by_name(parsed, 'node2')
        plugin2 = node2['plugins_to_install'][0]
        self.assertEqual(expected_plugin1, plugin1)
        self.assertEqual(expected_plugin2, plugin2)
