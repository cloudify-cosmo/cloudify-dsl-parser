########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

from dsl_parser import models
from dsl_parser import rel_graph
from dsl_parser import constants


def create_deployment_plan(plan):
    """
    Expand node instances based on number of instances to deploy and
    defined relationships
    """
    plan_node_graph = rel_graph.build_node_graph(plan['nodes'])
    deployment_node_graph = rel_graph.build_deployment_node_graph(
        plan_node_graph)
    node_instances = rel_graph.extract_node_instances(
        node_instances_graph=deployment_node_graph)
    deployment_plan = copy.deepcopy(plan)
    deployment_plan[constants.NODE_INSTANCES] = node_instances
    return models.Plan(deployment_plan)


def modify_deployment(nodes, previous_node_instances, modified_nodes):
    plan_node_graph = rel_graph.build_node_graph(nodes)
    previous_deployment_node_graph = rel_graph.build_node_graph(
        previous_node_instances)
    new_deployment_node_graph = rel_graph.build_deployment_node_graph(
        plan_node_graph,
        previous_deployment_node_graph,
        modified_nodes)

    added_and_related = rel_graph.extract_added_node_instances(
        previous_deployment_node_graph, new_deployment_node_graph)
    removed_and_related = rel_graph.extract_removed_node_instances(
        previous_deployment_node_graph, new_deployment_node_graph)

    return {
        'added_and_related': added_and_related,
        'removed_and_related': removed_and_related
    }
