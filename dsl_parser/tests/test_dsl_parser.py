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

    def test_create_node_instances_policies(self):

        node_id = "simple_web_server.host"
        node_policies = "stub"
        policies = {
            node_id: node_policies
        }

        expected_policies = {
            "simple_web_server.host_d82c0": node_policies,
            "simple_web_server.host_c2094": node_policies
        }

        suffix_map = { 'simple_web_server.host': ['_d82c0', '_c2094']}
        actual_policies = tasks.create_node_instances_policies(node_id, policies, suffix_map)
        self.assertEqual(actual_policies, expected_policies)

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
            "multi_instance.host" : ["_d82c0"],
            "multi_instance.db" : ["_c2094"] }

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
            ],
            "policies": {
                "multi_instance.db": "stub",
                "multi_instance.host": "stub"
            }
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
            ],
            "policies": {
                "multi_instance.db_42485": "stub",
                "multi_instance.db_6baa9": "stub",
                "multi_instance.host_c2094": "stub",
                "multi_instance.host_d82c0": "stub"
            }
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
            ],
            "policies": {
                "multi_instance.db": "stub",
                "multi_instance.host": "stub"
            }
        }

        expected_plan = {
            "nodes": [
                {
                    "id": "multi_instance.db_c2094",
                    "host_id": "multi_instance.host_d82c0",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host_d82c0",
                        }
                    ],
                },
                {
                    "id": "multi_instance.host_d82c0",
                    "host_id": "multi_instance.host_d82c0",
                    "instances" : {
                        "deploy": 1
                    }
                }
            ],
            "policies": {
                "multi_instance.db_c2094": "stub",
                "multi_instance.host_d82c0": "stub"
            }
        }
    
        random.seed(0)
        new_plan = json.loads(tasks.prepare_multi_instance_plan(plan))
        self.assertEqual(new_plan, expected_plan)

    def test_prepare_single_instance_plan_with_connected_to(self):

        plan = {
            "nodes": [
                {
                    "id": "multi_instance.host1",
                    "host_id": "multi_instance.host1",
                    "instances": {
                        "deploy": 1
                    }
                },
                {
                    "id": "multi_instance.host2",
                    "host_id": "multi_instance.host2",
                    "instances": {
                        "deploy": 1
                    }
                },
                {
                    "id": "multi_instance.db",
                    "host_id": "multi_instance.host1",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host1",
                        }
                    ],
                },
                {
                    "id": "multi_instance.webserver",
                    "host_id": "multi_instance.host2",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host2",
                        },
                        {
                            "type": "cloudify.relationships.connected_to",
                            "target_id": "multi_instance.db",
                        }
                    ],
                }
            ],
            "policies": {
                "multi_instance.host1": "stub",
                "multi_instance.host2": "stub",
                "multi_instance.db": "stub",
                "multi_instance.webserver": "stub"
            }
        }

        expected_plan = {
            "nodes": [
                {
                    "id": "multi_instance.db_6baa9",
                    "host_id": "multi_instance.host1_d82c0",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host1_d82c0",
                        }
                    ],
                },
                {
                    "id": "multi_instance.host2_c2094",
                    "host_id": "multi_instance.host2_c2094",
                    "instances": {
                        "deploy": 1
                    }
                },
                {
                    "id": "multi_instance.host1_d82c0",
                    "host_id": "multi_instance.host1_d82c0",
                    "instances": {
                        "deploy": 1
                    }
                },
                {
                    "id": "multi_instance.webserver_42485",
                    "host_id": "multi_instance.host2_c2094",
                    "relationships": [
                        {
                            "type": "cloudify.relationships.contained_in",
                            "target_id": "multi_instance.host2_c2094",
                        },
                        {
                            "type": "cloudify.relationships.connected_to",
                            "target_id": "multi_instance.db_6baa9",
                        }
                    ],
                }
            ],
            "policies": {
                "multi_instance.host1_d82c0": "stub",
                "multi_instance.host2_c2094": "stub",
                "multi_instance.db_6baa9": "stub",
                "multi_instance.webserver_42485": "stub"
            }
        }

        random.seed(0)
        new_plan = json.loads(tasks.prepare_multi_instance_plan(plan))

        self.assertEqual(new_plan, expected_plan)
