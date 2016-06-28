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

from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestAnchors(AbstractTestParser):

    @staticmethod
    def _get_node_properties(plan, id):
        return next((node['properties'] for node in plan['nodes']
                     if node['id'] == id))

    def test_anchors_append(self):
        bp_yaml = """
node_types:
    my_type:
        properties:
            prop1:
                default: 0
            prop2:
                default: 0

node_templates:
    node1:
        type: my_type
        properties: &props1
            prop1: 1
    node2:
        type: my_type
        properties:
            <<: *props1
            prop2: 2
    node3:
        type: my_type
        properties:
            <<: *props1
            prop2: 3
"""
        parsed_plan = self.parse(bp_yaml)

        expected_node_properties = {
            'node1': {'prop1': 1, 'prop2': 0},
            'node2': {'prop1': 1, 'prop2': 2},
            'node3': {'prop1': 1, 'prop2': 3}
        }

        for node, expected_value in expected_node_properties.iteritems():
            self.assertEquals(expected_value,
                              self._get_node_properties(parsed_plan, node))

    def test_anchors_override(self):
        bp_yaml = """
node_types:
    my_type:
        properties:
            prop1:
                default: 0
            prop2:
                default: 0

node_templates:
    node1:
        type: my_type
        properties: &props1
            prop1: 1
            prop2: 1
    node2:
        type: my_type
        properties: &props2
            <<: *props1
            prop2: 2
    node3:
        type: my_type
        properties:
            <<: *props2
            prop2: 3
"""
        parsed_plan = self.parse(bp_yaml)

        expected_node_properties = {
            'node1': {'prop1': 1, 'prop2': 1},
            'node2': {'prop1': 1, 'prop2': 2},
            'node3': {'prop1': 1, 'prop2': 3}
        }

        for node_id, expected_value in expected_node_properties.iteritems():
            self.assertEquals(expected_value,
                              self._get_node_properties(parsed_plan, node_id))
