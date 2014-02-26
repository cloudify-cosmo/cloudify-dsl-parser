__author__ = 'dan'

import copy
import networkx as nx
import random


def build_initial_node_graph(plan):
    graph = nx.DiGraph()
    for node in plan['nodes']:
        node_id = node['id']
        graph.add_node(node_id,
                       node=node)
        for relationship in node.get('relationships', []):
            target_id = relationship['target_id']
            graph.add_edge(node_id, target_id,
                           relationship=relationship)
    return graph


def build_multi_instance_node_graph(graph):
    new_graph = nx.DiGraph()
    contained_graph = _build_contained_in_graph(graph)
    for contained_tree in nx.weakly_connected_component_subgraphs(
            contained_graph.reverse(copy=True)):
        root = nx.topological_sort(contained_tree)[0]
        _build_multi_instance_node_tree_rec(root,
                                            contained_tree,
                                            new_graph,
                                            graph)
    print new_graph.nodes()
    print new_graph.edges()


def _build_multi_instance_node_tree_rec(root,
                                        contained_tree,
                                        master_graph,
                                        initial_graph,
                                        target_relationship=None,
                                        parent_id=None):
    instances_num = contained_tree.node[root]['node']['instances']['deploy']
    instances_copy = _n_copies(contained_tree.node[root], instances_num)
    for instance_copy in instances_copy:
        node_id = _instance_id(root, _generate_suffix())
        instance_copy['node']['id'] = node_id
        master_graph.add_node(node_id, instance_copy)
        if parent_id is not None:
            relationship = copy.deepcopy(target_relationship)
            relationship['target_id'] = parent_id
            master_graph.add_edge(node_id, parent_id,
                                  relationship=relationship)
        for neighbor in contained_tree.neighbors(root):
            descendants = nx.descendants(contained_tree, neighbor)
            descendants.add(neighbor)
            sub_tree = contained_tree.subgraph(descendants)
            _build_multi_instance_node_tree_rec(neighbor,
                                                sub_tree,
                                                master_graph,
                                                initial_graph,
                                                initial_graph[neighbor][root],
                                                node_id)


def _build_connected_to_graph(graph):
    return _build_graph_from_by_relationship_base(graph, 'connected')


def _build_contained_in_graph(graph):
    return _build_graph_from_by_relationship_base(graph, 'contained')


def _build_graph_from_by_relationship_base(graph, base):
    new_graph = nx.DiGraph()
    for node, neighbor, e_data in graph.edges_iter(data=True):
        if e_data['relationship']['base'] == base:
            new_graph.add_node(node, graph.node[node])
            new_graph.add_node(neighbor, graph.node[neighbor])
            new_graph.add_edge(node, neighbor, e_data)
    return new_graph


def _instance_id(node_id, node_suffix):
    return node_id + node_suffix


def _generate_suffix():
    return '_%05x' % random.randrange(16 ** 5)


def _n_copies(obj, n):
    return [copy.deepcopy(obj) for _ in range(n)]


def is_valid_acyclic_plan(graph):
    return nx.is_directed_acyclic_graph(graph)
