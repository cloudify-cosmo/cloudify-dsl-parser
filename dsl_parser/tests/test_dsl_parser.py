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
import random
import json

class TestDSLParser(unittest.TestCase):

    maxDiff = None

    def test_create_node_instances(self):

        node = {
            "id": "simple_web_server.host",
            "properties": { "x" : "y" },
            "host_id": "simple_web_server.host"
        }

        expected_instances = [
            {
                "id": "simple_web_server.host_d82c0",
                "properties": { "x" : "y" },
                "host_id": "simple_web_server.host_d82c0"
            },
            {
                "id": "simple_web_server.host_c2094",
                "properties": { "x" : "y" },
                "host_id": "simple_web_server.host_c2094"
            }
        ]

        suffix_map = { 'simple_web_server.host': ['_d82c0', '_c2094']}
        instances = tasks.create_node_instances(node, suffix_map)
        self.assertEqual(instances, expected_instances)

    def test_create_multiple_node_suffix_map(self):

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

        expected_suffix_map = {
            "multi_instance.host" : ["_d82c0","_c2094"],
            "multi_instance.db" : ["_6baa9", "_42485"] }

        random.seed(0)
        suffix_map = tasks.create_node_suffixes_map(nodes)
        self.assertEqual(suffix_map, expected_suffix_map)

    def test_create_single_node_suffix_map(self):

        nodes = [
            {
                "id": "multi_instance.db",
                "host_id": "multi_instance.host"
            },
            {
                "id": "multi_instance.host",
                "host_id": "multi_instance.host",
                "instances" : {
                    "deploy": 1
                }
            }
        ]

        expected_suffix_map = {
            "multi_instance.host" : [""],
            "multi_instance.db" : [""] }

        random.seed(0)
        suffix_map = tasks.create_node_suffixes_map(nodes)
        self.assertEqual(suffix_map, expected_suffix_map)

    def test_prepare_multi_instance_plan(self):

        plan = {
            "nodes": [
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host",
                        }
                    ],
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
                    "id": "multi_instance.db_6baa9",
                    "host_id": "multi_instance.host_d82c0",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host_d82c0",
                        }
                    ],
                },
                {
                    "id": "multi_instance.db_42485",
                    "host_id": "multi_instance.host_c2094",
                    "relationships": [
                        {
                        "type": "cloudify.relationships.contained_in",
                        "target_id": "multi_instance.host_c2094",
                        }
                    ],
                },
                {
                    "id": "multi_instance.host_d82c0",
                    "host_id": "multi_instance.host_d82c0",
                    "instances" : {
                        "deploy": 2
                    }
                },
                {
                    "id": "multi_instance.host_c2094",
                    "host_id": "multi_instance.host_c2094",
                    "instances" : {
                        "deploy": 2
                    }
                }
            ]
        }

        random.seed(0)
        new_plan = json.loads(tasks.prepare_multi_instance_plan(plan))
        self.assertEqual(new_plan, expected_plan)

    def test_prepare_single_instance_plan(self):

        plan = {
            "nodes": [
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host",
                        }
                    ],
                    },
                {
                    "id": "multi_instance.host",
                    "host_id": "multi_instance.host",
                    "instances" : {
                        "deploy": 1
                    }
                }
            ]
        }

        # everything in the new plan stays the same for backwards compatibility
        expected_plan = {
            "nodes": [
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host",
                        }
                    ],
                },
                {
                    "id": "multi_instance.host",
                    "host_id": "multi_instance.host",
                    "instances" : {
                        "deploy": 1
                    }
                }
            ]
        }
    
        random.seed(0)
        new_plan = json.loads(tasks.prepare_multi_instance_plan(plan))
        self.assertEqual(new_plan, expected_plan)        