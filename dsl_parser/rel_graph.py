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
import random
from collections import namedtuple

import networkx as nx

from dsl_parser import parser

NODES = 'nodes'
RELATIONSHIPS = 'relationships'
DEPENDS_ON_REL_TYPE = parser.DEPENDS_ON_REL_TYPE
CONNECTED_TO_REL_TYPE = parser.CONNECTED_TO_REL_TYPE
CONTAINED_IN_REL_TYPE = parser.CONTAINED_IN_REL_TYPE
CONNECTION_TYPE = 'connection_type'
ALL_TO_ALL = 'all_to_all'
ALL_TO_ONE = 'all_to_one'


class GraphContext(object):

    def __init__(self,
                 plan_node_graph,
                 deployment_node_graph,
                 previous_deployment_node_graph=None,
                 modified_nodes=None):
        self.plan_node_graph = plan_node_graph
        self.deployment_node_graph = deployment_node_graph
        self.previous_deployment_node_graph = previous_deployment_node_graph
        self.modified_nodes = modified_nodes
        self.node_ids_to_node_instance_ids = {}
        if previous_deployment_node_graph is not None:
            for node_instance_id, data in \
                    previous_deployment_node_graph.nodes_iter(data=True):
                node_instance = data['node']
                self.add_node_id_to_node_instance_id_mapping(
                    node_instance['name'], node_instance_id)

    @property
    def modification(self):
        return self.previous_deployment_node_graph is not None

    def add_node_id_to_node_instance_id_mapping(
            self, node_id, node_instance_id):
        if node_id not in self.node_ids_to_node_instance_ids:
            self.node_ids_to_node_instance_ids[node_id] = set()
        self.node_ids_to_node_instance_ids[node_id].add(node_instance_id)

    def get_node_instance_ids_by_node_id(self, node_id):
        return self.node_ids_to_node_instance_ids.get(node_id, set())

Container = namedtuple('Container', 'node_instance '
                                    'relationship_instance '
                                    'current_host_instance_id')


def build_node_graph(nodes):
    graph = nx.DiGraph()
    for node in nodes:
        node_id = node['id']
        graph.add_node(node_id, node=node)
        for relationship in node.get(RELATIONSHIPS, []):
            target_id = relationship['target_id']
            graph.add_edge(node_id, target_id,
                           relationship=relationship)
    return graph


def build_deployment_node_graph(plan_node_graph,
                                previous_deployment_node_graph=None,
                                modified_nodes=None):

    _verify_no_unsupported_relationships(plan_node_graph)

    deployment_node_graph = nx.DiGraph()
    ctx = GraphContext(
        plan_node_graph=plan_node_graph,
        deployment_node_graph=deployment_node_graph,
        previous_deployment_node_graph=previous_deployment_node_graph,
        modified_nodes=modified_nodes)

    _handle_contained_in(ctx)
    _handle_connected_to_and_depends_on(ctx)

    return deployment_node_graph


def extract_node_instances_from_deployment_node_graph(
        deployment_node_graph):
    nodes_instances = []
    for g_node, node_data in deployment_node_graph.nodes(data=True):
        node_instance = node_data['node']
        relationship_instances = []
        for neighbor in deployment_node_graph.neighbors(g_node):
            relationship_instance = \
                deployment_node_graph[g_node][neighbor]['relationship']
            relationship_instances.append(relationship_instance)
        node_instance[RELATIONSHIPS] = relationship_instances
        nodes_instances.append(node_instance)
    return nodes_instances


def _handle_contained_in(ctx):
    # build graph based only on connected_to relationships
    contained_graph = _build_contained_in_graph(ctx.plan_node_graph)

    # don't forget to include nodes in this graph than no one is contained
    # in them (these will be considered 1 node trees)
    no_containment_graph = ctx.plan_node_graph.copy()
    no_containment_graph.remove_nodes_from(contained_graph.nodes_iter())
    contained_graph.add_nodes_from(no_containment_graph.nodes_iter(data=True))

    # for each 'contained' tree, recursively build new tree based on
    # instances.deploy value with generated ids
    for contained_tree in nx.weakly_connected_component_subgraphs(
            contained_graph.reverse(copy=True)):
        # extract tree root node id
        node_id = nx.topological_sort(contained_tree)[0]
        _build_multi_instance_node_tree_rec(
            node_id=node_id,
            contained_tree=contained_tree,
            ctx=ctx)


