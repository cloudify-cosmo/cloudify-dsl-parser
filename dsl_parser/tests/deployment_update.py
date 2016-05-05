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
import copy

from dsl_parser.multi_instance import modify_deployment
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestDeploymentUpdate(AbstractTestParser):
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

    BASE_NODES = """
    without_rel:
        type: type
    with_rel:
        type: type
"""

    @staticmethod
    def modify_multi(plan, modified_nodes):
        return modify_deployment(
                nodes=modified_nodes,
                previous_nodes=plan['nodes'],
                previous_node_instances=plan['node_instances'],
                modified_nodes=(),
                scaling_groups={})

    def test_add_node(self):
        blueprint = self.BASE_BLUEPRINT + self.BASE_NODES

        plan = self.parse_multi(blueprint)
        plan['nodes'].append({
            'name': 'new_node',
            'id': 'new_node',
            'type': 'new_type',
            'number_of_instances': 1,
            'deploy_number_of_instances': 1,
            'min_number_of_instances': 1,
            'max_number_of_instances': 1,
            'relationships': [
                {'type': 'cloudify.relationships.connected_to',
                 'target_id': 'without_rel',
                 'type_hierarchy': ['cloudify.relationships.connected_to'],
                 'properties': {
                     'connection_type': 'all_to_all'
                 },
                 }
            ]
        })

        modified_nodes = plan['nodes']
        node_instances = self.modify_multi(plan, modified_nodes=modified_nodes)

        self.assertEqual(len(node_instances['added_and_related']), 2)
        added_and_related = node_instances['added_and_related']
        added = [n for n in added_and_related if 'modification' in n]
        related = [n for n in added_and_related if n not in added]
        self.assertEqual(len(added), 1)
        self.assertEqual(len(related), 1)
        self.assertEqual(len(node_instances['removed_and_related']), 0)
        self.assertEqual(len(node_instances['extended_and_related']), 0)
        self.assertEqual(len(node_instances['reduced_and_related']), 0)

    def test_remove_node(self):
        blueprint = self.BASE_BLUEPRINT + self.BASE_NODES + """
        relationships:
            -  type: cloudify.relationships.connected_to
               target: without_rel
    """

        plan = self.parse_multi(blueprint)
        nodes = \
            copy.deepcopy(
                    [n for n in plan['nodes'] if n['id'] != 'without_rel'])
        with_rel_node = nodes[0]
        with_rel_node['relationships'] = [r for r in
                                          with_rel_node['relationships']
                                          if r['target_id'] != 'without_rel']
        node_instances = self.modify_multi(plan, modified_nodes=nodes)

        self.assertEqual(len(node_instances['added_and_related']), 0)
        self.assertEqual(len(node_instances['removed_and_related']), 2)
        removed_and_related = node_instances['removed_and_related']
        removed = [n for n in removed_and_related if 'modification' in n]
        related = [n for n in removed_and_related if n not in removed]
        self.assertEqual(len(removed), 1)
        self.assertEqual(len(related), 1)
        self.assertEqual(len(node_instances['extended_and_related']), 0)
        self.assertEqual(len(node_instances['reduced_and_related']), 1)
        reduced_and_related = node_instances['reduced_and_related']
        reduced = [n for n in reduced_and_related if 'modification' in n]
        self.assertEqual(len(reduced), 1)

    def test_add_relationship(self):
        blueprint = self.BASE_BLUEPRINT + self.BASE_NODES

        rel_type = 'cloudify.relationships.connected_to'
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
        modified_nodes = [with_rel, without_rel]
        node_instances = self.modify_multi(plan, modified_nodes=modified_nodes)

        self.assertEqual(len(node_instances['added_and_related']), 0)
        self.assertEqual(len(node_instances['removed_and_related']), 0)
        self.assertEqual(len(node_instances['extended_and_related']), 2)
        extended_and_related = node_instances['extended_and_related']
        extended = [n for n in extended_and_related if 'modification' in n]
        related = [n for n in extended_and_related if n not in extended]
        self.assertEqual(len(extended), 1)
        self.assertEqual(len(related), 1)
        self.assertEqual(len(node_instances['reduced_and_related']), 0)

    def test_remove_relationship(self):
        blueprint = self.BASE_BLUEPRINT + self.BASE_NODES + """
        relationships:
            -  type: cloudify.relationships.connected_to
               target: without_rel
    """

        plan = self.parse_multi(blueprint)

        nodes = copy.deepcopy(plan['nodes'])
        node_with_rel = [n for n in nodes if n['id'] == 'with_rel'][0]
        relationships = [r for r in node_with_rel['relationships']
                         if r['target_id'] != 'without_rel']
        node_with_rel['relationships'] = relationships

        node_instances = self.modify_multi(plan, modified_nodes=nodes)

        self.assertEqual(len(node_instances['added_and_related']), 0)
        self.assertEqual(len(node_instances['removed_and_related']), 0)
        self.assertEqual(len(node_instances['extended_and_related']), 0)
        self.assertEqual(len(node_instances['reduced_and_related']), 2)
        reduced_and_related = node_instances['reduced_and_related']
        reduced = [n for n in reduced_and_related if 'modification' in n]
        related = [n for n in reduced_and_related if n not in reduced]
        self.assertEqual(len(reduced), 1)
        self.assertEqual(len(related), 1)
