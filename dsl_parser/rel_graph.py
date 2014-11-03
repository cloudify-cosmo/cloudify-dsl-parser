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

import random
import copy
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
        self.node_instance_ids = set()
        if previous_deployment_node_graph is not None:
            for node_instance_id, data in \
                    previous_deployment_node_graph.nodes_iter(data=True):
                self.node_instance_ids.add(node_instance_id)
                node_instance = data['node']
                self.add_node_id_to_node_instance_id_mapping(
                    _node_id_from_node_instance(node_instance),
                    node_instance_id)

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
    ctx.node_instance_ids.clear()
    ctx.node_ids_to_node_instance_ids.clear()
    for node_instance_id, data in deployment_node_graph.nodes_iter(
            data=True):
        ctx.node_instance_ids.add(node_instance_id)
        node_id = _node_id_from_node_instance(data['node'])
        ctx.add_node_id_to_node_instance_id_mapping(node_id,
                                                    node_instance_id)
    _handle_connected_to_and_depends_on(ctx)

    return deployment_node_graph


def extract_node_instances(node_instances_graph, copy_instances=False):
    node_instances = []
    for node_instance_id, data in node_instances_graph.nodes_iter(data=True):
        node_instance = data['node']
        node_instance_attributes = data.get('node_instance_attributes')
        if copy_instances:
            node_instance = copy.deepcopy(node_instance)
        if node_instance_attributes:
            node_instance.update(node_instance_attributes)
        relationship_instances = []
        for target_node_instance_id in node_instances_graph.neighbors_iter(
                node_instance_id):
            relationship_instance = \
                node_instances_graph[node_instance_id][
                    target_node_instance_id]['relationship']
            if copy_instances:
                relationship_instance = copy.deepcopy(relationship_instance)
            relationship_instances.append(relationship_instance)
        node_instance[RELATIONSHIPS] = relationship_instances
        node_instances.append(node_instance)
    return node_instances


def extract_added_node_instances(previous_deployment_node_graph,
                                 new_deployment_node_graph):
    added_instances_graph = _graph_diff(
        new_deployment_node_graph,
        previous_deployment_node_graph,
        node_instance_attributes={'modification': 'added'})
    return extract_node_instances(added_instances_graph, copy_instances=True)


def extract_removed_node_instances(previous_deployment_node_graph,
                                   new_deployment_node_graph):
    removed_instances_graph = _graph_diff(
        previous_deployment_node_graph,
        new_deployment_node_graph,
        node_instance_attributes={'modification': 'removed'})
    return extract_node_instances(removed_instances_graph, copy_instances=True)


def _graph_diff(G, H, node_instance_attributes):
    result = nx.DiGraph()
    for n1, data in G.nodes_iter(data=True):
        if n1 in H:
            continue
        result.add_node(n1, data,
                        node_instance_attributes=node_instance_attributes)
        for n2 in G.neighbors_iter(n1):
            result.add_node(n2, G.node[n2])
            result.add_edge(n1, n2, G[n1][n2])
        for n2 in G.predecessors_iter(n1):
            result.add_node(n2, G.node[n2])
            result.add_edge(n2, n1, G[n2][n1])
    return result


def _handle_contained_in(ctx):
    # build graph based only on connected_to relationships
    contained_graph = _build_contained_in_graph(ctx.plan_node_graph)

    # don't forget to include nodes in this graph than no one is contained
    # in them (these will be considered 1 node trees)
    contained_graph.add_nodes_from(ctx.plan_node_graph.nodes_iter(data=True))

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
        for child_node_id in contained_tree.neighbors_iter(node_id):
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
    current_instances_num = _number_of_instances(node)
    new_instances_num = 0
    previous_containers = []
    if ctx.modification:
        all_previous_node_instance_ids = ctx.get_node_instance_ids_by_node_id(
            node_id)
        previous_node_instance_ids = [
            instance_id for instance_id in all_previous_node_instance_ids
            if not parent_node_instance_id or
            (instance_id in ctx.previous_deployment_node_graph and
             ctx.previous_deployment_node_graph[instance_id].get(
                 parent_node_instance_id))
        ]

        previous_instances_num = len(previous_node_instance_ids)
        if node_id in ctx.modified_nodes:
            modified_node = ctx.modified_nodes[node_id]
            total_instances_num = modified_node['instances']
            if total_instances_num > previous_instances_num:
                new_instances_num = (total_instances_num -
                                     previous_instances_num)
            else:
                # removed nodes are removed from the
                # 'previous_node_instance_ids' list which means they will
                # not be included in the resulting graph
                _handle_removed_instances(previous_node_instance_ids,
                                          previous_instances_num,
                                          total_instances_num,
                                          modified_node)
        else:
            new_instances_num = (current_instances_num -
                                 previous_instances_num)
        previous_node_instances = [
            ctx.previous_deployment_node_graph.node[node_instance_id]['node']
            for node_instance_id in previous_node_instance_ids]
        previous_containers = [Container(node_instance,
                                         _extract_contained(node,
                                                            node_instance),
                                         node_instance.get('host_id'))
                               for node_instance in previous_node_instances]
    else:
        new_instances_num = current_instances_num

    new_containers = []
    for _ in range(new_instances_num):
        node_instance_id = _node_instance_id(node_id, ctx)
        node_instance = _node_instance_copy(node, node_instance_id)
        new_current_host_instance_id = _handle_host_instance_id(
            current_host_instance_id=current_host_instance_id,
            node_id=node_id,
            node_instance_id=node_instance_id,
            node_instance=node_instance)
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


