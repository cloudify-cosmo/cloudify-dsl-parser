#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from yaml import safe_dump, safe_load

from aria.parser import models
from aria.parser.exceptions import DSLParsingLogicException
from aria.parser.framework.elements.relationships import RelationshipMapping
from aria.parser.dsl_supported_versions import (
    parse_dsl_version, database,
    VersionNumber, VersionStructure,
)
from aria.parser.constants import (
    PLUGIN_NAME_KEY,
    PLUGIN_SOURCE_KEY,
    PLUGIN_INSTALL_KEY,
    PLUGIN_EXECUTOR_KEY,
    PLUGIN_INSTALL_ARGUMENTS_KEY,
    PLUGIN_PACKAGE_NAME,
    PLUGIN_PACKAGE_VERSION,
    PLUGIN_SUPPORTED_PLATFORM,
    PLUGIN_DISTRIBUTION,
    PLUGIN_DISTRIBUTION_VERSION,
    PLUGIN_DISTRIBUTION_RELEASE,
    CENTRAL_DEPLOYMENT_AGENT,
)

from .suite import (
    ParserTestCase,
    TempDirectoryTestCase,
    get_node_by_name,
    op_struct,
)


def _workflow_op_struct(plugin_name, mapping, parameters=None):
    return {
        'plugin': plugin_name,
        'operation': mapping,
        'parameters': parameters or {},
    }


