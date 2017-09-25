########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy

import networkx as nx
import yaml

from dsl_parser import constants
from dsl_parser import rel_graph
from dsl_parser.tests import scaling


class TestMultiInstanceGroups(scaling.BaseTestMultiInstance):
    """
    It appears I am unable writing coherent code. To compensate that,
    test util methods included in this class are documented in hope that
    the negative feelings you acquire while reading this file are somewhat
    reduced.
    """

    # the following tests, test multi instances during deployment creation

    def test_group_with_single_node(self):
        return self._test(
            groups={
                'group': {
                    'instances': 2,
                    'members': ['host']
                }
            },
            nodes={
                'host': {'type': 'Compute'}
            },
            expected_instances={
                'host': 2
            },
            expected_groups={
                'group': {
                    'instances': 2,
                    'members': {
                        'host': 1
                    }
                }
            }
        )

    def test_group_with_two_nodes(self):
        return self._test(
            groups={
                'group': {
                    'instances': 2,
                    'members': ['host1', 'host2']
                }
            },
            nodes={
                'host1': {'type': 'Compute'},
                'host2': {'type': 'Compute'},
            },
            expected_instances={
                'host1': 2,
                'host2': 2
            },
            expected_groups={
                'group': {
                    'instances': 2,
                    'members': {
                        'host1': 1,
                        'host2': 1
                    }
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it1(self):
        return self._test(
            groups={
                'group': {
                    'instances': 2,
                    'members': ['host']
                }
            },
            nodes={
                'host': {'type': 'Compute'},
                'db': {'type': 'Root',
                       'contained_in': 'host'},
            },
            expected_instances={
                'host': 2,
                'db': 2
            },
            expected_groups={
                'group': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'db': 1
                    }
                }
            },
            expected_relationships={
                'db': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['group']
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it2(self):
        return self._test(
            groups={
                'host_group': {
                    'instances': 2,
                    'members': ['host']
                },
                'db_group': {
                    'members': ['db']
                }
            },
            nodes={
                'host': {'type': 'Compute'},
                'db': {'type': 'Root',
                       'contained_in': 'host'},
            },
            expected_instances={
                'host': 2,
                'db': 2
            },
            expected_groups={
                'host_group': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'db': 1
                    }
                },
                'db_group': {
                    'instances': 2,
                    'members': {
                        'db': 1
                    }
                }
            },
            expected_relationships={
                'db': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host_group']
                }
            }
        )

    def test_group_with_host_and_ip(self):
        return self._test(
            groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': ['host', 'ip']
                }
            },
            nodes={
                'host': {'type': 'Compute',
                         'connected_to': ['ip']},
                'ip': {'type': 'Root'},
            },
            expected_instances={
                'host': 2,
                'ip': 2
            },
            expected_groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'ip': 1
                    }
                }
            },
            expected_relationships={
                'host': {
                    'target': 'ip',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_ip_and_volume(self):
        return self._test(
            groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': ['host', 'ip', 'volume']
                }
            },
            nodes={
                'host': {'type': 'Compute',
                         'connected_to': ['ip']},
                'ip': {'type': 'Root'},
                'volume': {'type': 'Root',
                           'connected_to': ['host'],
                           'instances': 2}
            },
            expected_instances={
                'host': 2,
                'ip': 2,
                'volume': 4
            },
            expected_groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 2
                    }
                }
            },
            expected_relationships={
                'host': {
                    'target': 'ip',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume(self):
        return self._test(
            groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': ['host', 'ip', 'volume']
                }
            },
            nodes={
                'host': {'type': 'Compute',
                         'connected_to': ['ip']},
                'db': {'type': 'Root',
                       'contained_in': 'host'},
                'ip': {'type': 'Root'},
                'volume': {'type': 'Root',
                           'connected_to': ['host'],
                           'instances': 2}
            },
            expected_instances={
                'host': 2,
                'db': 2,
                'ip': 2,
                'volume': 4
            },
            expected_groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'db': 1,
                        'ip': 1,
                        'volume': 2
                    }
                }
            },
            expected_relationships={
                'host': {
                    'target': 'ip',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2(self):
        return self._test(
            groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': ['host', 'ip', 'volume_scale_group']
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': ['volume']
                }
            },
            nodes={
                'host': {'type': 'Compute',
                         'connected_to': ['ip']},
                'db': {'type': 'Root',
                       'contained_in': 'host',
                       'connected_to': ['volume'],
                       'instances': 3},
                'ip': {'type': 'Root'},
                'volume': {'type': 'Root',
                           'connected_to': ['host']}
            },
            expected_instances={
                'host': 2,
                'db': 6,
                'ip': 2,
                'volume': 10
            },
            expected_groups={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'db': 3,
                        'ip': 1,
                        'volume': 5
                    }
                },
                'volume_scale_group': {
                    'instances': 10,
                    'members': {
                        'volume': 1
                    }
                }
            },
            expected_relationships={
                'host': {
                    'target': 'ip',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': [
                    {'target': 'host',
                     'count': 2,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources']},
                    {'target': 'volume',
                     'count': 2,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources']},
                ],
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container(self):  # noqa
        return self._test(
            groups={
                'container': {
                    'members': ['vm_with_resources']
                },
                'vm_with_resources': {
                    'instances': 2,
                    'members': ['host', 'ip', 'volume_scale_group']
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': ['volume', 'volume_c']
                }
            },
            nodes={
                'host': {'type': 'Compute',
                         'connected_to': ['ip']},
                'db': {'type': 'Root',
                       'contained_in': 'host',
                       'connected_to': ['volume'],
                       'instances': 3},
                'ip': {'type': 'Root'},
                'volume': {'type': 'Root',
                           'connected_to': ['host']},
                'volume_c': {'type': 'Root',
                             'connected_to': ['volume']}
            },
            expected_instances={
                'host': 2,
                'db': 6,
                'ip': 2,
                'volume': 10,
                'volume_c': 10
            },
            expected_groups={
                'container': {
                    'instances': 1,
                    'members': {
                        'host': 2,
                        'db': 6,
                        'ip': 2,
                        'volume': 10,
                        'volume_c': 10
                    }
                },
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'db': 3,
                        'ip': 1,
                        'volume': 5,
                        'volume_c': 5
                    }
                },
                'volume_scale_group': {
                    'instances': 10,
                    'members': {
                        'volume': 1,
                        'volume_c': 1
                    }
                }
            },
            expected_relationships={
                'host': {
                    'target': 'ip',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'db': [
                    {'target': 'host',
                     'count': 2,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources', 'container']},
                    {'target': 'volume',
                     'count': 2,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources', 'container']}
                ],
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume_c': {
                    'target': 'volume',
                    'count': 10,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['volume_scale_group',
                               'vm_with_resources',
                               'container']
                }
            }
        )

    def test_group_with_some_random_connections(self):
        return self._test(
            groups={
                'group1': {
                    'instances': 2,
                    'members': ['group2', 'group3', 'host2']
                },
                'group2': {
                    'instances': 2,
                    'members': ['host1']
                },
                'group3': {
                    'instances': 2,
                    'members': ['db', 'db_c']
                }
            },
            nodes={
                'host1': {'type': 'Compute',
                          'instances': 2},
                'host2': {'type': 'Compute',
                          'instances': 2},
                'db': {'type': 'Root',
                       'contained_in': 'host1',
                       'instances': 2},
                'db_c': {'type': 'Root',
                         'contained_in': 'host1',
                         'connected_to': ['db'],
                         'instances': 2},
            },
            expected_instances={
                'host1': 8,
                'host2': 4,
                'db': 32,
                'db_c': 32
            },
            expected_groups={
                'group1': {
                    'instances': 2,
                    'members': {
                        'host1': 4,
                        'host2': 2,
                        'db': 16,
                        'db_c': 16
                    }
                },
                'group2': {
                    'instances': 4,
                    'members': {
                        'host1': 2,
                        'db': 8,
                        'db_c': 8
                    }
                },
                'group3': {
                    'instances': 16,
                    'members': {
                        'db': 2,
                        'db_c': 2
                    }
                }
            },
            expected_relationships={
                'db': {
                    'target': 'host1',
                    'count': 8,
                    'source_count': 4,
                    'target_count': 1,
                    'groups': ['group1', 'group2']
                },
                'db_c': [
                    {'target': 'host1',
                     'count': 8,
                     'source_count': 4,
                     'target_count': 1,
                     'groups': ['group1', 'group2']},
                    {'target': 'db',
                     'count': 16,
                     'source_count': 2,
                     'target_count': 2,
                     'groups': ['group1', 'group2', 'group3']}
                ]
            }
        )

    def test_group_with_external_nodes_not_in_any_group1(self):
        return self._test(
            groups={
                'host1_group': {
                    'instances': 2,
                    'members': ['host1', 'volume']
                }
            },
            nodes={
                'host1': {'type': 'Compute'},
                'host2': {'type': 'Compute'},
                'db': {'type': 'Root',
                       'contained_in': 'host1'},
                'webserver': {'type': 'Root',
                              'contained_in': 'host2',
                              'connected_to': ['db']},
                'volume': {'type': 'Root',
                           'connected_to': ['host1']}
            },
            expected_instances={
                'host1': 2,
                'host2': 1,
                'db': 2,
                'webserver': 1,
                'volume': 2
            },
            expected_groups={
                'host1_group': {
                    'instances': 2,
                    'members': {
                        'host1': 1,
                        'volume': 1,
                        'db': 1
                    }
                }
            },
            expected_relationships={
                'db': {
                    'target': 'host1',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host1_group']
                },
                'webserver': [
                    {'target': 'host2',
                     'count': 1,
                     'source_count': 1,
                     'target_count': 1,
                     'groups': []},
                    {'target': 'db',
                     'count': 1,
                     'source_count': 1,
                     'target_count': 2,
                     'groups': []}
                ],
                'volume': {
                    'target': 'host1',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host1_group']
                }
            },
        )

    def test_group_with_external_nodes_not_in_any_group2(self):
        return self._test(
            groups={
                'host1_group': {
                    'instances': 2,
                    'members': ['host1', 'volume']
                }
            },
            nodes={
                'host1': {'type': 'Compute'},
                'host2': {'type': 'Compute'},
                'db': {'type': 'Root',
                       'contained_in': 'host1',
                       'connected_to': ['webserver']},
                'webserver': {'type': 'Root',
                              'contained_in': 'host2'},
                'volume': {'type': 'Root',
                           'connected_to': ['host1']}
            },
            expected_instances={
                'host1': 2,
                'host2': 1,
                'db': 2,
                'webserver': 1,
                'volume': 2
            },
            expected_groups={
                'host1_group': {
                    'instances': 2,
                    'members': {
                        'host1': 1,
                        'volume': 1,
                        'db': 1
                    }
                }
            },
            expected_relationships={
                'db': [
                    {'target': 'host1',
                     'count': 2,
                     'source_count': 1,
                     'target_count': 1,
                     'groups': ['host1_group']},
                    {'target': 'webserver',
                     'count': 1,
                     'source_count': 2,
                     'target_count': 1,
                     'groups': []}
                ],
                'webserver': {
                    'target': 'host2',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                },
                'volume': {
                    'target': 'host1',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host1_group']
                }
            },
        )

    def test_group_intertwined(self):
        return self._test(
            groups={
                'group1': {
                    'instances': 2,
                    'members': ['node1', 'group2']
                },
                'group2': {
                    'members': ['node2', 'group3']
                },
                'group3': {
                    'members': ['group4']
                },
                'group4': {
                    'members': ['node3']
                }
            },
            nodes={
                'node1': {'type': 'Root'},
                'node2': {'type': 'Root',
                          'contained_in': 'node1'},
                'node3': {'type': 'Root',
                          'contained_in': 'node1'}
            },
            expected_instances={
                'node1': 2,
                'node2': 2,
                'node3': 2
            },
            expected_groups={
                'group1': {
                    'instances': 2,
                    'members': {
                        'node1': 1,
                        'node2': 1,
                        'node3': 1
                    }
                },
                'group2': {
                    'instances': 2,
                    'members': {
                        'node2': 1,
                        'node3': 1
                    }
                },
                'group3': {
                    'instances': 2,
                    'members': {
                        'node3': 1
                    }
                },
                'group4': {
                    'instances': 2,
                    'members': {
                        'node3': 1
                    }
                }
            },
            expected_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['group1']
                },
                'node3': {
                    'target': 'node1',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['group1']
                }
            },
        )

    def test_group_of_node_contained_in1(self):
        return self._test(
            groups={
                'group': {
                    'members': ['node2']
                },
            },
            nodes={
                'node1': {'type': 'Root'},
                'node2': {'type': 'Root',
                          'contained_in': 'node1'}
            },
            expected_instances={
                'node1': 1,
                'node2': 1
            },
            expected_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 1
                    }
                }
            },
            expected_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                },
            },
        )

    def test_group_of_node_contained_in2(self):
        return self._test(
            groups={
                'group': {
                    'members': ['node2']
                },
            },
            nodes={
                'node1': {'type': 'Root'},
                'node2': {'type': 'Root',
                          'contained_in': 'node1',
                          'instances': 3}
            },
            expected_instances={
                'node1': 1,
                'node2': 3
            },
            expected_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 3
                    }
                }
            },
            expected_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 3,
                    'target_count': 1,
                    'groups': []
                },
            },
        )

    # the following tests, test scaling during deployment modification (scale)

    def test_group_with_single_node_scale_out(self):
        self._test_modify(
            base=self.test_group_with_single_node,
            modified_nodes={
                'group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1
            },
            expected_added_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host': 1
                    }
                }
            }
        )

    def test_group_with_single_node_scale_in(self):
        self._test_modify(
            base=self.test_group_with_single_node,
            modified_nodes={
                'group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1
            },
            expected_removed_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host': 1
                    }
                }
            }
        )

    def test_group_with_two_nodes_scale_out(self):
        self._test_modify(
            base=self.test_group_with_two_nodes,
            modified_nodes={
                'group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host1': 1,
                'host2': 1,
            },
            expected_added_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'host2': 1,
                    }
                }
            }
        )

    def test_group_with_two_nodes_scale_in(self):
        self._test_modify(
            base=self.test_group_with_two_nodes,
            modified_nodes={
                'group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host1': 1,
                'host2': 1,
            },
            expected_removed_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'host2': 1,
                    }
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it1_scale_out(self):
        self._test_modify(
            base=self.test_group_with_host_and_node_contained_in_it1,
            modified_nodes={
                'group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'db': 1,
            },
            expected_added_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'db': 1,
                    }
                }
            },
            expected_added_relationships={
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['group']
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it1_scale_in(self):
        self._test_modify(
            base=self.test_group_with_host_and_node_contained_in_it1,
            modified_nodes={
                'group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'db': 1,
            },
            expected_removed_groups={
                'group': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'db': 1,
                    }
                }
            },
            expected_removed_relationships={
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['group']
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it2_scale_out(self):
        self._test_modify(
            base=self.test_group_with_host_and_node_contained_in_it2,
            modified_nodes={
                'host_group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'db': 1,
            },
            expected_added_groups={
                'host_group': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'db': 1,
                    }
                },
                'db_group': {
                    'instances': 1,
                    'members': {
                        'db': 1
                    }
                }
            },
            expected_added_relationships={
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host_group']
                }
            }
        )

    def test_group_with_host_and_node_contained_in_it2_scale_in(self):
        self._test_modify(
            base=self.test_group_with_host_and_node_contained_in_it2,
            modified_nodes={
                'host_group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'db': 1,
            },
            expected_removed_groups={
                'host_group': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'db': 1,
                    }
                },
                'db_group': {
                    'instances': 1,
                    'members': {
                        'db': 1
                    }
                }
            },
            expected_removed_relationships={
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['host_group']
                }
            }
        )

    def test_group_with_host_and_ip_scale_out(self):
        self._test_modify(
            base=self.test_group_with_host_and_ip,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'ip': 1,
            },
            expected_added_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                    }
                }
            },
            expected_added_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_and_ip_scale_in(self):
        self._test_modify(
            base=self.test_group_with_host_and_ip,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'ip': 1,
            },
            expected_removed_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                    }
                }
            },
            expected_removed_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_ip_and_volume_scale_out1(self):
        self._test_modify(
            base=self.test_group_with_host_ip_and_volume,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'ip': 1,
                'volume': 2
            },
            expected_added_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 2
                    }
                }
            },
            expected_added_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_ip_and_volume_scale_in1(self):
        self._test_modify(
            base=self.test_group_with_host_ip_and_volume,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'ip': 1,
                'volume': 2
            },
            expected_removed_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 2
                    }
                }
            },
            expected_removed_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_ip_and_volume_scale_out2(self):
        self._test_modify(
            base=self.test_group_with_host_ip_and_volume,
            modified_nodes={
                'volume': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'volume': 2
            },
            expected_related_to_added_instances={
                'host': 2
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'host': 1
                    }
                }
            },
            expected_added_relationships={
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_ip_and_volume_scale_in2(self):
        self._test_modify(
            base=self.test_group_with_host_ip_and_volume,
            modified_nodes={
                'volume': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'volume': 2
            },
            expected_related_to_removed_instances={
                'host': 2
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'volume': 1
                    }
                }
            },
            expected_removed_relationships={
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume_scale_out1(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'ip': 1,
                'volume': 2,
                'db': 1
            },
            expected_added_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 2,
                        'db': 1
                    }
                }
            },
            expected_added_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume_scale_in1(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'ip': 1,
                'volume': 2,
                'db': 1
            },
            expected_removed_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 2,
                        'db': 1
                    }
                }
            },
            expected_removed_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume_scale_out2(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume,
            modified_nodes={
                'volume': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'volume': 2
            },
            expected_related_to_added_instances={
                'host': 2
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'host': 1
                    }
                }
            },
            expected_added_relationships={
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume_scale_in2(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume,
            modified_nodes={
                'volume': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'volume': 2
            },
            expected_related_to_removed_instances={
                'host': 2
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'host': 1,
                        'volume': 1
                    }
                }
            },
            expected_removed_relationships={
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_out1(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'ip': 1,
                'volume': 5,
                'db': 3
            },
            expected_added_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'db': 3
                    }
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': {
                        'volume': 1
                    }
                }
            },
            expected_added_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': [
                    {'target': 'host',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources']},
                    {'target': 'volume',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources']},
                ],
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_in1(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'vm_with_resources': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'ip': 1,
                'volume': 5,
                'db': 3
            },
            expected_removed_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'db': 3
                    }
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': {
                        'volume': 1
                    }
                }
            },
            expected_removed_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'db': [
                    {'target': 'host',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources']},
                    {'target': 'volume',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources']},
                ],
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_out2(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'volume_scale_group': {
                    'instances': 6
                }
            },
            expected_added_instances={
                'volume': 2
            },
            expected_related_to_added_instances={
                'host': 2,
                'db': 6
            },
            expected_added_groups={
                'volume_scale_group': {
                    'instances': 2,
                    'members': {
                        'volume': 1
                    }
                }
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'host': 1,
                        'db': 3
                    }
                },
            },
            expected_added_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 3,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_in2(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'volume_scale_group': {
                    'instances': 4
                }
            },
            expected_removed_instances={
                'volume': 2
            },
            expected_related_to_removed_instances={
                'host': 2,
                'db': 6
            },
            expected_removed_groups={
                'volume_scale_group': {
                    'instances': 2,
                    'members': {
                        'volume': 1
                    }
                }
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'host': 1,
                        'db': 3
                    }
                },
            },
            expected_removed_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 3,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_out3(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'db': {
                    'instances': 4
                }
            },
            expected_added_instances={
                'db': 2
            },
            expected_related_to_added_instances={
                'host': 2,
                'volume': 10
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 5,
                        'host': 1,
                        'db': 1
                    }
                },
            },
            expected_added_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 5,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_and_volume2_scale_in3(self):
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_and_volume2,
            modified_nodes={
                'db': {
                    'instances': 2
                }
            },
            expected_removed_instances={
                'db': 2
            },
            expected_related_to_removed_instances={
                'host': 2,
                'volume': 10
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 5,
                        'host': 1,
                        'db': 1
                    }
                },
            },
            expected_removed_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 5,
                    'groups': ['vm_with_resources']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_out1(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'vm_with_resources': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host': 1,
                'ip': 1,
                'volume': 5,
                'volume_c': 5,
                'db': 3
            },
            expected_added_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'volume_c': 5,
                        'db': 3
                    }
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': {
                        'volume': 1,
                        'volume_c': 1,
                    }
                }
            },
            expected_added_and_related_group_members={
                'container': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'volume_c': 5,
                        'db': 3
                    }
                }
            },
            expected_added_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'db': [
                    {'target': 'host',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources', 'container']},
                    {'target': 'volume',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources', 'container']},
                ],
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume_c': {
                    'target': 'volume',
                    'count': 5,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['volume_scale_group', 'vm_with_resources',
                               'container']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_in1(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'vm_with_resources': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host': 1,
                'ip': 1,
                'volume': 5,
                'volume_c': 5,
                'db': 3
            },
            expected_removed_groups={
                'vm_with_resources': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'volume_c': 5,
                        'db': 3
                    }
                },
                'volume_scale_group': {
                    'instances': 5,
                    'members': {
                        'volume': 1,
                        'volume_c': 1
                    }
                }
            },
            expected_removed_and_related_group_members={
                'container': {
                    'instances': 1,
                    'members': {
                        'host': 1,
                        'ip': 1,
                        'volume': 5,
                        'volume_c': 5,
                        'db': 3
                    }
                }
            },
            expected_removed_relationships={
                'host': {
                    'target': 'ip',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'db': [
                    {'target': 'host',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 1,
                     'groups': ['vm_with_resources', 'container']},
                    {'target': 'volume',
                     'count': 1,
                     'source_count': 3,
                     'target_count': 5,
                     'groups': ['vm_with_resources', 'container']},
                ],
                'volume': {
                    'target': 'host',
                    'count': 1,
                    'source_count': 5,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume_c': {
                    'target': 'volume',
                    'count': 5,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['volume_scale_group', 'vm_with_resources',
                               'container']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_out2(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'volume_scale_group': {
                    'instances': 6
                }
            },
            expected_added_instances={
                'volume': 2,
                'volume_c': 2
            },
            expected_related_to_added_instances={
                'host': 2,
                'db': 6
            },
            expected_added_groups={
                'volume_scale_group': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'volume_c': 1
                    }
                }
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'volume_c': 1,
                        'host': 1,
                        'db': 3
                    }
                },
                'container': {
                    'instances': 1,
                    'members': {
                        'volume': 2,
                        'volume_c': 2,
                        'host': 2,
                        'db': 6
                    }
                },
            },
            expected_added_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 3,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume_c': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['volume_scale_group', 'vm_with_resources',
                               'container']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_in2(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'volume_scale_group': {
                    'instances': 4
                }
            },
            expected_removed_instances={
                'volume': 2,
                'volume_c': 2
            },
            expected_related_to_removed_instances={
                'host': 2,
                'db': 6
            },
            expected_removed_groups={
                'volume_scale_group': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'volume_c': 1
                    }
                }
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 1,
                        'volume_c': 1,
                        'host': 1,
                        'db': 3
                    }
                },
                'container': {
                    'instances': 1,
                    'members': {
                        'volume': 2,
                        'volume_c': 2,
                        'host': 2,
                        'db': 6
                    }
                }
            },
            expected_removed_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 3,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume': {
                    'target': 'host',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['vm_with_resources', 'container']
                },
                'volume_c': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': ['volume_scale_group', 'vm_with_resources',
                               'container']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_out3(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'db': {
                    'instances': 4
                }
            },
            expected_added_instances={
                'db': 2
            },
            expected_related_to_added_instances={
                'host': 2,
                'volume': 10
            },
            expected_added_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 5,
                        'host': 1,
                        'db': 1
                    }
                },
                'container': {
                    'instances': 1,
                    'members': {
                        'volume': 10,
                        'host': 2,
                        'db': 2
                    }
                }
            },
            expected_added_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 5,
                    'groups': ['vm_with_resources', 'container']
                }
            }
        )

    def test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container_scale_in3(self):  # noqa
        self._test_modify(
            base=self.test_group_with_host_db_contained_in_it_ip_volume_volume_c_and_container,  # noqa
            modified_nodes={
                'db': {
                    'instances': 2
                }
            },
            expected_removed_instances={
                'db': 2
            },
            expected_related_to_removed_instances={
                'host': 2,
                'volume': 10
            },
            expected_removed_and_related_group_members={
                'vm_with_resources': {
                    'instances': 2,
                    'members': {
                        'volume': 5,
                        'host': 1,
                        'db': 1
                    }
                },
                'container': {
                    'instances': 1,
                    'members': {
                        'volume': 10,
                        'host': 2,
                        'db': 2
                    }
                }
            },
            expected_removed_relationships={
                'db': {
                    'target': 'volume',
                    'count': 2,
                    'source_count': 1,
                    'target_count': 5,
                    'groups': ['vm_with_resources', 'container']
                }
            }
        )

    def test_group_with_external_nodes_not_in_any_group1_scale_out(self):
        self._test_modify(
            base=self.test_group_with_external_nodes_not_in_any_group1,
            modified_nodes={
                'host1_group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host1': 1,
                'db': 1,
                'volume': 1
            },
            expected_related_to_added_instances={
                'webserver': 1
            },
            expected_added_groups={
                'host1_group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'db': 1,
                        'volume': 1
                    }
                }
            },
            expected_added_relationships={
                'webserver': {
                    'target': 'db',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            }
        )

    def test_group_with_external_nodes_not_in_any_group1_scale_in(self):
        self._test_modify(
            base=self.test_group_with_external_nodes_not_in_any_group1,
            modified_nodes={
                'host1_group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host1': 1,
                'db': 1,
                'volume': 1
            },
            expected_related_to_removed_instances={
                'webserver': 1
            },
            expected_removed_groups={
                'host1_group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'db': 1,
                        'volume': 1
                    }
                }
            },
            expected_removed_relationships={
                'webserver': {
                    'target': 'db',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            }
        )

    def test_group_with_external_nodes_not_in_any_group2_scale_out(self):
        self._test_modify(
            base=self.test_group_with_external_nodes_not_in_any_group2,
            modified_nodes={
                'host1_group': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'host1': 1,
                'db': 1,
                'volume': 1
            },
            expected_related_to_added_instances={
                'webserver': 1
            },
            expected_added_groups={
                'host1_group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'db': 1,
                        'volume': 1
                    }
                }
            },
            expected_added_relationships={
                'db': {
                    'target': 'webserver',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            }
        )

    def test_group_with_external_nodes_not_in_any_group2_scale_in(self):
        self._test_modify(
            base=self.test_group_with_external_nodes_not_in_any_group2,
            modified_nodes={
                'host1_group': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'host1': 1,
                'db': 1,
                'volume': 1
            },
            expected_related_to_removed_instances={
                'webserver': 1
            },
            expected_removed_groups={
                'host1_group': {
                    'instances': 1,
                    'members': {
                        'host1': 1,
                        'db': 1,
                        'volume': 1
                    }
                }
            },
            expected_removed_relationships={
                'db': {
                    'target': 'webserver',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            }
        )

    def test_group_of_node_contained_in1_scale_out1(self):
        self._test_modify(
            base=self.test_group_of_node_contained_in1,
            modified_nodes={
                'node2': {
                    'instances': 2
                }
            },
            expected_added_instances={
                'node2': 1,
            },
            expected_related_to_added_instances={
                'node1': 1
            },
            expected_added_and_related_group_members={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 1
                    }
                }
            },
            expected_added_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            })

    def test_group_of_node_contained_in1_scale_out2(self):
        self._test_modify(
            base=self.test_group_of_node_contained_in1,
            modified_nodes={
                'node2': {
                    'instances': 3
                }
            },
            expected_added_instances={
                'node2': 2,
            },
            expected_related_to_added_instances={
                'node1': 1
            },
            expected_added_and_related_group_members={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 2
                    }
                }
            },
            expected_added_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': []
                }
            })

    def test_group_of_node_contained_in2_scale_in1(self):
        self._test_modify(
            base=self.test_group_of_node_contained_in2,
            modified_nodes={
                'node2': {
                    'instances': 2
                }
            },
            expected_removed_instances={
                'node2': 1,
            },
            expected_related_to_removed_instances={
                'node1': 1
            },
            expected_removed_and_related_group_members={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 1
                    }
                }
            },
            expected_removed_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 1,
                    'target_count': 1,
                    'groups': []
                }
            })

    def test_group_of_node_contained_in2_scale_in2(self):
        self._test_modify(
            base=self.test_group_of_node_contained_in2,
            modified_nodes={
                'node2': {
                    'instances': 1
                }
            },
            expected_removed_instances={
                'node2': 2,
            },
            expected_related_to_removed_instances={
                'node1': 1
            },
            expected_removed_and_related_group_members={
                'group': {
                    'instances': 1,
                    'members': {
                        'node2': 2
                    }
                }
            },
            expected_removed_relationships={
                'node2': {
                    'target': 'node1',
                    'count': 1,
                    'source_count': 2,
                    'target_count': 1,
                    'groups': []
                }
            })

    def _test(
            self,
            groups,
            nodes,
            expected_instances,
            expected_groups,
            expected_relationships=None):
        """Main test util method for testing scaling during initial blueprint
        parsing (deployment creation).

        This method will create a blueprint file from the supplied ``groups``
        and ``nodes``. It will then assert the resulting plan for
        ``expected_instances``, ``expected_groups`` and
        ``expected_relationships``.

       ``groups`` is a dict from group names to the group definitions
        a group definition has the following structure::

            {
                'instances': 3,  # number of initial instances
                'members': ['host1', 'db1']  # group members
            }

        ``nodes`` is a dict from node names to node definitions
        a node definition has the following structure::

            {
                'type': 'Root',  # Compute or Root are allowed
                'instances': 2,  # initial instances (optional, default 1)
                'contained_in': 'host1',  # optional,
                'connected_to': ['db1', 'volume1']  # optional
            }

        ``expected_instances`` is a dict from node names to total expected
        number of node instances this node will have after multi parser. eg::

            {
                'host1': 12,
                'db1': 24
            }

        ``expected_groups`` is a dict from group names to group
        expectations. a group expectation has the following structure::

            {
                'instances': 2,  # total expected number of group instances

                # for each node member, the expected number of instances
                # inside a group instance. e.g. if there are a total of 4 host
                # instances spread across two groups, then within a group
                # instance, 2 host instances a expected (as in the example
                # below)
                # note that all group members are expected, also those that are
                # implicitly contained in a group due to them being contained
                # in some other node that is contained in a group (recursively)
                'members': {
                    'host': 2,
                    'db': 6,
                    'ip': 2,
                    'volume': 10,
                    'volume_c': 10
                }

        ``expected_relationships`` is a dict from relationship sources to
        relationship target expectations. if a source has more than one target
        it key is a list of targets. e.g.::

            expected_relationships = {
                # key is source node name
                'host': {

                    # target is target name
                    'target': 'ip',

                    # expected number of weakly connected components with
                    # relationships between source and target node instances.
                    # for example, if a db is connected to a volume and both
                    # are contained in some group, then within each group
                    # instance, the connection will be all_to_all but the
                    # connection will not "escape" group boundaries.
                    'count': 2,

                    # number of expected source instances within each weakly
                    # connected component
                    'source_count': 1,

                    # number of expected target instances within each weakly
                    # connected component
                    'target_count': 1,

                    # groups that are expected to have a group instance
                    # containing the entire component (for each component)
                    # (all source and target instances of a single component)
                    'groups': ['vm_with_resources', 'container']
                },
                # example for a list of targets
                'db': [
                    {'target': 'host',
                     ...},
                    {'target': 'volume',
                     ...}
                ],
            }

        .. note::
            If a test is to be "extended" by a modification test, it should
            return the result of the ``self._test`` invocation.
        """

        # generate a blueprint and parse a multi-instance plan based on the
        # provided groups and nodes.
        plan = self._parse_multi(groups=groups, nodes=nodes)
        node_instances = plan['node_instances']

        self._assert_instances_count(
            node_instances=node_instances,
            expected_instances=expected_instances)

        group_components = self._assert_groups(
            plan=plan,
            expected_groups=expected_groups,
            node_instances=plan['node_instances'],
            assert_scaling_groups_count=True)

        self._assert_relationships(
            node_instances=node_instances,
            expected_relationships=expected_relationships,
            group_components=group_components)

        # Used by modification tests as the result of the base tests
        # (``self._test_modify``)
        return {'plan': plan, 'initial_group_components': group_components}

    def _test_modify(
            self,
            base,
            modified_nodes,
            expected_added_instances=None,
            expected_related_to_added_instances=None,
            expected_removed_instances=None,
            expected_related_to_removed_instances=None,
            expected_added_groups=None,
            expected_added_and_related_group_members=None,
            expected_removed_groups=None,
            expected_removed_and_related_group_members=None,
            expected_added_relationships=None,
            expected_removed_relationships=None):
        """Main test utility method for testing deployment modification (e.g.
        scale out/scale in)

        This method expects a base test to build upon (a test using the
        ``self._test`` method) and a modification definition. It then accepts
        many different optional (depending on the context) expectations.

        the ``base`` parameters should be a function that makes use of
        ``self._test`` and returns its return value.

        ``modified_nodes`` is a dict from a modification to a new instance
        count. nodes and groups can be specified. e.g.::

            modified_nodes = {
                # the node or group name
                'vm_with_resources': {
                    # the new absolute number of instances
                    'instances': 3
                }

        ``expected_added_instances`` is a dict from node names to the expected
        number of added node instances. e.g.::

            {
                'host': 2,
                'db': 2
            }

        ``expected_related_to_added_instances`` is a dict from node names of
        nodes that have a relationship from/to a new node instance but are not
        new themselves. It has the same structure as
        ``expected_added_instances``

        ``expected_removed_instances`` is a dict from node names to the
        expected number of removed node instances, it has the same structure as
        ``expected_added_instances``

        ``expected_related_to_removed_instances`` is a dict from node names of
        nodes that have a relationship from/to a removed node instance but are
        not removed themselves. It has the same structure as
        ``expected_added_instances``

        ``expected_added_groups`` is a dict from group names to group
        definitions. the groups in this dict are groups which are expected to
        have entirely new logical instances. a group definition has the
        following structure::

            {
                # expected number of new group instances
                'instances': 2,

                # for each group instance, for each node group member
                # expected number of new group node instance members
                'members': {
                    'volume': 1,
                    'volume_c': 1
                }
            }

        ``expected_added_and_related_group_members`` is a dict from group names
        to group definitions. the groups in this dict are groups which their
        instances are expected to have new members (but the group instance
        already existed). a group definition has the following structure::

            {
                # expected number of existing groups instances that are
                # affected by the newly added node instances.
                'instances': 2,

                # all group members that are affected by the newly added nodes.
                # this includes the newly added nodes, and nodes that have a
                # relationship to/from the added nodes.
                'members': {
                    'volume': 1,
                    'volume_c': 1,
                    'host': 1,
                    'db': 3
                }
            },

        ``expected_removed_groups`` follows the same logic as
        ``expected_added_groups`` but for removed group instances

        ``expected_added_and_related_group_members`` follows the same logic as
        ``expected_removed_and_related_group_members`` but for removed node
        instances.

        ``expected_added_relationships`` and ``expected_removed_relationships``
        follow the same logic as in ``self._test``, ``expected_relationships``
        parameters. The expectations themselves should only be for new/removed
        relationships and their respective source/target node instances.

        """

        # call the base test and extract initial test data.
        result = base()
        plan = result['plan']
        initial_group_components = result['initial_group_components']

        # make actual multi instance modification
        modification = self.modify_multi(plan=plan,
                                         modified_nodes=modified_nodes)

        added_and_related_node_instances = modification['added_and_related']
        removed_and_related_node_instances = modification[
            'removed_and_related']

        self._assert_modification_instances_count(
            plan=plan,
            added_and_related_node_instances=added_and_related_node_instances,
            removed_and_related_node_instances=removed_and_related_node_instances,  # noqa
            expected_added_instances=expected_added_instances,
            expected_related_to_added_instances=expected_related_to_added_instances,  # noqa
            expected_removed_instances=expected_removed_instances,
            expected_related_to_removed_instances=expected_related_to_removed_instances)  # noqa

        added_group_components, removed_group_components = self._assert_modification_groups(  # noqa
            plan=plan,
            initial_group_components=initial_group_components,
            added_and_related_node_instances=added_and_related_node_instances,
            removed_and_related_node_instances=removed_and_related_node_instances,  # noqa
            expected_added_groups=expected_added_groups,
            expected_added_and_related_group_members=expected_added_and_related_group_members,  # noqa
            expected_removed_groups=expected_removed_groups,
            expected_removed_and_related_group_members=expected_removed_and_related_group_members)  # noqa

        self._assert_modification_relationships(
            added_and_related_node_instances=added_and_related_node_instances,
            removed_and_related_node_instances=removed_and_related_node_instances,  # noqa
            added_group_components=added_group_components,
            removed_group_components=removed_group_components,
            expected_added_relationships=expected_added_relationships,
            expected_removed_relationships=expected_removed_relationships)

    def _assert_instances_count(
            self,
            node_instances,
            expected_instances):
        # for node verify that its number of instances is as expected.
        expected_instances = expected_instances or {}
        expected_total = 0
        for node_id, expected_count in expected_instances.items():
            expected_total += expected_count
            instances = self._nodes_by_name(
                nodes=node_instances,
                name=node_id)
            self.assertEqual(expected_count, len(instances))
        # verify that the total number of node instances adds up
        self.assertEqual(expected_total, len(node_instances))

    def _assert_modification_instances_count(
            self,
            plan,
            added_and_related_node_instances,
            removed_and_related_node_instances,
            expected_added_instances,
            expected_related_to_added_instances,
            expected_removed_instances,
            expected_related_to_removed_instances):

        node_instances = plan['node_instances']
        node_instance_ids = set(i['id'] for i in node_instances)

        def assert_new(instances):
            for instance in instances:
                self.assertNotIn(instance['id'], node_instance_ids)

        def assert_existing(instances):
            for instance in instances:
                self.assertIn(instance['id'], node_instance_ids)

        added_node_instances = [
            n for n in added_and_related_node_instances
            if n.get('modification') == 'added']
        self._assert_instances_count(
            node_instances=added_node_instances,
            expected_instances=expected_added_instances)
        assert_new(added_node_instances)

        related_to_added_node_instances = [
            n for n in added_and_related_node_instances
            if n.get('modification') != 'added']
        self._assert_instances_count(
            node_instances=related_to_added_node_instances,
            expected_instances=expected_related_to_added_instances)
        assert_existing(related_to_added_node_instances)

        removed_node_instances = [
            n for n in removed_and_related_node_instances
            if n.get('modification') == 'removed']
        self._assert_instances_count(
            node_instances=removed_node_instances,
            expected_instances=expected_removed_instances)
        assert_existing(related_to_added_node_instances)

        related_to_removed_node_instances = [
            n for n in removed_and_related_node_instances
            if n.get('modification') != 'removed']
        self._assert_instances_count(
            node_instances=related_to_removed_node_instances,
            expected_instances=expected_related_to_removed_instances)
        assert_existing(related_to_added_node_instances)

    def _assert_groups(
            self,
            plan,
            node_instances,
            expected_groups,
            assert_scaling_groups_count=False,
            assert_new_group_instances=False,
            assert_old_group_instances=False,
            assert_group_instances_remain=False,
            initial_group_components=None):

        # validating correct test util usage
        assert not (assert_new_group_instances and assert_old_group_instances)

        # these assertions are only relevant for modification tests
        # thus, we verify that we have the initial group components
        # that were generated in the base test.
        if assert_old_group_instances or assert_new_group_instances:
            assert initial_group_components

        expected_groups = expected_groups or {}

        # we copy the plan and the provided node instances because the
        # rel_graph calls modify these data structure
        plan_copy = copy.deepcopy(plan)
        node_instances_copy = copy.deepcopy(node_instances)

        scaling_groups = plan_copy['scaling_groups']
        plan_graph = rel_graph.build_node_graph(
            nodes=plan_copy['nodes'],
            scaling_groups=scaling_groups)

        # re-use internal rel_graph method that builds node/group instances
        # graph, only use the contained_graph it builds
        # the previous_node_instances kwargs is misleading in its name.
        # it makes sense in the actual context in which it is called.
        # here, it is simply the node instances used to build the graph.
        _, contained_graph = rel_graph.build_previous_deployment_node_graph(
            plan_node_graph=plan_graph,
            previous_node_instances=node_instances_copy)

        # for modification tests, we want to maintain weakly connected
        # components, for example, if a db is contained in a host and that
        # db is connected to a volume and the volume is connected to the host.
        # and all these nodes are part of some group.
        # if the volume is scaled, there will be no new/removed relationships
        # between the db and the host, but we still want to treat them as part
        # of the same group instance. thus, we augment to contained_graph
        # with relationships from the full deployment plan graph and marks
        # nodes that are not part of the new graph with a 'stub' marker.
        # so we can filter them out later.
        if initial_group_components:
            _, p_contained_graph = rel_graph.\
                build_previous_deployment_node_graph(
                    plan_node_graph=plan_graph,
                    previous_node_instances=plan_copy['node_instances'])
            for n, data in p_contained_graph.nodes_iter(data=True):
                if n not in contained_graph:
                    contained_graph.add_node(n, stub=True, **data)
            for s, t in p_contained_graph.edges_iter():
                if not contained_graph.has_edge(s, t):
                    contained_graph.add_edge(s, t)

        # groups components is calculated in this function and is used by
        # the assert relationship tests and by this assert group method
        # when called as part of a modification test (initial_group_components)
        # each key is a group name. each value is a dict with all group
        # instance ids and for each group instance, all node instances that
        # are contained in that group (recursively)
        group_components = {}

        # for create deployment plan tests (not modification tests)
        # this assertion serves for robustness purposes, to make sure
        # all scaling groups were included in the initial expected_groups.
        # it is not used in modification tests because not all groups
        # are necessarily affected by a modification.
        if assert_scaling_groups_count:
            self.assertEqual(len(scaling_groups), len(expected_groups))

        for group_name, expected_group in expected_groups.items():

            # The following builds weakly connected components that include
            # all node instances that are contained in each group instance

            # first extract group instances
            group_instances = set(
                n for n in contained_graph
                if not contained_graph.node[n].get('stub') and
                contained_graph.node[n]['node']['name'] == group_name)

            # now, for each group instance include all its ancestors including
            # itself
            contained_in_group_instances = []
            for group_instance in group_instances:
                contained_in_group_instances.append(group_instance)
                contained_in_group_instances += nx.ancestors(contained_graph,
                                                             group_instance)

            # build a subgraph containing only nodes that are part of any
            # instance of the current group
            group_subgraph = contained_graph.subgraph(
                contained_in_group_instances)

            # split subgraph into weakly connected components.
            components = nx.weakly_connected_component_subgraphs(
                group_subgraph)

            # verify expected number of group instances
            self.assertEqual(
                expected_group['instances'],
                nx.number_weakly_connected_components(group_subgraph))

            # export all group instances and for each group instance its
            # its members
            instances_and_ancestors = [
                set(n for n in c if not contained_graph.node[n].get('stub'))
                for c in components]
            group_components[group_name] = {
                'instances': group_instances,
                'instances_and_ancestors': instances_and_ancestors
            }

            # used by scale out modification tests to verify all group
            # instances are indeed new
            if assert_new_group_instances:
                previous_group_instances = initial_group_components[
                    group_name]['instances']
                self.assertFalse(group_instances & previous_group_instances)

            # used by scale in modification tests to verify all group
            # instances are instances that actually existed before the
            # modification
            elif assert_old_group_instances:
                previous_group_instances = initial_group_components[
                    group_name]['instances']
                self.assertTrue(group_instances <= previous_group_instances)

            # for each group instance:
            for component in components:
                expected_total_count = 0
                for member, count in expected_group['members'].items():
                    expected_total_count += count
                    component_members = [
                        n for n in component if
                        not component.node[n].get('stub') and
                        component.node[n]['node']['name'] == member]
                    # verify expected node instances member count
                    # component members is a list of all node instances
                    # of a single node contained within the current group
                    # instance
                    self.assertEqual(count, len(component_members))
                component_node_members = [
                    n for n in component if
                    not component.node[n].get('stub') and
                    not component.node[n]['node'].get('group')]
                # verify group member instances count adds up
                self.assertEqual(expected_total_count,
                                 len(component_node_members))

                # used by scale in modification tests to verify that a certain
                # group instance still exists (is references by some node
                # instances).
                if assert_group_instances_remain:
                    self.assertTrue(
                        any(component.node[n]['node'].get(
                            'modification') != 'removed' for n in component
                            if not component.node[n]['node'].get('group')))
        return group_components

    def _assert_modification_groups(
            self,
            plan,
            initial_group_components,
            added_and_related_node_instances,
            removed_and_related_node_instances,
            expected_added_groups,
            expected_added_and_related_group_members,
            expected_removed_groups,
            expected_removed_and_related_group_members):

        # added_group_components is used by added relationships assertions
        added_group_components = {}
        if expected_added_groups:
            group_components = self._assert_groups(
                plan=plan,
                expected_groups=expected_added_groups,
                node_instances=added_and_related_node_instances,
                initial_group_components=initial_group_components,
                assert_new_group_instances=True)
            added_group_components.update(group_components)
        if expected_added_and_related_group_members:
            group_components = self._assert_groups(
                plan=plan,
                expected_groups=expected_added_and_related_group_members,
                node_instances=added_and_related_node_instances,
                initial_group_components=initial_group_components,
                assert_old_group_instances=True)
            added_group_components.update(group_components)

        # removed_group_components is used by removed relationships assertions
        removed_group_components = {}
        if expected_removed_groups:
            group_components = self._assert_groups(
                plan=plan,
                expected_groups=expected_removed_groups,
                node_instances=removed_and_related_node_instances,
                initial_group_components=initial_group_components,
                assert_old_group_instances=True)
            removed_group_components.update(group_components)
        if expected_removed_and_related_group_members:
            group_components = self._assert_groups(
                plan=plan,
                expected_groups=expected_removed_and_related_group_members,
                node_instances=removed_and_related_node_instances,
                initial_group_components=initial_group_components,
                assert_old_group_instances=True,
                assert_group_instances_remain=True)
            removed_group_components.update(group_components)

        return added_group_components, removed_group_components

    def _assert_relationships(
            self,
            node_instances,
            expected_relationships,
            group_components):
        expected_relationships = expected_relationships or {}
        for node_id, relationships in expected_relationships.items():

            # normalize expected_relationships to be a list
            if not isinstance(relationships, list):
                relationships = [relationships]

            source_instances = self._nodes_by_name(nodes=node_instances,
                                                   name=node_id)

            for relationship in relationships:

                target_name = relationship['target']
                components_count = relationship['count']
                source_count = relationship['source_count']
                target_count = relationship['target_count']
                groups = relationship['groups']

                # for each relationship, build a graph containing all
                # source and target node instances.
                r_graph = nx.DiGraph()
                for source in source_instances:
                    r_graph.add_node(source['id'], source=True)
                    source_relationships = self._relationships_by_target_name(
                        source['relationships'], target_name)
                    for source_relationship in source_relationships:
                        r_graph.add_edge(source['id'],
                                         source_relationship['target_id'])

                # split graph into weakly connected components
                components = nx.weakly_connected_component_subgraphs(r_graph)

                # assert expected number of components count
                self.assertEqual(
                    components_count,
                    nx.number_weakly_connected_components(r_graph))

                # for each weakly connected component:
                for component in components:

                    # assert expected source node instances count
                    component_source_nodes = [
                        n for n in component
                        if component.node[n].get('source')]
                    self.assertEqual(source_count, len(component_source_nodes))

                    # assert expected target node instances count
                    component_target_nodes = [
                        n for n in component
                        if not component.node[n].get('source')]
                    self.assertEqual(target_count, len(component_target_nodes))

                    # assert that each source node instance is indeed connected
                    # to all target node instances withing the component.
                    for component_source_node in component_source_nodes:
                        self.assertEqual(
                            target_count,
                            len(r_graph.successors(component_source_node)))

                    # for each group specified in the expected relationship
                    # verify that a group instance containing all source
                    # and target node instances exists.
                    component_set = set(component)
                    for group_name in groups:
                        ancestors = group_components[
                            group_name]['instances_and_ancestors']
                        self.assertTrue(
                            any(component_set <= group for group in ancestors))

    def _assert_modification_relationships(
            self,
            added_and_related_node_instances,
            removed_and_related_node_instances,
            added_group_components,
            removed_group_components,
            expected_added_relationships,
            expected_removed_relationships):
        self._assert_relationships(added_and_related_node_instances,
                                   expected_added_relationships,
                                   group_components=added_group_components)
        self._assert_relationships(removed_and_related_node_instances,
                                   expected_removed_relationships,
                                   group_components=removed_group_components)

    def _parse_multi(self, groups, nodes):
        """This method builds a build a blueprint and parses a multi instance
        plan based in the provided groups and nodes"""

        node_templates = {}
        for node_id, node in nodes.items():
            node_template = {
                'type': 'cloudify.nodes.{0}'.format(node['type'])
            }
            instances = node.get('instances')
            contained_in = node.get('contained_in')
            connected_to = node.get('connected_to')
            relationships = []
            if contained_in:
                relationships.append({
                    'type': 'cloudify.relationships.contained_in',
                    'target': contained_in
                })
            if connected_to:
                for target in connected_to:
                    relationships.append({
                        'type': 'cloudify.relationships.connected_to',
                        'target': target
                    })
            if instances is not None:
                node_template['capabilities'] = {
                    'scalable': {
                        'properties': {
                            'default_instances': instances
                        }
                    }
                }
            node_template['relationships'] = relationships
            node_templates[node_id] = node_template

        blueprint_groups = {}
        policies = {}
        for group_name, group in groups.items():
            blueprint_groups[group_name] = {
                'members': group['members']
            }
            group_instances = group.get('instances')
            policies[group_name] = {
                'type': constants.SCALING_POLICY,
                'targets': [group_name]
            }
            if group_instances is not None:
                policies[group_name]['properties'] = {
                    'default_instances': group_instances
                }

        # final blueprint definition
        blueprint = {
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'node_types': {
                'cloudify.nodes.Compute': {},
                'cloudify.nodes.Root': {}
            },
            'relationships': {
                'cloudify.relationships.contained_in': {},
                'cloudify.relationships.connected_to': {
                    'properties': {
                        'connection_type': {
                            'default': 'all_to_all'
                        }
                    }
                }},
            'node_templates': node_templates,
            'groups': blueprint_groups,
            'policies': policies
        }

        # convert to yaml a parse a multi instance plan
        return self.parse_multi(yaml.safe_dump(blueprint))