def _handle_removed_instances(
        previous_node_instance_ids,
        previous_instances_num,
        total_instances_num,
        modified_node):
    removed_instances_num = previous_instances_num - total_instances_num
    removed_ids_include_hint = modified_node.get(
        'removed_ids_include_hint', [])
    removed_ids_exclude_hint = modified_node.get(
        'removed_ids_exclude_hint', [])
    for removed_instance_id in removed_ids_include_hint:
        if removed_instances_num <= 0:
            break
        if removed_instance_id in previous_node_instance_ids:
            previous_node_instance_ids.remove(removed_instance_id)
            removed_instances_num -= 1
    for removed_instance_id in copy.copy(
            previous_node_instance_ids):
        if removed_instances_num <= 0:
            break
        if removed_instance_id in removed_ids_exclude_hint:
            continue
        previous_node_instance_ids.remove(removed_instance_id)
        removed_instances_num -= 1
    remaining_removed_instance_ids = previous_node_instance_ids[
        :removed_instances_num]
    for removed_instance_id in remaining_removed_instance_ids:
        previous_node_instance_ids.remove(removed_instance_id)


def _extract_contained(node, node_instance):
    for node_relationship in node.get('relationships', []):
        if CONTAINED_IN_REL_TYPE in node_relationship['type_hierarchy']:
            contained_node_relationship = node_relationship
            break
    else:
        return None
    for node_instance_relationship in node_instance['relationships']:
        if (node_instance_relationship['type'] ==
                contained_node_relationship['type']):
            return node_instance_relationship
    raise RuntimeError('Failed extracting contained node instance '
                       'relationships for node instance: {0}'
                       .format(node_instance['id']))


def _handle_host_instance_id(current_host_instance_id,
                             node_id,
                             node_instance_id,
                             node_instance):
    # If this condition applies, we assume current root is a host node
    if current_host_instance_id is None and \
       node_instance.get('host_id') == node_id:
        current_host_instance_id = node_instance_id
    if current_host_instance_id is not None:
        node_instance['host_id'] = current_host_instance_id
    return current_host_instance_id


def _handle_connected_to_and_depends_on(ctx):

    relationship_target_ids = {}
    if ctx.modification:
        for s, t, e_data in ctx.previous_deployment_node_graph.edges_iter(
                data=True):
            s_node = ctx.previous_deployment_node_graph.node[s]['node']
            t_node = ctx.previous_deployment_node_graph.node[t]['node']
            rel = e_data['relationship']
            key = (_node_id_from_node_instance(s_node),
                   _node_id_from_node_instance(t_node),
                   rel['type'])
            if key not in relationship_target_ids:
                relationship_target_ids[key] = set()
            target_ids = relationship_target_ids[key]
            target_ids.add(rel['target_id'])

    connected_graph = _build_connected_to_and_depends_on_graph(
        ctx.plan_node_graph)
    for source_node_id, target_node_id, edge_data in connected_graph.edges(
            data=True):
        relationship = edge_data['relationship']
        connection_type = _verify_and_get_connection_type(relationship)
        target_node_instance_ids = ctx.get_node_instance_ids_by_node_id(
            target_node_id)
        if connection_type == ALL_TO_ONE:
            if ctx.modification:
                key = (source_node_id, target_node_id, relationship['type'])
                target_ids = relationship_target_ids[key]
                if len(target_ids) != 1:
                    raise IllegalAllToOneState(
                        'Expected exactly one target id for relationship '
                        '{0}->{1} ({2})'.format(source_node_id,
                                                target_node_id,
                                                relationship['type']))
                target_node_instance_id = target_ids.copy().pop()
            else:
                target_node_instance_id = min(target_node_instance_ids)
            target_node_instance_ids = [target_node_instance_id]
        for source_node_instance_id in ctx.get_node_instance_ids_by_node_id(
                source_node_id):
            for target_node_instance_id in target_node_instance_ids:
                relationship_instance = _relationship_instance_copy(
                    relationship,
                    target_node_instance_id=target_node_instance_id)
                ctx.deployment_node_graph.add_edge(
                    source_node_instance_id, target_node_instance_id,
                    relationship=relationship_instance)


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


def _node_instance_id(node_id, ctx):
    generated_id = _generate_id()
    new_node_instance_id = '{0}_{1}'.format(node_id, generated_id)
    while new_node_instance_id in ctx.node_instance_ids:
        generated_id = _generate_id()
        new_node_instance_id = '{0}_{1}'.format(node_id, generated_id)
    return new_node_instance_id


def _generate_id():
    return '%05x' % random.randrange(16 ** 5)


def _node_instance_copy(node, node_instance_id):
    result = {
        'name': _node_id_from_node(node),
        'node_id': _node_id_from_node(node),
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
                edge['relationship'], [
                    DEPENDS_ON_REL_TYPE,
                    CONTAINED_IN_REL_TYPE,
                    CONNECTED_TO_REL_TYPE]):
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


def _node_id_from_node(node):
    return node.get('name') or node.get('id')


def _node_id_from_node_instance(instance):
    return instance.get('name') or instance.get('node_id')


def _number_of_instances(node):
    return (node.get('instances', {}).get('deploy') or
            node.get('number_of_instances'))


class IllegalConnectedToConnectionType(Exception):
    pass


class UnsupportedRelationship(Exception):
    pass


class IllegalAllToOneState(Exception):
    pass