class TestParserApi(ParserTestCase, TempDirectoryTestCase):
    def test_type_with_interfaces_and_basic_plugin(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += """
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
        properties:
            install_agent:
                default: 'false'
            key: {}
"""
        result = self.parse()
        self._assert_blueprint(result)
        first_node = result['nodes'][0]
        parsed_plugins = first_node['plugins']
        expected_plugins = [{
            PLUGIN_NAME_KEY: 'test_plugin',
            PLUGIN_SOURCE_KEY: 'dummy',
            PLUGIN_INSTALL_KEY: True,
            PLUGIN_EXECUTOR_KEY: CENTRAL_DEPLOYMENT_AGENT,
            PLUGIN_INSTALL_ARGUMENTS_KEY: None,
            PLUGIN_PACKAGE_NAME: None,
            PLUGIN_PACKAGE_VERSION: None,
            PLUGIN_SUPPORTED_PLATFORM: None,
            PLUGIN_DISTRIBUTION: None,
            PLUGIN_DISTRIBUTION_VERSION: None,
            PLUGIN_DISTRIBUTION_RELEASE: None,
        }]
        self.assertEquals(parsed_plugins, expected_plugins)

    def test_type_with_interface_and_plugin_with_install_args(self):
        self.template.version_section('1.1')
        self.template.node_template_section()
        self.template += self.template.PLUGIN_WITH_INSTALL_ARGS
        self.template += self.template.BASIC_TYPE
        result = self.parse()
        self._assert_blueprint(result)
        first_node = result['nodes'][0]
        parsed_plugins = first_node['plugins']
        expected_plugins = [{
            PLUGIN_NAME_KEY: 'test_plugin',
            PLUGIN_SOURCE_KEY: 'dummy',
            PLUGIN_INSTALL_KEY: True,
            PLUGIN_EXECUTOR_KEY: CENTRAL_DEPLOYMENT_AGENT,
            PLUGIN_INSTALL_ARGUMENTS_KEY: '-r requirements.txt',
            PLUGIN_PACKAGE_NAME: None,
            PLUGIN_PACKAGE_VERSION: None,
            PLUGIN_SUPPORTED_PLATFORM: None,
            PLUGIN_DISTRIBUTION: None,
            PLUGIN_DISTRIBUTION_VERSION: None,
            PLUGIN_DISTRIBUTION_RELEASE: None,
        }]
        self.assertEquals(parsed_plugins, expected_plugins)

    def test_version_1_2_and_above_input_imports(self):
        importable = """
inputs:
    test_input2:
        default: value
"""
        self._verify_1_2_and_below_non_mergeable_imports(importable, 'inputs')
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
        self._verify_1_2_and_below_non_mergeable_imports(importable, 'outputs')
        self._verify_1_3_and_above_mergeable_imports(importable)

    def test_agent_plugin_in_node_contained_in_host_contained_in_container(self):  # noqa
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        self.assertEqual(
            'compute', get_node_by_name(result, 'compute')['host_id'])

    def test_node_host_id_field(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        self.assertEquals('test_node', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])
        self.assertEquals('test_node1', result['nodes'][2]['host_id'])

    def test_node_host_id_field_via_node_supertype(self):
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: another_type
node_types:
    cloudify.nodes.Compute: {}
    another_type:
        derived_from: cloudify.nodes.Compute
            """
        result = self.parse()
        self.assertEquals('test_node1', result['nodes'][0]['host_id'])

    def test_node_host_id_field_via_relationship_derived_from_inheritance(
            self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        self.assertEquals('test_node1', result['nodes'][1]['host_id'])

    def test_node_type_operation_override(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        start_operation = result['nodes'][0]['operations']['start']
        self.assertEqual('overriding_start', start_operation['operation'])

    def test_node_type_node_template_operation_override(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        start_operation = result['nodes'][0]['operations']['start']
        self.assertEqual('overriding_start', start_operation['operation'])

    def test_executor_override_node_types(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0]['plugins_to_install']))

    def test_executor_override_plugin_declaration(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        plugin = result['nodes'][0]['deployment_plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0][
            'deployment_plugins_to_install']))

    def test_executor_override_type_declaration(self):
        self.template.version_section('1.0')
        self.template += """
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
        result = self.parse()
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0][
            'plugins_to_install']))

    def test_policy_type_properties_empty_properties(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties={})))
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += '\n' + safe_dump(policy_types)
        result = self.parse()
        self.assertEqual(result['policy_types'], policy_types['policy_types'])

    def test_policy_type_properties_empty_property(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict()))))
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += '\n' + safe_dump(policy_types)
        result = self.parse()
        self.assertEqual(result['policy_types'], policy_types['policy_types'])

    def test_policy_type_properties_property_with_description_only(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict(
                            description='property description')))))
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += '\n' + safe_dump(policy_types)
        result = self.parse()
        self.assertEqual(result['policy_types'], policy_types['policy_types'])

    def test_policy_type_properties_property_with_default_only(self):
        policy_types = dict(
            policy_types=dict(
                policy_type=dict(
                    source='the_source',
                    properties=dict(
                        property=dict(default='default_value')
                    ))))
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += '\n' + safe_dump(policy_types)
        result = self.parse()
        self.assertEqual(result['policy_types'], policy_types['policy_types'])

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
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += '\n' + safe_dump(policy_types)
        result = self.parse()
        self.assertEqual(result['policy_types'], policy_types['policy_types'])

    def test_policy_type_imports(self):
        policy_types = [
            dict(policy_types={'policy_type{0}'.format(i): dict(
                source='the_source',
                properties=dict(
                    property=dict(
                        default='default_value',
                        description='property description')))})
            for i in range(2)
        ]
        for i in range(2):
            policy_types.append(dict(
                policy_types={
                    'policy_type{0}'.format(i): dict(
                        source='the_source',
                        properties=dict(
                            property=dict(
                                default='default_value',
                                description='property description')))}))

        template = self.template.version_section('1.0', raw=True)
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template.template = template + self.create_yaml_with_imports([
            str(self.template),
            safe_dump(policy_types[0]),
            safe_dump(policy_types[1]),
        ])

        expected_result = dict(policy_types=policy_types[0]['policy_types'])
        expected_result['policy_types'].update(policy_types[1]['policy_types'])

        result = self.parse()
        self.assertEqual(
            result['policy_types'], expected_result['policy_types'])

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
        template = self.template.version_section('1.0', raw=True)
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template.template = template + self.create_yaml_with_imports([
            str(self.template),
            safe_dump(policy_triggers[0]),
            safe_dump(policy_triggers[1]),
        ])

        expected_result = dict(
            policy_triggers=policy_triggers[0]['policy_triggers'])
        expected_result['policy_triggers'].update(policy_triggers[1][
            'policy_triggers'])

        result = self.parse()
        self.assertEqual(
            result['policy_triggers'], expected_result['policy_triggers'])

    def test_groups_schema_properties_merge(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template += """
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
        result = self.parse()
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
        groups = [
            dict(groups={
                'group{0}'.format(i): dict(
                    members=['test_node'],
                    policies=dict(
                        policy=dict(
                            type='policy_type',
                            properties={},
                            triggers={})))})
            for i in range(2)
        ]
        policy_types = """
policy_types:
    policy_type:
        properties: {}
        source: source
"""
        template = self.template.version_section('1.0', raw=True)
        self.template.node_type_section()
        self.template.plugin_section()
        self.template.node_template_section()
        self.template.template = template + self.create_yaml_with_imports([
            str(self.template),
            policy_types,
            safe_dump(groups[0]),
            safe_dump(groups[1])])

        expected_result = dict(groups=groups[0]['groups'])
        expected_result['groups'].update(groups[1]['groups'])

        result = self.parse()
        self.assertEqual(result['groups'], expected_result['groups'])

    def test_operation_mapping_with_properties_injection(self):
        self.template.version_section('1.0')
        self.template.node_template_section()
        self.template.plugin_section()
        self.template += """
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
        result = self.parse()
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

    def test_version(self):
        def assertion(expected):
            self.template.node_type_section()
            self.template.node_template_section()
            version = self.parse()['version']
            version = models.Version(version)
            self.assertEqual(version.definitions_name, 'cloudify_dsl')
            self.assertEqual(version.definitions_version.number, expected)

        self.template.version_section('1.0')
        assertion(expected=VersionNumber(1, 0))
        self.template.clear()
        self.template.version_section('1.1')
        assertion(expected=VersionNumber(1, 1))
        self.template.clear()
        self.template.version_section('1.2')
        assertion(expected=VersionNumber(1, 2))
        self.template.clear()

    def test_version_comparison(self):

        def parse_version(version):
            version_structure = VersionStructure(
                'cloudify_dsl',
                VersionNumber(*(int(n) for n in version.split('_'))))
            default_db = database.copy()
            database['cloudify_dsl'].add(version_structure)
            try:
                parsed = parse_dsl_version('cloudify_dsl_{0}'.format(version))
            finally:
                database.clear()
                database.update(default_db)
            major, minor, micro = parsed.number
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
        self.template.version_section('1.2')
        self.template += """
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
        plan = self.parse()
        self.assertNotIn('dsl_definitions', plan)
        node1 = get_node_by_name(plan, 'node1')
        node2 = get_node_by_name(plan, 'node2')
        node3 = get_node_by_name(plan, 'node3')
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

    def test_plugin_fields(self):
        self.template.version_section('1.2')
        self.template += """
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
        base_plugin_def = {
            'distribution': 'dist',
            'distribution_release': 'release',
            'distribution_version': 'version',
            'install': True,
            'install_arguments': '123',
            'package_name': 'name',
            'package_version': 'version',
            'source': 'source',
            'supported_platform': 'any',
        }
        deployment_plugin_def = base_plugin_def.copy()
        deployment_plugin_def['executor'] = 'central_deployment_agent'
        host_plugin_def = base_plugin_def.copy()
        host_plugin_def['executor'] = 'host_agent'
        raw_parsed = safe_load(str(self.template))
        raw_parsed['plugins'] = {
            'plugin1': deployment_plugin_def,
            'plugin2': host_plugin_def,
        }

        self.template.clear()
        self.template.version_section('1.2')
        self.template += safe_dump(raw_parsed)
        parsed = self.parse()
        expected_plugin1 = deployment_plugin_def.copy()
        expected_plugin1['name'] = 'plugin1'
        expected_plugin2 = host_plugin_def.copy()
        expected_plugin2['name'] = 'plugin2'
        plugin1 = parsed['deployment_plugins_to_install'][0]
        node2 = get_node_by_name(parsed, 'node2')
        plugin2 = node2['plugins_to_install'][0]
        self.assertEqual(expected_plugin1, plugin1)
        self.assertEqual(expected_plugin2, plugin2)

    def _assert_blueprint(self, result):
        node = result['nodes'][0]
        plugin_props = [
            p for p in node['plugins']
            if p['name'] == 'test_plugin'][0]

        self.assertEquals('test_type', node['type'])
        self.assertEquals(11, len(plugin_props))
        self.assertEquals('test_plugin', plugin_props[PLUGIN_NAME_KEY])
        operations = node['operations']
        self.assertEquals(
            op_struct('test_plugin', 'install',
                      executor='central_deployment_agent'),
            operations['install'])
        self.assertEquals(
            op_struct('test_plugin', 'install',
                      executor='central_deployment_agent'),
            operations['test_interface1.install'])
        self.assertEquals(
            op_struct('test_plugin', 'terminate',
                      executor='central_deployment_agent'),
            operations['terminate'])
        self.assertEquals(
            op_struct('test_plugin', 'terminate',
                      executor='central_deployment_agent'),
            operations['test_interface1.terminate'])

    def _create_importable_yaml_for_version_1_3_and_above(self, importable):
        old_template = str(self.template)
        self.template.template = self.template.BASIC_TYPE
        self.template.plugin_section()
        self.template += importable
        imported_yaml = self.make_yaml_file(str(self.template))
        self.template.template = old_template
        self.template += """
imports:
    -   {0}""".format(imported_yaml)
        self.template.node_template_section()
        self.template.input_section()
        self.template.output_section()

    def _verify_1_2_and_below_non_mergeable_imports(
            self, importable, import_type):
        self.template.clear()
        self.template.version_section('1.2')
        self._create_importable_yaml_for_version_1_3_and_above(importable)
        ex = self.assertRaises(DSLParsingLogicException, self.parse)
        self.assertIn(
            "Import failed: non-mergeable field: '{0}'".format(import_type),
            str(ex))

    def _verify_1_3_and_above_mergeable_imports(self, importable):
        self.template.clear()
        self.template.version_section('1.3')
        self._create_importable_yaml_for_version_1_3_and_above(importable)
        result = self.parse()
        self._assert_blueprint(result)

    def test_relationship_types_extensions(self):
        relationship_mapping = RelationshipMapping()
        self.assertEqual(
            expected=relationship_mapping.depens_on_relationship_type,
            observed='cloudify.relationships.depends_on')
        self.assertEqual(
            expected=relationship_mapping.contained_in_relationship_type,
            observed='cloudify.relationships.contained_in')
        self.assertEqual(
            expected=relationship_mapping.contained_to_relationship_type,
            observed='cloudify.relationships.connected_to')
        self.assertEqual(
            expected=relationship_mapping.group_contained_in_relationship_type,
            observed='__group_contained_in__')
        self.assertEqual(
            expected=relationship_mapping.connection_type,
            observed='connection_type')

        self.assertEqual(
            expected=set(relationship_mapping.type_values()),
            observed=set([
                'cloudify.relationships.depends_on',
                'cloudify.relationships.contained_in',
                'cloudify.relationships.connected_to',
                '__group_contained_in__',
                'connection_type',
            ]))
