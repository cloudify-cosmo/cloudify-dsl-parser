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

NODES = "nodes"

logger = get_task_logger(__name__)
logger.level = logging.DEBUG

@task
def prepare_multi_instance_plan(nodes_plan_json, **kwargs):

    """
    JSON should include "nodes" and "nodes_extra".
    """
    plan = json.loads(nodes_plan_json)

    new_nodes = create_multi_instance_nodes(plan[NODES])
    plan[NODES] = new_nodes

    return plan


def create_multi_instance_nodes(nodes):

    new_nodes = []

    nodes_suffixes_map = create_node_suffixes_map(nodes)
    node_ids = create_node_suffixes_map(nodes).iterkeys()

    for node_id in node_ids:
        node = get_node(node_id, nodes)
        instances = create_node_instances(node, nodes_suffixes_map)
        new_nodes.extend(instances)

    return new_nodes


def create_node_suffixes_map(nodes):
    """
    This method insepcts the current nodes and creates a list of random suffixes.
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
            host_id = node["host_id"]
            number_of_hosts = len (suffix_map[host_id])
            suffix_map[node["id"]] = _generate_unique_ids(number_of_hosts)

    return suffix_map

def is_host(node):
    return node["host_id"] == node["id"]

def get_node(node_id, nodes):

    """
    Retrieves a node from the nodes list based on the node id.
    """
    for node in nodes:
        if node_id == node['id']:
            return node
    raise RuntimeError("Could not find a node with id {0} in nodes".format(node_id))


def create_node_instances(node, suffixes_map):

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
        node_copy['id'] = node_id + '_' + node_suffixes[i]
        node_copy['host_id'] = host_id + '_' + host_suffixes[i]
        logger.debug("generated new node instance {0}".format(node_copy))

        instances.append(node_copy)

    return instances

def _generate_unique_ids(number_of_ids):
    ids = set([])
    while (len(ids) < number_of_ids):
        id = '%05x' % random.randrange(16**5)
        if (id not in ids):
            ids.add(id)

    return list(ids)