def _build_multi_instance_node_tree_rec(node_id,
                                        contained_tree,
                                        ctx,
                                        parent_relationship=None,
                                        parent_node_instance_id=None,
                                        current_host_instance_id=None):
    node = contained_tree.node[node_id]['node']
    containers = _build_and_update_node_instances(
        ctx=ctx,
        node=node,
        parent_node_instance_id=parent_node_instance_id,
        parent_relationship=parent_relationship,
        current_host_instance_id=current_host_instance_id)
    for container in containers:
        node_instance = container.node_instance
        node_instance_id = node_instance['id']
        relationship_instance = container.relationship_instance
        new_current_host_instance_id = container.current_host_instance_id
        ctx.deployment_node_graph.add_node(node_instance_id,
                                           node=node_instance)
        if parent_node_instance_id is not None:
            ctx.deployment_node_graph.add_edge(
                node_instance_id, parent_node_instance_id,
                relationship=relationship_instance)
        for child_node_id in contained_tree.neighbors(node_id):
            descendants = nx.descendants(contained_tree, child_node_id)
            descendants.add(child_node_id)
            child_contained_tree = contained_tree.subgraph(descendants)
            _build_multi_instance_node_tree_rec(
                node_id=child_node_id,
                contained_tree=child_contained_tree,
                ctx=ctx,
                parent_relationship=ctx.plan_node_graph[
                    child_node_id][node_id]['relationship'],
                parent_node_instance_id=node_instance_id,
                current_host_instance_id=new_current_host_instance_id)


def _build_and_update_node_instances(ctx,
                                     node,
                                     parent_node_instance_id,
                                     parent_relationship,
                                     current_host_instance_id):
    node_id = node['id']
    new_instances_num = 0
    previous_containers = []
    if ctx.modification:
        previous_node_instances = ctx.get_node_instance_ids_by_node_id(node_id)
        previous_instances_num = len(previous_node_instances)
        if node_id in ctx.modified_nodes:
            total_instances_num = ctx.modified_nodes[node_id]['instances']
            if total_instances_num > previous_instances_num:
                new_instances_num = (total_instances_num -
                                     previous_instances_num)
            else:
                removed_instances_num = (previous_instances_num -
                                         total_instances_num)
                removed_instance_ids = previous_instances_num[
                    :removed_instances_num]
                for removed_instance_id in removed_instance_ids:
                    ctx.previous_deployment_node_graph.remove_node(
                        removed_instance_id)
                    previous_node_instances.remove(removed_instance_id)
        previous_containers = [Container(node_instance,
                                         _extract_contained(node_instance),
                                         node_instance.get('host_id'))
                               for node_instance in previous_node_instances]
    else:
        new_instances_num = node['instances']['deploy']

    new_containers = []
    for _ in range(new_instances_num):
        node_instance_id = _node_instance_id(node_id)
        node_instance = _node_instance_copy(node, node_instance_id)
        new_current_host_instance_id = _handle_host_instance_id(
            current_host_instance_id=current_host_instance_id,
            node_id=node_id,
            node_instance_id=node_instance_id,
            node_instance=node_instance)
        ctx.add_node_id_to_node_instance_id_mapping(node_id, node_instance_id)
        if parent_node_instance_id is not None:
            relationship_instance = _relationship_instance_copy(
                parent_relationship,
                target_node_instance_id=parent_node_instance_id)
        else:
            relationship_instance = None
        new_containers.append(Container(node_instance,
                                        relationship_instance,
                                        new_current_host_instance_id))
    return previous_containers + new_containers


def _extract_contained(node_instance):
    for relationship in node_instance['relationships']:
        if CONTAINED_IN_REL_TYPE in relationship['type_hierarchy']:
            return relationship
    return None


def _extract_relationship(node_instance, target_instance_id):
    for relationship in node_instance['relationships']:
        if relationship['target_id'] == target_instance_id:
            return relationship
    raise ValueError('No relationship for {0} has target_id {1}'
                     .format(node_instance['id'], target_instance_id))


def _handle_host_instance_id(current_host_instance_id,
                             node_id,
                             node_instance_id,
                             node_instance):
    # If this condition applies, we assume current root is a host node
    if current_host_instance_id is None and \
       'host_id' in node_instance and node_instance['host_id'] == node_id:
        current_host_instance_id = node_instance_id
    if current_host_instance_id is not None:
        node_instance['host_id'] = current_host_instance_id
    return current_host_instance_id


