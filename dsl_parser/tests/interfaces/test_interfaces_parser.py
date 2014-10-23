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
from jsonschema import validate
from dsl_parser.constants import INTERFACES
from dsl_parser.interfaces.constants import NO_OP

from dsl_parser.interfaces.interfaces_parser import \
    merge_node_type_interfaces
from dsl_parser.interfaces.interfaces_parser import \
    merge_relationship_type_and_instance_interfaces
from dsl_parser.interfaces.interfaces_parser import \
    merge_node_type_and_node_template_interfaces
from dsl_parser.interfaces.interfaces_parser import \
    merge_relationship_type_interfaces
from dsl_parser.parser import SOURCE_INTERFACES, TARGET_INTERFACES
from dsl_parser.schemas import NODE_TYPE_INTERFACES_SCHEMA, RELATIONSHIP_TYPE_INTERFACES_SCHEMA, \
    RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA
from dsl_parser.schemas import NODE_TEMPLATE_INTERFACES_SCHEMA


class InterfacesParserTest(testtools.TestCase):

    def _create_node_type(self, interfaces):
        validate(interfaces, NODE_TYPE_INTERFACES_SCHEMA)
        return {
            INTERFACES: interfaces
        }

    def _create_node_template(self, interfaces):
        validate(interfaces, NODE_TEMPLATE_INTERFACES_SCHEMA)
        return {
            INTERFACES: interfaces
        }

    def _create_relationship_type(self,
                                  source_interfaces=None,
                                  target_interfaces=None):
        result = {}
        if source_interfaces:
            validate(source_interfaces, RELATIONSHIP_TYPE_INTERFACES_SCHEMA)
            result[SOURCE_INTERFACES] = source_interfaces
        if target_interfaces:
            validate(target_interfaces, RELATIONSHIP_TYPE_INTERFACES_SCHEMA)
            result[TARGET_INTERFACES] = target_interfaces
        return result

    def _create_relationship_instance(self,
                                      source_interfaces=None,
                                      target_interfaces=None):
        result = {}
        if source_interfaces:
            validate(source_interfaces,
                     RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA)
            result[SOURCE_INTERFACES] = source_interfaces
        if target_interfaces:
            validate(target_interfaces,
                     RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA)
            result[TARGET_INTERFACES] = target_interfaces
        return result

    def test_merge_node_type_interfaces(self):

        overriding_node_type = self._create_node_type(
            interfaces={
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
        )
        overridden_node_type = self._create_node_type(
            interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {}
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }
                    }
                }
            },
            'interface2': {
                'start': {
                    'implementation': '',
                    'inputs': {}
                }
            }
        }

        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_node_type=overriding_node_type,
            overridden_node_type=overridden_node_type
        )
        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overriding(self):

        overriding_node_type = {}
        overridden_node_type = self._create_node_type(
            interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_node_type=overriding_node_type,
            overridden_node_type=overridden_node_type
        )
        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overridden(self):

        overriding_node_type = self._create_node_type(
            interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )
        overridden_node_type = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        actual_merged_interfaces = merge_node_type_interfaces(
            overriding_node_type=overriding_node_type,
            overridden_node_type=overridden_node_type
        )
        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_node_type_and_node_template_interfaces(self):

        node_type = self._create_node_type(
            interfaces={
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
        )

        node_template = self._create_node_template(
            interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'inputs': {}
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': 'value'
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type=node_type,
                node_template=node_template
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_node_type_no_interfaces_and_node_template_interfaces(self):

        node_type = {}
        node_template = self._create_node_template(
            interfaces={
                'interface1': {
                    'start': 'mock.tasks.start'
                }
            }
        )

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {}
                }
            }
        }

        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type=node_type,
                node_template=node_template
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_node_type_interfaces_and_node_template_no_interfaces(self):

        node_type = self._create_node_type(
            interfaces={
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start'
                    }
                }
            }
        )
        node_template = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'inputs': {}
                }
            }
        }

        actual_merged_interfaces = \
            merge_node_type_and_node_template_interfaces(
                node_type=node_type,
                node_template=node_template
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_interfaces(self):

        overriding_relationship_type = self._create_relationship_type(
            source_interfaces={
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
            },
            target_interfaces={
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
        )
        overridden_relationship_type = self._create_relationship_type(
            source_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            },
            target_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': {
                                'default': 'value'
                            }
                        }
                    }
                },
                'interface2': {
                    'start': {
                        'implementation': '',
                        'inputs': {}
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': {
                                'default': 'value'
                            }
                        }
                    }
                },
                'interface2': {
                    'start': {
                        'implementation': '',
                        'inputs': {}
                    }
                }
            }
        }
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_relationship_type=overriding_relationship_type,
            overridden_relationship_type=overridden_relationship_type
        )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_source_interfaces_on_overriding(self):  # NOQA

        overriding_relationship_type = self._create_relationship_type(
            target_interfaces={
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
        )
        overridden_relationship_type = self._create_relationship_type(
            source_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            },
            target_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': {
                                'default': 'value'
                            }
                        }
                    }
                },
                'interface2': {
                    'start': {
                        'implementation': '',
                        'inputs': {}
                    }
                }
            }
        }
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_relationship_type=overriding_relationship_type,
            overridden_relationship_type=overridden_relationship_type
        )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_source_interfaces_on_overridden(self):  # NOQA

        overriding_relationship_type = self._create_relationship_type(
            source_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            },
            target_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        overridden_relationship_type = self._create_relationship_type(
            target_interfaces={
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
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            }
        }
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_relationship_type=overriding_relationship_type,
            overridden_relationship_type=overridden_relationship_type
        )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_target_interfaces_on_overriding(self):  # NOQA

        overriding_relationship_type = self._create_relationship_type(
            source_interfaces={
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
        )
        overridden_relationship_type = self._create_relationship_type(
            source_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            },
            target_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': {
                                'default': 'value'
                            }
                        }
                    }
                },
                'interface2': {
                    'start': NO_OP
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            }
        }
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_relationship_type=overriding_relationship_type,
            overridden_relationship_type=overridden_relationship_type
        )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_target_interfaces_on_overridden(self):  # NOQA

        overriding_relationship_type = self._create_relationship_type(
            source_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            },
            target_interfaces={
                'interface1': {
                    'start': {},
                    'stop': {}
                },
                'interface2': {
                    'start': {}
                }
            }
        )

        overridden_relationship_type = self._create_relationship_type(
            source_interfaces={
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
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': NO_OP,
                    'stop': NO_OP
                },
                'interface2': {
                    'start': NO_OP
                }
            }
        }
        actual_merged_interfaces = merge_relationship_type_interfaces(
            overriding_relationship_type=overriding_relationship_type,
            overridden_relationship_type=overridden_relationship_type
        )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_interfaces(self):

        relationship_type = self._create_relationship_type(
            source_interfaces={
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
            },
            target_interfaces={
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
        )
        relationship_instance = self._create_relationship_instance(
            source_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            },
            target_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type=relationship_type,
                relationship_instance=relationship_instance
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_no_source_interfaces_and_instance_interfaces(self):  # NOQA

        relationship_type = self._create_relationship_type(
            target_interfaces={
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
        )
        relationship_instance = self._create_relationship_instance(
            source_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            },
            target_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type=relationship_type,
                relationship_instance=relationship_instance
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_no_target_interfaces_type_and_instance_interfaces(self):  # NOQA

        relationship_type = self._create_relationship_type(
            source_interfaces={
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
        )
        relationship_instance = self._create_relationship_instance(
            source_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            },
            target_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type=relationship_type,
                relationship_instance=relationship_instance
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_no_source_interfaces(self):

        relationship_type = self._create_relationship_type(
            source_interfaces={
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
            },
            target_interfaces={
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
        )
        relationship_instance = self._create_relationship_instance(
            target_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type=relationship_type,
                relationship_instance=relationship_instance
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_no_target_interfaces(self):

        relationship_type = self._create_relationship_type(
            source_interfaces={
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
            },
            target_interfaces={
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
        )
        relationship_instance = self._create_relationship_instance(
            source_interfaces={
                'interface1': {
                    'start': 'mock.tasks.start-overridden'
                }
            }
        )

        expected_merged_interfaces = {
            SOURCE_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start-overridden',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            },
            TARGET_INTERFACES: {
                'interface1': {
                    'start': {
                        'implementation': 'mock.tasks.start',
                        'inputs': {}
                    },
                    'stop': {
                        'implementation': 'mock.tasks.stop',
                        'inputs': {
                            'key': 'value'
                        }
                    }
                }
            }
        }

        actual_merged_interfaces = \
            merge_relationship_type_and_instance_interfaces(
                relationship_type=relationship_type,
                relationship_instance=relationship_instance
            )

        self.assertDictEqual(actual_merged_interfaces,
                             expected_merged_interfaces)
