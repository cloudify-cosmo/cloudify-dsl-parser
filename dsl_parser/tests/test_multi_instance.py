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

import itertools

from dsl_parser import rel_graph

from dsl_parser.multi_instance import (create_deployment_plan,
                                       modify_deployment)
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestMultiInstance(AbstractTestParser):

    BASE_BLUEPRINT = """
node_types:
    cloudify.nodes.Compute:
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

    def modify_multi(self, plan, modified_nodes):
        return modify_deployment(plan['nodes'],
                                 plan['node_instances'],
                                 modified_nodes)

    def setUp(self):
        AbstractTestParser.setUp(self)

    def tearDown(self):
        AbstractTestParser.tearDown(self)

    def test_single_node(self):

        yaml = self.BASE_BLUEPRINT + """

    host:
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
    host2:
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        instances:
            deploy: 2
    host2:
        type: cloudify.nodes.Compute
        instances:
            deploy: 2
    host3:
        type: cloudify.nodes.Compute
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
        self.assertEqual(set(node_ids), set(target_ids))

    def _assert_all_to_one(self, source_relationships, node_ids, target_name):
        relationships = self._relationships_by_target_name(
            source_relationships, target_name)
        target_ids = [rel['target_id'] for rel in relationships]
        self.assertEqual(1, len(set(target_ids)))
        self.assertIn(target_ids[0], node_ids)
        return target_ids[0]

    def _assert_all_to_all(self, source_relationships_lists,
                           node_ids, target_name):
        for source_relationships in source_relationships_lists:
            relationships = self._relationships_by_target_name(
                source_relationships, target_name)
            target_ids = [rel['target_id'] for rel in relationships]
            self.assertEqual(set(node_ids), set(target_ids))

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

    def test_modified_single_node_added(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 2}
        })
        self._assert_modification(modification, 1, 0, 1, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        for instance in added_and_related:
            self.assertEqual('host', instance['name'])
            self.assertIn('host_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])

    def test_modified_single_node_removed(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
        instances:
            deploy: 2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 1}
        })
        self._assert_modification(modification, 0, 1, 0, 1)
        self._assert_removed_in_previous(plan, modification)

    def test_modified_single_node_added_with_child_contained_in_1(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 2}
        })
        self._assert_modification(modification, 2, 0, 2, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host_nodes = self._nodes_by_name(added_and_related, 'host')
        self.assertEqual(1, len(host_nodes))
        for instance in host_nodes:
            self.assertEqual('host', instance['name'])
            self.assertIn('host_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')

    def test_modified_single_node_removed_with_child_contained_in_1(self):
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
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 1}
        })
        self._assert_modification(modification, 0, 2, 0, 2)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host_nodes = self._nodes_by_name(removed_and_related, 'host')
        self.assertEqual(1, len(host_nodes))
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')
        self._assert_each_node_valid_hosted(db_nodes, host_nodes)

    def test_modified_single_node_added_with_child_contained_in_2(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'db': {'instances': 2}
        })
        self._assert_modification(modification, 2, 0, 1, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host_nodes = self._nodes_by_name(added_and_related, 'host')
        self.assertEqual(1, len(host_nodes))
        for instance in host_nodes:
            self.assertEqual('host', instance['name'])
            self.assertIn('host_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')

    def test_modified_single_node_removed_with_child_contained_in_2(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'db': {'instances': 1}
        })
        self._assert_modification(modification, 0, 2, 0, 1)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host_nodes = self._nodes_by_name(removed_and_related, 'host')
        self.assertEqual(1, len(host_nodes))
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')
        self._assert_each_node_valid_hosted(db_nodes, host_nodes)

    def test_modified_two_nodes_added_with_child_contained_in(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
    db:
        type: db
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 2},
            'db': {'instances': 2}
        })
        self._assert_modification(modification, 5, 0, 4, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host_nodes = self._nodes_by_name(added_and_related, 'host')
        self.assertEqual(2, len(host_nodes))
        for instance in host_nodes:
            self.assertEqual('host', instance['name'])
            self.assertIn('host_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(3, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')

    def test_modified_two_nodes_removed_with_child_contained_in(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
        instances:
            deploy: 2
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 1},
            'db': {'instances': 1}
        })
        self._assert_modification(modification, 0, 5, 0, 4)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host_nodes = self._nodes_by_name(removed_and_related, 'host')
        self.assertEqual(2, len(host_nodes))
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(3, len(db_nodes))
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host_nodes), 'host')

    def test_modified_single_node_added_with_connected_1(self):
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
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host1': {'instances': 2}
        })
        self._assert_modification(modification, 3, 0, 2, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host1_nodes = self._nodes_by_name(added_and_related, 'host1')
        host2_nodes = self._nodes_by_name(added_and_related, 'host2')
        self.assertEqual(1, len(host1_nodes))
        self.assertEqual(1, len(host2_nodes))
        for i, host_nodes in enumerate([host1_nodes, host2_nodes], start=1):
            for instance in host_nodes:
                self.assertEqual('host{0}'.format(i), instance['name'])
                self.assertIn('host{0}_'.format(i), instance['id'])
                self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host1_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host1_nodes), 'host1')
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_single_node_removed_with_connected_1(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
        instances:
            deploy: 2
    host2:
        type: cloudify.types.host
        instances:
            deploy: 2
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host1': {'instances': 1}
        })
        self._assert_modification(modification, 0, 5, 0, 3)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host1_nodes = self._nodes_by_name(removed_and_related, 'host1')
        host2_nodes = self._nodes_by_name(removed_and_related, 'host2')
        self.assertEqual(1, len(host1_nodes))
        self.assertEqual(2, len(host2_nodes))
        for i, host_nodes in enumerate([host1_nodes, host2_nodes], start=1):
            for instance in host_nodes:
                self.assertEqual('host{0}'.format(i), instance['name'])
                self.assertIn('host{0}_'.format(i), instance['id'])
                self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(2, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host1_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host1_nodes), 'host1')
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_single_node_added_with_connected_2(self):
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
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host2': {'instances': 2}
        })
        self._assert_modification(modification, 2, 0, 1, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host2_nodes = self._nodes_by_name(added_and_related, 'host2')
        self.assertEqual(1, len(host2_nodes))
        for instance in host2_nodes:
            self.assertEqual('host2', instance['name'])
            self.assertIn('host2_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_single_node_removed_with_connected_2(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
        instances:
            deploy: 2
    host2:
        type: cloudify.types.host
        instances:
            deploy: 2
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host2': {'instances': 1}
        })
        self._assert_modification(modification, 0, 5, 0, 1)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host2_nodes = self._nodes_by_name(removed_and_related, 'host2')
        self.assertEqual(1, len(host2_nodes))
        for instance in host2_nodes:
            self.assertEqual('host2', instance['name'])
            self.assertIn('host2_', instance['id'])
            self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(4, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_single_node_added_with_connected_3(self):
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
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'db': {'instances': 2}
        })
        self._assert_modification(modification, 3, 0, 1, 0)
        self._assert_added_not_in_previous(plan, modification)
        added_and_related = modification['added_and_related']
        host1_nodes = self._nodes_by_name(added_and_related, 'host1')
        host2_nodes = self._nodes_by_name(added_and_related, 'host2')
        self.assertEqual(1, len(host1_nodes))
        self.assertEqual(1, len(host2_nodes))
        for i, host_nodes in enumerate([host1_nodes, host2_nodes], start=1):
            for instance in host_nodes:
                self.assertEqual('host{0}'.format(i), instance['name'])
                self.assertIn('host{0}_'.format(i), instance['id'])
                self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(1, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host1_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host1_nodes), 'host1')
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_single_node_removed_with_connected_3(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
        instances:
            deploy: 2
    host2:
        type: cloudify.types.host
        instances:
            deploy: 2
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
            -   type: cloudify.relationships.connected_to
                target: host2
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'db': {'instances': 1}
        })
        self._assert_modification(modification, 0, 6, 0, 2)
        self._assert_removed_in_previous(plan, modification)
        removed_and_related = modification['removed_and_related']
        host1_nodes = self._nodes_by_name(removed_and_related, 'host1')
        host2_nodes = self._nodes_by_name(removed_and_related, 'host2')
        self.assertEqual(2, len(host1_nodes))
        self.assertEqual(2, len(host2_nodes))
        for i, host_nodes in enumerate([host1_nodes, host2_nodes], start=1):
            for instance in host_nodes:
                self.assertEqual('host{0}'.format(i), instance['name'])
                self.assertIn('host{0}_'.format(i), instance['id'])
                self.assertEqual(instance['host_id'], instance['id'])
        db_nodes = self._nodes_by_name(removed_and_related, 'db')
        self.assertEqual(2, len(db_nodes))
        for instance in db_nodes:
            self.assertEqual('db', instance['name'])
            self.assertIn('db_', instance['id'])
        self._assert_each_node_valid_hosted(db_nodes, host1_nodes)
        self._assert_contained(self._nodes_relationships(db_nodes),
                               self._node_ids(host1_nodes), 'host1')
        self._assert_all_to_all([node['relationships'] for node in db_nodes],
                                self._node_ids(host2_nodes), 'host2')

    def test_modified_added_with_connected_all_to_one(self):
        yaml = self.BASE_BLUEPRINT + """
    host1:
        type: cloudify.types.host
    host2:
        type: cloudify.types.host
        instances:
            deploy: 5
    db:
        type: db
        instances:
            deploy: 5
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host1
            -   type: cloudify.relationships.connected_to
                target: host2
                properties:
                    connection_type: all_to_one
"""
        plan = self.parse_multi(yaml)
        node_instances = plan['node_instances']
        db_nodes = self._nodes_by_name(node_instances, 'db')
        host2_nodes = self._nodes_by_name(node_instances, 'host2')
        initial_target_id = self._assert_all_to_one(
            self._nodes_relationships(db_nodes, 'host2'),
            self._node_ids(host2_nodes),
            'host2')
        modification = self.modify_multi(plan, {
            'host2': {'instances': 10},
            'db': {'instances': 10}
        })
        self._assert_modification(modification, 12, 0, 10, 0)
        added_and_related = modification['added_and_related']
        added_db_nodes = self._nodes_by_name(added_and_related, 'db')
        self.assertEqual(5, len(added_db_nodes))
        added_host1_nodes = self._nodes_by_name(added_and_related, 'host1')
        self.assertEqual(1, len(added_host1_nodes))
        added_host2_nodes = self._nodes_by_name(added_and_related, 'host2')
        self.assertEqual(6, len(added_host2_nodes))
        new_target_id = self._assert_all_to_one(
            self._nodes_relationships(added_db_nodes, 'host2'),
            self._node_ids(host2_nodes + added_host2_nodes),
            'host2')
        self.assertEqual(initial_target_id, new_target_id)

    def test_removed_ids_hint(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.types.host
        instances:
            deploy: 3
    db:
        type: db
        instances:
            deploy: 2
        relationships:
            -   type: cloudify.relationships.contained_in
                target: host
"""
        plan = self.parse_multi(yaml)
        nodes = plan['node_instances']
        host_ids = self._node_ids(self._nodes_by_name(nodes, 'host'))
        db_ids = self._node_ids(self._nodes_by_name(nodes, 'db'))

        for host_id in host_ids:
            modification = self.modify_multi(plan, {
                'host': {
                    'instances': 2,
                    'removed_ids_include_hint': [host_id]
                }
            })
            self._assert_modification(modification, 0, 3, 0, 3)
            removed_host_ids = self._node_ids(self._nodes_by_name(
                modification['removed_and_related'], 'host'))
            self.assertEqual(removed_host_ids, [host_id])

        for host_id in host_ids:
            modification = self.modify_multi(plan, {
                'host': {
                    'instances': 2,
                    'removed_ids_exclude_hint': [host_id]
                }
            })
            self._assert_modification(modification, 0, 3, 0, 3)
            removed_host_ids = self._node_ids(self._nodes_by_name(
                modification['removed_and_related'], 'host'))
            self.assertNotIn(host_id, removed_host_ids)

        for db_id in db_ids:
            modification = self.modify_multi(plan, {
                'db': {
                    'instances': 1,
                    'removed_ids_include_hint': [db_id]
                }
            })
            self._assert_modification(modification, 0, 6, 0, 3)
            removed_db_ids = self._node_ids(self._nodes_by_name(
                modification['removed_and_related'], 'db'))
            self.assertIn(db_id, removed_db_ids)

        for db_id in db_ids:
            modification = self.modify_multi(plan, {
                'db': {
                    'instances': 1,
                    'removed_ids_exclude_hint': [db_id]
                }
            })
            self._assert_modification(modification, 0, 6, 0, 3)
            removed_db_ids = self._node_ids(self._nodes_by_name(
                modification['removed_and_related'], 'db'))
            self.assertNotIn(db_id, removed_db_ids)

        # give all nodes as include hint to see we only take what is needed
        modification = self.modify_multi(plan, {
            'db': {
                'instances': 1,
                'removed_ids_include_hint': db_ids
            }
        })
        self._assert_modification(modification, 0, 6, 0, 3)

        # give all nodes as exclude hint to see we still take what is needed
        modification = self.modify_multi(plan, {
            'db': {
                'instances': 1,
                'removed_ids_exclude_hint': db_ids
            }
        })
        self._assert_modification(modification, 0, 6, 0, 3)

    def _nodes_relationships(self, nodes, target_name=None):
        relationships = []
        for node in nodes:
            for rel in node['relationships']:
                if target_name and rel['target_name'] != target_name:
                    continue
                relationships.append(rel)
        return relationships

    def _assert_added_not_in_previous(self, plan, modification):
        previous_node_instances = plan['node_instances']
        added_and_related = modification['added_and_related']
        previous_graph = rel_graph.build_node_graph(previous_node_instances)
        added_nodes_graph = rel_graph.build_node_graph(added_and_related)
        for instance_id, data in added_nodes_graph.nodes_iter(data=True):
            instance = data['node']
            if instance.get('modification') == 'added':
                self.assertNotIn(instance_id, previous_graph)
            else:
                self.assertIn(instance_id, previous_graph)
        for source, target, in added_nodes_graph.edges_iter():
            self.assertFalse(previous_graph.has_edge(source, target))

    def _assert_removed_in_previous(self, plan, modification):
        previous_node_instances = plan['node_instances']
        removed_and_related = modification['removed_and_related']
        previous_graph = rel_graph.build_node_graph(previous_node_instances)
        removed_nodes_graph = rel_graph.build_node_graph(removed_and_related)
        for instance_id, data in removed_nodes_graph.nodes_iter(data=True):
            self.assertIn(instance_id, previous_graph)
        for source, target, in removed_nodes_graph.edges_iter():
            self.assertTrue(previous_graph.has_edge(source, target))

    def _assert_modification(self,
                             modification,
                             expected_added_and_related_count,
                             expected_removed_and_related_count,
                             expected_added_count,
                             expected_removed_count):
        added_and_related = modification['added_and_related']
        removed_and_related = modification['removed_and_related']
        added = [instance for instance in added_and_related
                 if instance.get('modification') == 'added']
        removed = [instance for instance in removed_and_related
                   if instance.get('modification') == 'removed']

        self.assertEqual(expected_added_and_related_count,
                         len(added_and_related))
        self.assertEqual(expected_removed_and_related_count,
                         len(removed_and_related))
        self.assertEqual(expected_added_count,
                         len(added))
        self.assertEqual(expected_removed_count,
                         len(removed))