def _handle_connected_to_and_depends_on(ctx):
    connected_graph = _build_connected_to_and_depends_on_graph(
        ctx.plan_node_graph)
    for source_node_id, target_node_id, edge_data in connected_graph.edges(
            data=True):
        relationship = edge_data['relationship']
        connection_type = _verify_and_get_connection_type(relationship)
        for source_node_instance_id in ctx.get_node_instance_ids_by_node_id(
                source_node_id):
            target_node_instance_ids = list(
                ctx.get_node_instance_ids_by_node_id(target_node_id))
            if connection_type == ALL_TO_ONE:
                target_node_instance_ids = target_node_instance_ids[:1]
            for target_node_instance_id in target_node_instance_ids:
                relationship_instance = _get_instance_relationship(
                    ctx=ctx,
                    source_node_instance_id=source_node_instance_id,
                    target_node_instance_id=target_node_instance_id,
                    relationship=relationship)
                ctx.deployment_node_graph.add_edge(
                    source_node_instance_id, target_node_instance_id,
                    relationship=relationship_instance)


def _get_instance_relationship(ctx,
                               source_node_instance_id,
                               target_node_instance_id,
                               relationship):
    if (ctx.modification and
        source_node_instance_id in
            ctx.previous_deployment_node_graph.node and
        target_node_instance_id in
            ctx.previous_deployment_node_graph.node):
        return copy.deepcopy(ctx.plan_node_graph[
            source_node_instance_id][target_node_instance_id]['relationship'])
    else:
        return _relationship_instance_copy(
            relationship,
            target_node_instance_id=target_node_instance_id)


def _build_connected_to_and_depends_on_graph(graph):
    return _build_graph_by_relationship_types(
        graph,
        build_from_types=[CONNECTED_TO_REL_TYPE, DEPENDS_ON_REL_TYPE],
        # because contained_in derived from depends_on
        exclude_types=[CONTAINED_IN_REL_TYPE])


def _build_contained_in_graph(graph):
    return _build_graph_by_relationship_types(
        graph,
        build_from_types=[CONTAINED_IN_REL_TYPE],
        exclude_types=[])


def _build_graph_by_relationship_types(graph,
                                       build_from_types,
                                       exclude_types):
    relationship_base_graph = nx.DiGraph()
    for source, target, edge_data in graph.edges_iter(data=True):
        include_edge = (
            _relationship_type_hierarchy_includes_one_of(
                edge_data['relationship'], build_from_types) and not
            _relationship_type_hierarchy_includes_one_of(
                edge_data['relationship'], exclude_types))
        if include_edge:
            relationship_base_graph.add_node(source, graph.node[source])
            relationship_base_graph.add_node(target, graph.node[target])
            relationship_base_graph.add_edge(source, target, edge_data)
    return relationship_base_graph


def _node_instance_id(node_id):
    return node_id + _generate_suffix()


def _generate_suffix():
    return '_%05x' % random.randrange(16 ** 5)


def _node_instance_copy(node, node_instance_id):
    result = {
        'name': node['name'],
        'id': node_instance_id
    }
    if 'host_id' in node:
        result['host_id'] = node['host_id']
    return result


def _relationship_instance_copy(relationship,
                                target_node_instance_id):
    return {
        'type': relationship['type'],
        'target_name': relationship['target_id'],
        'target_id': target_node_instance_id
    }


# currently we have decided not to support such relationships
# until we better understand what semantics are required for such
# relationships
def _verify_no_unsupported_relationships(graph):
    for s, t, edge in graph.edges_iter(data=True):
        if not _relationship_type_hierarchy_includes_one_of(
                edge['relationship'], [DEPENDS_ON_REL_TYPE]):
            raise UnsupportedRelationship()


def _verify_and_get_connection_type(relationship):
    if CONNECTION_TYPE not in relationship['properties'] or \
       relationship['properties'][CONNECTION_TYPE] not in [ALL_TO_ALL,
                                                           ALL_TO_ONE]:
        raise IllegalConnectedToConnectionType()
    return relationship['properties'][CONNECTION_TYPE]


def _relationship_type_hierarchy_includes_one_of(relationship, expected_types):
    relationship_type_hierarchy = relationship['type_hierarchy']
    return any([relationship_type in expected_types
                for relationship_type in relationship_type_hierarchy])


class IllegalContainedInState(Exception):
    pass


class IllegalConnectedToConnectionType(Exception):
    pass


class UnsupportedRelationship(Exception):
    pass
