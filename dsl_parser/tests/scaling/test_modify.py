########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

from dsl_parser.tests import scaling


class TestMultiInstanceModify(scaling.BaseTestMultiInstance):

    def test_modified_single_node_added(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.nodes.Compute
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

    def test_modified_single_no_actual_modification(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.nodes.Compute
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(plan, {
            'host': {'instances': 1}
        })
        self._assert_modification(modification, 0, 0, 0, 0)

    def test_modified_single_node_removed(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
    host2:
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    host2:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
    host2:
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    host2:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
    host2:
        type: cloudify.nodes.Compute
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
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    host2:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 2
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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
        type: cloudify.nodes.Compute
    host2:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 5
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 5
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

    def test_scale_out_from_zero_with_relationship(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 0
                    min_instances: 0
        relationships:
            -   type: cloudify.relationships.connected_to
                target: webserver
                properties:
                    connection_type: all_to_one
    webserver:
        type: webserver
"""
        plan = self.parse_multi(yaml)
        modification = self.modify_multi(
            plan, modified_nodes={'host': {'instances': 1}})
        added = modification['added_and_related']
        self.assertEqual(2, len(added))

    def test_removed_ids_hint(self):
        yaml = self.BASE_BLUEPRINT + """
    host:
        type: cloudify.nodes.Compute
        capabilities:
            scalable:
                properties:
                    default_instances: 3
    db:
        type: db
        capabilities:
            scalable:
                properties:
                    default_instances: 2
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

    def _test_base_nodes(self):
        return self.BASE_BLUEPRINT + """
            without_rel:
                type: type
            with_rel:
                type: type
        """

    def test_new_node(self):
        blueprint = self._test_base_nodes()

        plan = self.parse_multi(blueprint)

        plan['nodes'].append({
            'name': 'new_node',
            'id': 'new_node',
            'type': 'new_type',
            'number_of_instances': 1,
            'deploy_number_of_instances': 1,
            'min_number_of_instances': 1,
            'max_number_of_instances': 1,
        })
        new_node = [n for n in plan['nodes'] if n['id'] == 'new_node'][0]

        modified_nodes = [new_node]
        self.modify_multi(plan, modified_nodes=modified_nodes)

    def test_new_relationship(self):
        blueprint = self._test_base_nodes()

        connected_to = 'cloudify.relationships.connected_to'
        rel_type = connected_to

        plan = self.parse_multi(blueprint)

        with_rel = [n for n in plan['nodes'] if n['id'] == 'with_rel'][0]
        without_rel = [n for n in plan['nodes'] if n['id'] == 'without_rel'][0]
        with_rel['relationships'] = \
            [{'type': rel_type,
              'type_hierarchy': [rel_type],
              'target_id': without_rel['id'],
              'source_interface': {
                  'cloudify.interfaces.relationship_lifecycle': {
                      'preconfigure': 'scripts/increment.sh',
                      'establish': 'scripts/increment.sh',
                      'postconfigure': 'scripts/increment.sh'
                  }
              },
              'properties': {
                  'connection_type': 'all_to_all'
              }}]
        modified_nodes = [with_rel]
        self.modify_multi(plan, modified_nodes=modified_nodes)
