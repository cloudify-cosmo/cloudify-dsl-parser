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

__author__ = 'idanmo'

import unittest

import dsl_parser.tasks as tasks
import json

class TestDSLParser(unittest.TestCase):

    def test_create_node_instances(self):

        node = {
            "id": "simple_web_server.host",
            "properties": { "x" : "y" },
            "host_id": "simple_web_server.host"
        }

        expected_instances = [
            {
                "id": "simple_web_server.host_1",
                "properties": { "x" : "y" },
                "host_id": "simple_web_server.host_1"
            },
            {
                "id": "simple_web_server.host_2",
                "properties": { "x" : "y" },
                "host_id": "simple_web_server.host_2"
            }
        ]

        instances = tasks.create_node_instances(node, 2)
        self.assertEqual(instances, expected_instances)

    def test_create_node_expansion_map(self):

        nodes = [
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host"
                },
                {
                    "id": "multi_instance.host",
                    "host_id": "multi_instance.host",
                    "instances" : {
                        "deploy": 2
                    }
                }
            ]

        expected_expansion_map = { "multi_instance.db" : 2,
                          "multi_instance.host" : 2 }

        expansion_map = tasks.create_node_expansion_map(nodes)
        self.assertEqual(expansion_map, expected_expansion_map)

    def test_prepare_multi_instance_plan(self):

        plan = {
            "nodes": [
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host"
                },
                {
                    "id": "multi_instance.host",
                    "host_id": "multi_instance.host",
                    "instances" : {
                        "deploy": 2
                    }
                }
            ]
        }

        # everything in the new plan stays the same except for nodes that belonged to a tier.
        expected_plan = {
            "nodes": [
                {
                    "id": "multi_instance.db_1",
                    "host_id": "multi_instance.host_1"
                },
                {
                    "id": "multi_instance.db_2",
                    "host_id": "multi_instance.host_2"
                },
                {
                    "id": "multi_instance.host_1",
                    "host_id": "multi_instance.host_1",
                    "instances" : {
                        "deploy": 2
                    }
                },
                {
                    "id": "multi_instance.host_2",
                    "host_id": "multi_instance.host_2",
                    "instances" : {
                        "deploy": 2
                    }
                }
            ]
        }

        new_plan = tasks.prepare_multi_instance_plan(json.dumps(plan))
        self.assertEqual(new_plan, expected_plan)
