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

import logging
from celery.utils.log import get_task_logger
from celery import task

__author__ = 'idanmo'

import json
import random
import parser

NODES = "nodes"
POLICIES = "policies"

logger = get_task_logger(__name__)
logger.level = logging.DEBUG


@task
def prepare_multi_instance_plan(plan, **kwargs):
    """
    Expand node instances based on number of instances to deploy
    """
    modify_to_multi_instance_plan(plan)
    return json.dumps(plan)


@task
def parse_dsl(dsl_location, alias_mapping_url, resources_base_url, **kwargs):
    result = parser.parse_from_url(dsl_url=dsl_location, alias_mapping_url=alias_mapping_url,
                                   resources_base_url=resources_base_url)
    return json.dumps(result)


def modify_to_multi_instance_plan(plan):
    nodes = plan[NODES]
    policies = plan[POLICIES]

    new_nodes = []
    new_policies = {}

    nodes_suffixes_map = create_node_suffixes_map(nodes)
    node_ids = create_node_suffixes_map(nodes).iterkeys()

    for node_id in node_ids:
        node = get_node(node_id, nodes)
        instances = _create_node_instances(node, nodes_suffixes_map)
        new_nodes.extend(instances)
        instances_policies = _create_node_instances_policies(node_id,
                                                             policies,
                                                             nodes_suffixes_map)
        new_policies.update(instances_policies)

    plan[NODES] = new_nodes
    plan[POLICIES] = new_policies


def create_node_suffixes_map(nodes):
    """
    This method inspects the current nodes and creates a list of random suffixes.
    That is, for every node, it determines how many instances are needed
    and generates a random number (later used as id suffix) for each instance.
    """

    suffix_map = {}
    for node in nodes:
        if is_host(node):
            number_of_hosts = node["instances"]["deploy"]
            suffix_map[node["id"]] = _generate_unique_ids(number_of_hosts)

    for node in nodes:
        if not is_host(node):
            if is_hosted(node):
                host_id = node["host_id"]
                number_of_hosts = len(suffix_map[host_id])
                suffix_map[node["id"]] = _generate_unique_ids(number_of_hosts)
            else:
                suffix_map[node["id"]] = [node["id"]]
    return suffix_map


def is_host(node):
    return is_hosted(node) and node["host_id"] == node["id"]


def is_hosted(node):
    return 'host_id' in node


def get_node(node_id, nodes):
    """
    Retrieves a node from the nodes list based on the node id.
    """
    for node in nodes:
        if node_id == node['id']:
            return node
    raise RuntimeError("Could not find a node with id {0} in nodes".format(node_id))


def _create_node_instances(node, suffixes_map):
    """
    This method duplicates the given node 'number_of_instances' times and return an array with the duplicated instance.
    Each instance has a different id and each instance has a different host_id.
    id's are generated with an random index suffixed to the original id.
    For example: app.host --> [app.host_ab54ef, app.host_2_12345] in case of 2 instances.
    """

    instances = []

    node_id = node['id']
    node_suffixes = suffixes_map[node_id]
    host_id = node['host_id']
    host_suffixes = suffixes_map[host_id]
    number_of_instances = len(node_suffixes)

    for i in range(number_of_instances):
        node_copy = node.copy()
        node_copy['id'] = _build_node_instance_id(node_id, node_suffixes[i])
        node_copy['host_id'] = _build_node_instance_id(host_id, host_suffixes[i])
        logger.debug("generated new node instance {0}".format(node_copy))
        if 'relationships' in node_copy:
            new_relationships = []
            for relationship in node_copy['relationships']:
                new_relationship = relationship
                target_id = relationship['target_id']
                if relationship['type'].endswith('relationships.contained_in'):
                    new_relationship = relationship.copy()
                    new_relationship['target_id'] = _build_node_instance_id(target_id, suffixes_map[target_id][i])
                elif (relationship['type'].endswith('relationships.connected_to') or
                          relationship['type'].endswith('relationships.depends_on')):
                    new_relationship = relationship.copy()
                    # TODO support connected_to with tiers
                    # currently only 1 instance for connected_to (and depends_on) is supported
                    new_relationship['target_id'] = _build_node_instance_id(target_id, suffixes_map[target_id][0])
                new_relationships.append(new_relationship)
            node_copy['relationships'] = new_relationships

        instances.append(node_copy)

    return instances


def _create_node_instances_policies(node_id, policies, node_suffixes_map):
    """
    This method duplicates the policies for each node_id. and returns a map. let us use an example:
    Given:
    node_id -> { ... node policies ... }
    Returns:
    {
        node_id_suffix1 -> { ... node policies ... },
        node_id_suffix2 -> { ... node policies ... (same as above) }
        ...
    }
    """

    if not node_id in policies:
        return {}

    node_suffixes = node_suffixes_map[node_id]
    node_policies = policies[node_id]
    node_instances_policies = {}
    number_of_instances = len(node_suffixes)
    for i in range(number_of_instances):
        the_id = _build_node_instance_id(node_id, node_suffixes[i])
        node_instances_policies[the_id] = node_policies
    return node_instances_policies


def _build_node_instance_id(node_id, node_suffix):
    return node_id + node_suffix


def _generate_unique_ids(number_of_ids):
    ids = []
    while len(ids) < number_of_ids:
        rand_id = '_%05x' % random.randrange(16 ** 5)
        if rand_id not in ids:
            ids.append(rand_id)

    return list(ids)
