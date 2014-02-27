__author__ = 'dan'

import copy
import networkx as nx
import random

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


def build_multi_instance_node_graph(initial_graph):

    _verify_no_depends_relationships(initial_graph)

    new_graph = nx.DiGraph()
    ctx = GraphContext()

    connected_graph = _build_connected_to_graph(initial_graph)

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

    for node, neighbor, e_data in connected_graph.edges(data=True):
        relationship = e_data['relationship']
        connection_type = _verify_and_get_connection_type(relationship)
        print node, neighbor, relationship, connection_type

    # print new_graph.nodes()
    # print new_graph.edges()


def _build_multi_instance_node_tree_rec(root,
                                        contained_tree,
                                        master_graph,
                                        initial_graph,
                                        ctx,
                                        target_relationship=None,
                                        parent_id=None):
    instances_num = contained_tree.node[root]['node']['instances']['deploy']
    instances_copy = _n_copies(contained_tree.node[root], instances_num)
    for instance_copy in instances_copy:
        node_id = _instance_id(root, _generate_suffix())
        instance_copy['node']['id'] = node_id
        ctx.add_name_to_id_mapping(root, node_id)
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
                                                ctx,
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


def _is_valid_acyclic_plan(graph):
    return nx.is_directed_acyclic_graph(graph)


def _verify_tree(graph):
    if not _is_tree(graph):
        raise IllegalContainedInState


# currently we have decided not to support such relationships
# until we better understand what semantics are required for such
# relationships
def _verify_no_depends_relationships(graph):
    g = _build_graph_from_by_relationship_base(graph, 'depends')
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