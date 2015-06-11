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

import testtools
from dsl_parser.interfaces.constants import NO_OP

from dsl_parser.interfaces.interfaces_parser import (
    merge_node_type_interfaces,
    merge_relationship_type_and_instance_interfaces,
    merge_node_type_and_node_template_interfaces,
    merge_relationship_type_interfaces)
from dsl_parser.elements import operation

from dsl_parser.tests.interfaces import validate


class InterfacesParserTest(testtools.TestCase):

    def _validate_type_interfaces(self, interfaces):
        validate(interfaces, operation.NodeTypeInterfaces)

    def _validate_instance_interfaces(self, interfaces):
        validate(interfaces, operation.NodeTemplateInterfaces)

    def test_merge_node_type_interfaces(self):

        overriding_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            }
        }
        overridden_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    },
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            },
            'interface2': {
                'start': {
                    'implementation': '',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(overriding_interfaces)
        self._validate_type_interfaces(overridden_interfaces)
        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overriding(self):

        overriding_interfaces = {}
        overridden_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        self._validate_type_interfaces(overridden_interfaces)
        self._validate_type_interfaces(overriding_interfaces)
        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overridden(self):

        overriding_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        overridden_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        self._validate_type_interfaces(overridden_interfaces)
        self._validate_type_interfaces(overriding_interfaces)
        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_node_type_and_node_template_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            }
        }

        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': 'value'
                    },
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(node_type_interfaces)
        self._validate_instance_interfaces(node_template_interfaces)
        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type_interfaces=node_type_interfaces,
                node_template_interfaces=node_template_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_node_type_no_interfaces_and_node_template_interfaces(self):

        node_type_interfaces = {}
        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start'
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(node_type_interfaces)
        self._validate_instance_interfaces(node_template_interfaces)
        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type_interfaces=node_type_interfaces,
                node_template_interfaces=node_template_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_node_type_interfaces_and_node_template_no_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                }
            }
        }
        node_template_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(node_type_interfaces)
        self._validate_instance_interfaces(node_template_interfaces)
        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type_interfaces=node_type_interfaces,
                node_template_interfaces=node_template_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_interfaces(self):

        overriding_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            }
        }

        overridden_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    },
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            },
            'interface2': {
                'start': {
                    'implementation': '',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(overriding_interfaces)
        self._validate_type_interfaces(overridden_interfaces)
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overriding(self):  # NOQA

        overriding_interfaces = {}
        overridden_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        self._validate_type_interfaces(overriding_interfaces)
        self._validate_type_interfaces(overridden_interfaces)
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overridden(self):  # NOQA

        overriding_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        overridden_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        self._validate_type_interfaces(overriding_interfaces)
        self._validate_type_interfaces(overridden_interfaces)
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_interfaces(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            }
        }

        relationship_instance_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': 'value'
                    },
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(relationship_type_interfaces)
        self._validate_instance_interfaces(relationship_instance_interfaces)
        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type_interfaces=relationship_type_interfaces,
                relationship_instance_interfaces=relationship_instance_interfaces)  # noqa

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_no_interfaces_and_instance_interfaces(self):  # NOQA

        relationship_type_interfaces = {}
        relationship_instance_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(relationship_type_interfaces)
        self._validate_instance_interfaces(relationship_instance_interfaces)
        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type_interfaces=relationship_type_interfaces,
                relationship_instance_interfaces=relationship_instance_interfaces)  # noqa

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_no_interfaces(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            }
        }

        relationship_instance_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {},
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': 'value'
                    },
                    'executor': None,
                    'max_retries': None,
                    'retry_interval': None
                }
            }
        }

        self._validate_type_interfaces(relationship_type_interfaces)
        self._validate_instance_interfaces(relationship_instance_interfaces)
        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type_interfaces=relationship_type_interfaces,
                relationship_instance_interfaces=relationship_instance_interfaces)  # noqa

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)
