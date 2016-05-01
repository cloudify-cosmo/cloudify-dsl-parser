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

import itertools

from dsl_parser import rel_graph
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class BaseTestMultiInstance(AbstractTestParser):

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

    @staticmethod
    def _relationships_by_target_name(relationships, name):
        return [rel for rel in relationships if rel['target_name'] == name]

    @staticmethod
    def _nodes_by_name(nodes, name):
        return [node for node in nodes if node['name'] == name]

    @staticmethod
    def _node_ids(nodes):
        return [node['id'] for node in nodes]

    def _assert_each_node_valid_hosted(self, nodes, hosts):
        node_ids = self._node_ids(nodes)
        host_ids = self._node_ids(hosts)
        self.assertEqual(len(node_ids) % len(host_ids), 0)
        self.assertEqual(len(node_ids), len(set(node_ids)))
        node_host_ids = [node['host_id'] for node in nodes]
        for node_host_id in node_host_ids:
            self.assertIn(node_host_id, host_ids)

        def key_fun(n):
            return n['host_id']

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

    @staticmethod
    def _nodes_relationships(nodes, target_name=None):
        relationships = []
        for node in nodes:
            for rel in node['relationships']:
                if target_name and rel['target_name'] != target_name:
                    continue
                relationships.append(rel)
        return relationships

    def _assert_added_not_in_previous(self, plan, modification):
        plan_node_graph = rel_graph.build_node_graph(
            nodes=plan['nodes'],
            scaling_groups=plan['scaling_groups'])
        previous_node_instances = plan['node_instances']
        added_and_related = modification['added_and_related']
        previous_graph, _ = rel_graph.build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=previous_node_instances)
        added_nodes_graph, _ = rel_graph.build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=added_and_related)
        for instance_id, data in added_nodes_graph.nodes_iter(data=True):
            instance = data['node']
            if instance.get('modification') == 'added':
                self.assertNotIn(instance_id, previous_graph)
            else:
                self.assertIn(instance_id, previous_graph)
        for source, target, in added_nodes_graph.edges_iter():
            self.assertFalse(previous_graph.has_edge(source, target))

    def _assert_removed_in_previous(self, plan, modification):
        plan_node_graph = rel_graph.build_node_graph(
            nodes=plan['nodes'],
            scaling_groups=plan['scaling_groups'])
        previous_node_instances = plan['node_instances']
        removed_and_related = modification['removed_and_related']
        previous_graph, _ = rel_graph.build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=previous_node_instances)
        removed_nodes_graph, _ = rel_graph.build_previous_deployment_node_graph(  # noqa
            plan_node_graph=plan_node_graph,
            previous_node_instances=removed_and_related)
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
