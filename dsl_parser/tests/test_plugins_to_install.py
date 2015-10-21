########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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


from dsl_parser import constants
from dsl_parser.tests.test_parser_api import op_struct
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class NodePluginsToInstallTest(AbstractTestParser):

    @staticmethod
    def _get_plugin_to_install_from_node(node, plugin_name):
        return next(plugin for plugin in node['plugins_to_install']
                    if plugin['name'] == plugin_name)

    def test_no_duplicate_node_plugins_to_install_field_from_relationship(self):  # NOQA
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
        relationships:
            - type: cloudify.relationships.my_relationship
              target: test_node2
    test_node2:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute: {}

plugins:
    test_plugin:
        executor: host_agent
        source: dummy

relationships:
    cloudify.relationships.my_relationship:
        source_interfaces:
            cloudify.interfaces.relationship_lifecycle:
                postconfigure:
                    implementation: test_plugin.task.postconfigure
                    inputs: {}
"""
        result = self.parse(yaml)
        node = [n for n in result['nodes'] if n['name'] == 'test_node1'][0]
        plugin = node['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(node['plugins_to_install']))

    def test_node_plugins_to_install_field_from_relationship(self):  # NOQA
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
        relationships:
            - type: cloudify.relationships.my_relationship
              target: test_node2
    test_node2:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute: {}

plugins:
    test_plugin:
        executor: host_agent
        source: dummy

relationships:
    cloudify.relationships.my_relationship:
        source_interfaces:
            cloudify.interfaces.relationship_lifecycle:
                postconfigure:
                    implementation: test_plugin.task.postconfigure
                    inputs: {}
"""
        result = self.parse(yaml)
        node = [n for n in result['nodes'] if n['name'] == 'test_node1'][0]
        plugin = node['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(node['plugins_to_install']))

    def test_node_plugins_to_install_field(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
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

    def test_node_plugins_to_install_field_plugins_from_contained_nodes(self):
        # testing to ensure plugins from nodes with contained_in relationships
        #  to a host node (whether direct
        # or recursive) also get added to the plugins_to_install field.
        # this test also ensures there's no problem with a "duplicate" plugin
        # on the plugins_to_install field,
        # as test_plugin should be added from both test_node2 and test_node4
        # [only one should remain in the end]
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
    test_node2:
        type: test_type
        relationships:
            -   type: cloudify.relationships.contained_in
                target: test_node1
    test_node3:
        type: test_type2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: test_node2
    test_node4:
        type: test_type
        relationships:
            -   type: cloudify.relationships.contained_in
                target: test_node3
node_types:
    cloudify.nodes.Compute: {}
    test_type:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
    test_type2:
        interfaces:
            test_interface2:
                install:
                    implementation: test_plugin2.install
                    inputs: {}
relationships:
    cloudify.relationships.contained_in: {}
plugins:
    test_plugin:
        executor: host_agent
        source: dummy
    test_plugin2:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)

        self.assertEquals(4, len(result['nodes']))
        nodes = self._sort_result_nodes(
            result['nodes'],
            ['test_node1', 'test_node2', 'test_node3', 'test_node4'])

        # ensuring non-host nodes don't have this field
        self.assertTrue('plugins_to_install' not in nodes[1])

        node = nodes[0]
        test_plugin = self._get_plugin_to_install_from_node(
            node, 'test_plugin')
        test_plugin2 = self._get_plugin_to_install_from_node(
            node, 'test_plugin2')
        self.assertEquals('test_plugin', test_plugin['name'])
        self.assertEquals('test_plugin2', test_plugin2['name'])
        self.assertEquals(2, len(nodes[0]['plugins_to_install']))

    def test_instance_relationships_target_node_plugins(self):
        # tests that plugins defined on instance relationships as
        # "run_on_node"="target" will
        # indeed appear in the output on the target node's plugins section
        yaml = self.MINIMAL_BLUEPRINT + """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
                source_interfaces:
                    test_interface1:
                        install: test_plugin1.install
            -   type: test_relationship
                target: test_node
                target_interfaces:
                    test_interface1:
                        install: test_plugin2.install
relationships:
    test_relationship: {}
plugins:
    test_plugin1:
        executor: central_deployment_agent
        source: dummy
    test_plugin2:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(2, len(result['nodes']))
        nodes = self._sort_result_nodes(result['nodes'], ['test_node',
                                                          'test_node2'])
        self.assertEquals('test_node2', nodes[1]['id'])
        self.assertEquals(2, len(nodes[1]['relationships']))

        relationship1 = nodes[1]['relationships'][0]
        self.assertEquals('test_relationship', relationship1['type'])
        self.assertEquals('test_node', relationship1['target_id'])
        rel1_source_ops = relationship1['source_operations']
        self.assertEqual(op_struct('test_plugin1', 'install',
                                   executor='central_deployment_agent'),
                         rel1_source_ops['install'])
        self.assertEqual(op_struct('test_plugin1', 'install',
                                   executor='central_deployment_agent'),
                         rel1_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel1_source_ops))
        self.assertEquals(8, len(relationship1))
        plugin1_def = nodes[1]['plugins'][0]
        self.assertEquals('test_plugin1', plugin1_def['name'])

        relationship2 = nodes[1]['relationships'][1]
        self.assertEquals('test_relationship', relationship2['type'])
        self.assertEquals('test_node', relationship2['target_id'])
        rel2_source_ops = relationship2['target_operations']
        self.assertEqual(op_struct('test_plugin2', 'install',
                                   executor='central_deployment_agent'),
                         rel2_source_ops['install'])
        self.assertEqual(op_struct('test_plugin2', 'install',
                                   executor='central_deployment_agent'),
                         rel2_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel2_source_ops))
        self.assertEquals(8, len(relationship2))

        # expecting the other plugin to be under test_node rather than
        # test_node2:
        plugin2_def = nodes[0]['plugins'][0]
        self.assertEquals('test_plugin2', plugin2_def['name'])


class DeploymentPluginsToInstallTest(AbstractTestParser):

    def test_one_central_one_host_plugin_on_same_node(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
                create:
                    implementation: test_management_plugin.create
                    inputs: {}
plugins:
    test_plugin:
        executor: host_agent
        source: dummy
    test_management_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        deployment_plugins_to_install_for_node = \
            result['nodes'][0][constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_node))
        plugin = deployment_plugins_to_install_for_node[0]
        self.assertEquals('test_management_plugin', plugin['name'])

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_plan))

    def test_one_central_overrides_host_plugin(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    test_node1:
        type: test_type
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    executor: central_deployment_agent
plugins:
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        node = result['nodes'][0]
        deployment_plugins_to_install_for_node = \
            node[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_node))
        plugin = deployment_plugins_to_install_for_node[0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertIsNone(node.get('plugins_to_install'))
        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_plan))
        plugin = deployment_plugins_to_install_for_plan[0]
        self.assertEquals('test_plugin', plugin['name'])

    def test_node_plugins_to_install_no_host(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Root
node_types:
    cloudify.nodes.Root:
        interfaces:
            test_interface:
                start:
                    implementation: cloud.server.start
                    inputs: {}
plugins:
    cloud:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        self.assertEquals(1,
                          len(result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]))

    def test_same_plugin_one_two_nodes(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute
    test_node2:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_management_plugin.start
                    inputs: {}

plugins:
    test_management_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        for node in result['nodes']:
            deployment_plugins_to_install_for_node = \
                node[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
            self.assertEquals(1, len(deployment_plugins_to_install_for_node))
            plugin = deployment_plugins_to_install_for_node[0]
            self.assertEquals('test_management_plugin', plugin['name'])

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_plan))

    def test_two_plugins_on_one_node(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_management_plugin1.start
                    inputs: {}
                create:
                    implementation: test_management_plugin2.create
                    inputs: {}

plugins:
    test_management_plugin1:
        executor: central_deployment_agent
        source: dummy
    test_management_plugin2:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        deployment_plugins_to_install_for_node = \
            result['nodes'][0][constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(2, len(deployment_plugins_to_install_for_node))

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(2, len(deployment_plugins_to_install_for_plan))

    def test_no_operation_mapping_no_plugin(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}

plugins:
    test_management_plugin:
        executor: central_deployment_agent
        source: dummy
    test_plugin:
        executor: host_agent
        source: dummy
"""
        result = self.parse(yaml)
        deployment_plugins_to_install_for_node = \
            result['nodes'][0][constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(0, len(deployment_plugins_to_install_for_node))

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(0, len(deployment_plugins_to_install_for_plan))

    def test_two_identical_plugins_on_node(self):
        yaml = """
node_templates:
    test_node1:
        type: cloudify.nodes.Compute

node_types:
    cloudify.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_management_plugin.start
                    inputs: {}
                create:
                    implementation: test_management_plugin.create
                    inputs: {}

plugins:
    test_management_plugin:
        executor: central_deployment_agent
        source: dummy
"""
        result = self.parse(yaml)
        deployment_plugins_to_install_for_node = \
            result['nodes'][0][constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_node))

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            result[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_plan))
