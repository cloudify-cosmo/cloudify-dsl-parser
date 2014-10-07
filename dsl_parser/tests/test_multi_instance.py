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

__author__ = 'dank'

import random
import itertools

from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser.multi_instance import create_deployment_plan
from dsl_parser import rel_graph


class TestMultiInstance(AbstractTestParser):

    BASE_BLUEPRINT = """
node_types:
    cloudify.types.host:
        properties:
            x:
                default: y
    db: {}
    webserver: {}
    db_dependent: {}
    type: {}
    network: {}
relationships:
    test_relationship: {}
    cloudify.relationships.depends_on:
        properties:
            connection_type:
                default: 'all_to_all'
    cloudify.relationships.contained_in:
        derived_from: cloudify.relationships.depends_on
    cloudify.relationships.connected_to:
        derived_from: cloudify.relationships.depends_on

node_templates:
    """

    def parse_multi(self, yaml):
        return create_deployment_plan(self.parse(yaml))

    def setUp(self):
        random.seed(0)
        AbstractTestParser.setUp(self)

    def tearDown(self):
        AbstractTestParser.tearDown(self)

    def test_single_node(self):

        yaml = self.BASE_BLUEPRINT + """

    host:
        type: cloudify.types.host
        instances:
            deploy: 2
"""

        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(2, len(nodes))
        self.assertEquals(2, len(set(self._node_ids(nodes))))

        self.assertIn('host_', nodes[0]['id'])
        self.assertIn('host_', nodes[1]['id'])
        self.assertEquals(nodes[0]['id'], nodes[0]['host_id'])
        self.assertEquals(nodes[1]['id'], nodes[1]['host_id'])

    def test_two_nodes_one_contained_in_other(self):

        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(2, len(nodes))
        self.assertEquals(2, len(set(self._node_ids(nodes))))
        db = self._nodes_by_name(nodes, 'db')[0]
        host = self._nodes_by_name(nodes, 'host')[0]

        self.assertIn('host_', host['id'])
        self.assertIn('db_', db['id'])
        self.assertEquals(host['id'], host['host_id'])
        self.assertEquals(host['id'], db['host_id'])

        db_relationships = db['relationships']
        self.assertEquals(1, len(db_relationships))
        self.assertEquals(host['id'], db_relationships[0]['target_id'])

    def test_two_nodes_one_contained_in_other_two_instances(self):

        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
        instances:
            deploy: 2
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(4, len(nodes))
        self.assertEqual(4, len(set(self._node_ids(nodes))))

        db_nodes = self._nodes_by_name(nodes, 'db')
        host_nodes = self._nodes_by_name(nodes, 'host')
        host_node_ids = self._node_ids(host_nodes)

        db_1 = db_nodes[0]
        db_2 = db_nodes[1]
        host_1 = host_nodes[0]
        host_2 = host_nodes[1]

        self.assertIn('host_', host_1['id'])
        self.assertIn('host_', host_2['id'])
        self.assertEqual(host_1['id'], host_1['host_id'])
        self.assertEqual(host_2['id'], host_2['host_id'])

        self.assertIn('db_', db_1['id'])
        self.assertIn('db_', db_2['id'])
        self.assertIn(db_1['host_id'], host_node_ids)
        self.assertIn(db_2['host_id'], host_node_ids)
        self.assertNotEqual(db_1['host_id'], db_2['host_id'])

        db1_relationships = db_1['relationships']
        self.assertEquals(1, len(db1_relationships))
        self.assertEquals(db_1['host_id'], db1_relationships[0]['target_id'])
        db2_relationships = db_2['relationships']
        self.assertEquals(1, len(db2_relationships))
        self.assertEquals(db_2['host_id'], db2_relationships[0]['target_id'])

    def test_single_connected_to(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
    host2:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
    webserver:
        type: webserver
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host2
            -   type: cloudify.relationships.connected_to
                target: db
    db_dependent:
        type: db_dependent
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
            -   type: cloudify.relationships.connected_to
                target: db
"""

        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(5, len(nodes))
        self.assertEquals(5, len(set(self._node_ids(nodes))))

        host1 = self._nodes_by_name(nodes, 'host1')[0]
        host2 = self._nodes_by_name(nodes, 'host2')[0]
        db = self._nodes_by_name(nodes, 'db')[0]
        webserver = self._nodes_by_name(nodes, 'webserver')[0]
        db_dependent = self._nodes_by_name(nodes, 'db_dependent')[0]

        self.assertIn('host1_', host1['id'])
        self.assertIn('host2_', host2['id'])
        self.assertIn('db_', db['id'])
        self.assertIn('webserver_', webserver['id'])
        self.assertIn('db_dependent_', db_dependent['id'])

        self.assertEquals(host1['id'], host1['host_id'])
        self.assertEquals(host2['id'], host2['host_id'])
        self.assertEquals(host1['id'], db['host_id'])
        self.assertEquals(host2['id'], webserver['host_id'])
        self.assertEquals(host1['id'], db_dependent['host_id'])

        db_relationships = db['relationships']
        self.assertEquals(1, len(db_relationships))
        self.assertEquals(host1['id'], db_relationships[0]['target_id'])

        webserver_relationships = webserver['relationships']
        self.assertEquals(2, len(webserver_relationships))
        webserver_host_rel = self._relationships_by_target_name(
            webserver_relationships, 'host2')[0]
        webserver_db_rel = self._relationships_by_target_name(
            webserver_relationships, 'db')[0]
        self.assertEquals(host2['id'],
                          webserver_host_rel['target_id'])
        self.assertEquals(db['id'],
                          webserver_db_rel['target_id'])

        db_dependent_relationships = db_dependent['relationships']
        self.assertEquals(2, len(db_dependent_relationships))
        db_dependent_db_rel = self._relationships_by_target_name(
            db_dependent_relationships, 'db')[0]
        db_dependent_host_rel = self._relationships_by_target_name(
            db_dependent_relationships, 'host1')[0]
        self.assertEquals(db['id'],
                          db_dependent_db_rel['target_id'])
        self.assertEquals(host1['id'],
                          db_dependent_host_rel['target_id'])

    def test_prepare_deployment_plan_single_none_host_node(self):

        yaml = self.BASE_BLUEPRINT + """
    node1_id:
        type: type
"""

        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(1, len(nodes))
        self.assertIn('node1_id_', nodes[0]['id'])
        self.assertTrue('host_id' not in nodes[0])

    def test_connected_to_and_contained_in_with_and_without_host_id(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
        instances:
            deploy: 2
    host2:
        type: cloudify.types.host
        instances:
            deploy: 2
    host3:
        type: cloudify.types.host
        instances:
            deploy: 2
    network:
        type: network
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
    webserver1:
        type: webserver
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host2
            -   type: cloudify.relationships.connected_to
                target: db
                properties:
                    connection_type: all_to_one
    webserver2:
        type: webserver
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host2
            -   type: cloudify.relationships.depends_on
                target: db
                properties:
                    connection_type: all_to_all
    db_dependent:
        type: db_dependent
        relationships:
            -   type: cloudify.relationships.contained_in
                target: db
"""
        multi_plan = self.parse_multi(yaml)
        nodes = multi_plan['node_instances']
        self.assertEquals(19, len(nodes))
        self.assertEquals(19, len(set(self._node_ids(nodes))))

        network_1 = self._nodes_by_name(nodes, 'network')[0]

        host1_nodes = self._nodes_by_name(nodes, 'host1')
        host1_1 = host1_nodes[0]
        host1_2 = host1_nodes[1]
        host2_nodes = self._nodes_by_name(nodes, 'host2')
        host2_1 = host2_nodes[0]
        host2_2 = host2_nodes[1]
        host3_nodes = self._nodes_by_name(nodes, 'host3')
        host3_1 = host3_nodes[0]
        host3_2 = host3_nodes[1]
        webserver1_nodes = self._nodes_by_name(nodes, 'webserver1')
        webserver1_1 = webserver1_nodes[0]
        webserver1_2 = webserver1_nodes[1]
        webserver2_nodes = self._nodes_by_name(nodes, 'webserver2')
        webserver2_1 = webserver2_nodes[0]
        webserver2_2 = webserver2_nodes[1]
        db_nodes = self._nodes_by_name(nodes, 'db')
        db_1 = db_nodes[0]
        db_2 = db_nodes[1]
        db_3 = db_nodes[2]
        db_4 = db_nodes[3]
        db_dependent_nodes = self._nodes_by_name(nodes, 'db_dependent')
        db_dependent_1 = db_dependent_nodes[0]
        db_dependent_2 = db_dependent_nodes[1]
        db_dependent_3 = db_dependent_nodes[2]
        db_dependent_4 = db_dependent_nodes[3]

        self.assertIn('network_', network_1['id'])
        self.assertIn('host1_', host1_1['id'])
        self.assertIn('host1_', host1_2['id'])
        self.assertIn('host2_', host2_1['id'])
        self.assertIn('host2_', host2_2['id'])
        self.assertIn('host3_', host3_1['id'])
        self.assertIn('host3_', host3_2['id'])
        self.assertIn('webserver1_', webserver1_1['id'])
        self.assertIn('webserver1_', webserver1_2['id'])
        self.assertIn('webserver2_', webserver2_1['id'])
        self.assertIn('webserver2_', webserver2_2['id'])
        self.assertIn('db_', db_1['id'])
        self.assertIn('db_', db_2['id'])
        self.assertIn('db_', db_3['id'])
        self.assertIn('db_', db_4['id'])
        self.assertIn('db_dependent_', db_dependent_1['id'])
        self.assertIn('db_dependent_', db_dependent_2['id'])
        self.assertIn('db_dependent_', db_dependent_3['id'])
        self.assertIn('db_dependent_', db_dependent_4['id'])

        self.assertTrue('host_id' not in network_1)

        self.assertEquals(host1_1['id'], host1_1['host_id'])
        self.assertEquals(host1_2['id'], host1_2['host_id'])
        self.assertEquals(host2_1['id'], host2_1['host_id'])
        self.assertEquals(host2_2['id'], host2_2['host_id'])
        self.assertEquals(host3_1['id'], host3_1['host_id'])
        self.assertEquals(host3_2['id'], host3_2['host_id'])

        self._assert_each_node_valid_hosted(
            webserver1_nodes, host2_nodes)
        self._assert_each_node_valid_hosted(
            webserver2_nodes, host2_nodes)
        self._assert_each_node_valid_hosted(
            db_nodes, host1_nodes)
        self._assert_each_node_valid_hosted(
            db_dependent_nodes, host1_nodes)

        network_1_relationships = network_1['relationships']
        host1_1_relationships = host1_1['relationships']
        host1_2_relationships = host1_2['relationships']
        host2_1_relationships = host2_1['relationships']
        host2_2_relationships = host2_2['relationships']
        host3_1_relationships = host3_1['relationships']
        host3_2_relationships = host2_2['relationships']
        webserver1_1_relationships = webserver1_1['relationships']
        webserver1_2_relationships = webserver1_2['relationships']
        webserver2_1_relationships = webserver2_1['relationships']
        webserver2_2_relationships = webserver2_2['relationships']
        db_1_relationships = db_1['relationships']
        db_2_relationships = db_2['relationships']
        db_3_relationships = db_3['relationships']
        db_4_relationships = db_4['relationships']
        db_dependent_1_relationships = db_dependent_1['relationships']
        db_dependent_2_relationships = db_dependent_2['relationships']
        db_dependent_3_relationships = db_dependent_3['relationships']
        db_dependent_4_relationships = db_dependent_4['relationships']

        self.assertEquals(0, len(network_1_relationships))
        self.assertEquals(0, len(host1_1_relationships))
        self.assertEquals(0, len(host1_2_relationships))
        self.assertEquals(0, len(host2_1_relationships))
        self.assertEquals(0, len(host2_2_relationships))
        self.assertEquals(0, len(host3_1_relationships))
        self.assertEquals(0, len(host3_2_relationships))
        self.assertEquals(2, len(webserver1_1_relationships))
        self.assertEquals(2, len(webserver1_2_relationships))
        self.assertEquals(5, len(webserver2_1_relationships))
        self.assertEquals(5, len(webserver2_2_relationships))
        self.assertEquals(1, len(db_1_relationships))
        self.assertEquals(1, len(db_2_relationships))
        self.assertEquals(1, len(db_3_relationships))
        self.assertEquals(1, len(db_4_relationships))
        self.assertEquals(1, len(db_dependent_1_relationships))
        self.assertEquals(1, len(db_dependent_2_relationships))
        self.assertEquals(1, len(db_dependent_3_relationships))
        self.assertEquals(1, len(db_dependent_4_relationships))

        self._assert_contained(webserver1_1_relationships +
                               webserver1_2_relationships,
                               self._node_ids(host2_nodes), 'host2')

        self._assert_all_to_one(webserver1_1_relationships +
                                webserver1_2_relationships,
                                self._node_ids(db_nodes), 'db')

        self._assert_contained(webserver2_1_relationships +
                               webserver2_2_relationships,
                               self._node_ids(host2_nodes), 'host2')

        self._assert_all_to_all([webserver2_1_relationships,
                                 webserver2_2_relationships],
                                self._node_ids(db_nodes), 'db')

        self._assert_contained(db_1_relationships +
                               db_2_relationships +
                               db_3_relationships +
                               db_4_relationships,
                               self._node_ids(host1_nodes), 'host1')

        self._assert_contained(db_dependent_1_relationships +
                               db_dependent_2_relationships +
                               db_dependent_3_relationships +
                               db_dependent_4_relationships,
                               self._node_ids(db_nodes), 'db')

    def _relationships_by_target_name(self, relationships, name):
        return [rel for rel in relationships if rel['target_name'] == name]

    def _nodes_by_name(self, nodes, name):
        return [node for node in nodes if node['name'] == name]

    def _node_ids(self, nodes):
        return [node['id'] for node in nodes]

    def _assert_each_node_valid_hosted(self, nodes, hosts):
        node_ids = self._node_ids(nodes)
        host_ids = self._node_ids(hosts)
        self.assertEqual(len(node_ids) % len(host_ids), 0)
        self.assertEqual(len(node_ids), len(set(node_ids)))
        node_host_ids = [node['host_id'] for node in nodes]
        for node_host_id in node_host_ids:
            self.assertIn(node_host_id, host_ids)
        key_fun = lambda n: n['host_id']
        for _, g in itertools.groupby(sorted(nodes, key=key_fun), key=key_fun):
            self.assertEqual(len(list(g)), len(node_ids) / len(host_ids))

    def _assert_contained(self, source_relationships, node_ids, target_name):
        relationships = self._relationships_by_target_name(
            source_relationships, target_name)
        target_ids = [rel['target_id'] for rel in relationships]
        self.assertSetEqual(set(node_ids), set(target_ids))

    def _assert_all_to_one(self, source_relationships, node_ids, target_name):
        relationships = self._relationships_by_target_name(
            source_relationships, target_name)
        target_ids = [rel['target_id'] for rel in relationships]
        self.assertEqual(1, len(set(target_ids)))
        self.assertIn(target_ids[0], node_ids)

    def _assert_all_to_all(self, source_relationships_lists,
                           node_ids, target_name):
        for source_relationships in source_relationships_lists:
            relationships = self._relationships_by_target_name(
                source_relationships, target_name)
            target_ids = [rel['target_id'] for rel in relationships]
            self.assertSetEqual(set(node_ids), set(target_ids))

    def test_illegal_connection_type(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.connected_to
                target: host
                properties:
                    connection_type: invalid
"""
        self.assertRaises(rel_graph.IllegalConnectedToConnectionType,
                          self.parse_multi, yaml)

    def test_unsupported_relationship(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: test_relationship
                target: host
"""
        self.assertRaises(rel_graph.UnsupportedRelationship,
                          self.parse_multi, yaml)
