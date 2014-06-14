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
__author__ = 'dan'

import copy
import networkx as nx
import random

NODES = 'nodes'
NODE_INSTANCES = 'node_instances'
RELATIONSHIPS = 'relationships'
CONNECTION_TYPE = 'connection_type'
ALL_TO_ALL = 'all_to_all'
ALL_TO_ONE = 'all_to_one'


class GraphContext(object):
    def __init__(self):
        self.name_to_ids = {}

    def add_name_to_id_mapping(self, name, node_id):
        if name not in self.name_to_ids:
            self.name_to_ids[name] = set()
        self.name_to_ids[name].add(node_id)

    def get_ids_by_name(self, name):
        return self.name_to_ids.get(name, [])


def build_initial_node_graph(plan):
    graph = nx.DiGraph()
    for node in plan['nodes']:
        node_id = node['id']
        graph.add_node(node_id, node=node)
        for relationship in node.get(RELATIONSHIPS, []):
            target_id = relationship['target_id']
            graph.add_edge(node_id, target_id,
                           relationship=relationship)
    return graph


def build_multi_instance_node_graph(initial_graph):

    _verify_no_undefined_relationships(initial_graph)

    new_graph = nx.DiGraph()
    ctx = GraphContext()

    _handle_contained_in(initial_graph, new_graph, ctx)
    _handle_connected_to_and_depends_on(initial_graph, new_graph, ctx)

    return new_graph


def create_multi_instance_plan_from_multi_instance_graph(
        plan,
        multi_instance_graph):
    plan = copy.deepcopy(plan)
    nodes_instances = []
    for g_node, node_data in multi_instance_graph.nodes(data=True):
        node_instance = node_data['node']
        relationship_instances = []
        for neighbor in multi_instance_graph.neighbors(g_node):
            relationship_instance = \
                multi_instance_graph[g_node][neighbor]['relationship']
            relationship_instances.append(relationship_instance)
        node_instance[RELATIONSHIPS] = relationship_instances
        nodes_instances.append(node_instance)
    plan[NODE_INSTANCES] = nodes_instances
    return plan


def _handle_contained_in(initial_graph,
                         new_graph,
                         ctx):
    # build graph based only on connected_to relationships
    contained_graph = _build_contained_in_graph(initial_graph)

    # don't forget to include nodes in this graph than no one is contained
    # in them (these will be considered 1 node trees)
    no_containment_graph = initial_graph.copy()
    no_containment_graph.remove_nodes_from(contained_graph.nodes_iter())
    contained_graph.add_nodes_from(no_containment_graph.nodes_iter(data=True))

    # for each 'contained' tree, recursively build new tree based on
    # instances.deploy value with generated ids
    for contained_tree in nx.weakly_connected_component_subgraphs(
            contained_graph.reverse(copy=True)):
        _verify_tree(contained_tree)
        root = nx.topological_sort(contained_tree)[0]
        _build_multi_instance_node_tree_rec(root,
                                            contained_tree,
                                            new_graph,
                                            initial_graph,
                                            ctx)


def _build_multi_instance_node_tree_rec(root,
                                        contained_tree,
                                        master_graph,
                                        initial_graph,
                                        ctx,
                                        target_relationship=None,
                                        parent_id=None,
                                        current_host_id=None):
    instances_num = contained_tree.node[root]['node']['instances']['deploy']
    root_node = contained_tree.node[root]['node']
    for _ in range(instances_num):
        node_id = _instance_id(root, _generate_suffix())
        node = _node_instance_copy(root_node, node_id)

        new_current_host_id = _handle_host_id(current_host_id,
                                              root, node_id, node)

        ctx.add_name_to_id_mapping(root, node_id)
        master_graph.add_node(node_id, node=node)
        if parent_id is not None:
            relationship = _relationship_instance_copy(target_relationship,
                                                       target_id=parent_id)
            master_graph.add_edge(node_id, parent_id,
                                  relationship=relationship)
        for neighbor in contained_tree.neighbors(root):
            descendants = nx.descendants(contained_tree, neighbor)
            descendants.add(neighbor)
            sub_tree = contained_tree.subgraph(descendants)
            _build_multi_instance_node_tree_rec(
                neighbor,
                sub_tree,
                master_graph,
                initial_graph,
                ctx,
                initial_graph[neighbor][root]['relationship'],
                node_id,
                current_host_id=new_current_host_id)


def _handle_host_id(current_host_id, node_name, node_id, node):
    # If this condition applies, we assume current root is a host node
    if current_host_id is None and \
       'host_id' in node and node['host_id'] == node_name:
        current_host_id = node_id
    if current_host_id is not None:
        node['host_id'] = current_host_id
    return current_host_id


def _handle_connected_to_and_depends_on(initial_graph,
                                        new_graph,
                                        ctx):
    connected_and_depends_graph = \
        _build_connected_to_and_depends_on_graph(initial_graph)
    for node, neighbor, e_data in \
            connected_and_depends_graph.edges(data=True):
        relationship = e_data['relationship']
        connection_type = _verify_and_get_connection_type(relationship)
        for multi_instance_node in ctx.get_ids_by_name(node):
            targets = list(ctx.get_ids_by_name(neighbor))
            if connection_type == ALL_TO_ONE:
                targets = targets[:1]
            for target_node in targets:
                relationship_copy = _relationship_instance_copy(
                    relationship, target_id=target_node)
                new_graph.add_edge(multi_instance_node, target_node,
                                   relationship=relationship_copy)


def _build_connected_to_and_depends_on_graph(graph):
    return _build_graph_from_by_relationship_base(graph, ['connected',
                                                          'depends'])


def _build_contained_in_graph(graph):
    return _build_graph_from_by_relationship_base(graph, ['contained'])


def _build_graph_from_by_relationship_base(graph, bases):
    new_graph = nx.DiGraph()
    for node, neighbor, e_data in graph.edges_iter(data=True):
        if e_data['relationship']['base'] in bases:
            new_graph.add_node(node, graph.node[node])
            new_graph.add_node(neighbor, graph.node[neighbor])
            new_graph.add_edge(node, neighbor, e_data)
    return new_graph


def _instance_id(node_id, node_suffix):
    return node_id + node_suffix


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


def _relationship_instance_copy(relationship, target_id):
    return {
        'type': relationship['type'],
        'target_name': relationship['target_id'],
        'target_id': target_id
    }


def _is_valid_acyclic_plan(graph):
    return nx.is_directed_acyclic_graph(graph)


def _verify_tree(graph):
    if not _is_tree(graph):
        raise IllegalContainedInState


# currently we have decided not to support such relationships
# until we better understand what semantics are required for such
# relationships
def _verify_no_undefined_relationships(graph):
    g = _build_graph_from_by_relationship_base(graph, 'undefined')
    if len(g.nodes()) > 0:
        raise UnsupportedRelationship


def _verify_and_get_connection_type(relationship):
    if CONNECTION_TYPE not in relationship['properties'] or \
       relationship['properties'][CONNECTION_TYPE] not in [ALL_TO_ALL,
                                                           ALL_TO_ONE]:
        raise IllegalConnectedToConnectionType
    return relationship['properties'][CONNECTION_TYPE]


def _is_tree(graph):
    # we are not testing 'nx.is_weakly_connected(graph)' because we have
    # called this method after breaking the initial graph into weakly connected
    # components
    return nx.number_of_nodes(graph) == nx.number_of_edges(graph) + 1


class IllegalContainedInState(Exception):
    pass


class IllegalConnectedToConnectionType(Exception):
    pass


class UnsupportedRelationship(Exception):
    pass
