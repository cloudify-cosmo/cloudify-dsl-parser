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

import os
import unittest

from dsl_parser.tests import utils


def parse(name):
    return utils.parse_dsl_resource(
        os.path.join('interfaces', name)
    )


class TestInterfaces(unittest.TestCase):

    """
    Test case for various interface semantics.
    """

    def test_node_template_no_op_merges_node_type_no_op(self):
        dsl = parse('node_template_no_op_merges_node_type_no_op.yaml')

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_merges_node_type_non_existing_interface(self):
        dsl = parse('node_template_no_op_merges_node_type_non_existing_interface.yaml')

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_template_no_op_merges_node_type_non_existing_interfaces(self):
        dsl = parse('node_template_no_op_merges_node_type_non_existing_interfaces.yaml')

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_merges_node_type_operation(self):
        dsl = parse('node_template_no_op_merges_node_type_operation.yaml')

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_merges_node_type_operation_mapping(self):
        dsl = parse('node_template_no_op_merges_node_type_operation_mapping.yaml')

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_overrides_node_type_no_op(self):
        dsl = parse('node_template_no_op_overrides_node_type_no_op.yaml')

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_overrides_node_type_operation(self):
        dsl = parse('node_template_no_op_overrides_node_type_operation.yaml')

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_no_op_overrides_node_type_operation_mapping(self):
        dsl = parse('node_template_no_op_overrides_node_type_operation_mapping.yaml')

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)



    def test_node_template_operation_mapping_merges_node_type_no_op(self):
        dsl = parse(
            'node_template_operation_mapping_merges_node_type_no_op.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_merges_node_type_non_existing_interface(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_merges_node_type_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_template_operation_mapping_merges_node_type_non_existing_interfaces(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_merges_node_type_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_merges_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_merges_node_type_operation.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_merges_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_merges_node_type_operation_mapping.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_overrides_no_op_node_type(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_overrides_no_op_node_type.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_overrides_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_overrides_node_type_operation.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_mapping_overrides_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_template_operation_mapping_overrides_node_type_operation_mapping.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value-overridden'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)



    def test_node_template_operation_merges_node_type_no_op(self):
        dsl = parse(
            'node_template_operation_merges_node_type_no_op.yaml'
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_merges_node_type_non_existing_interface(self):  # NOQA

        dsl = parse(
            'node_template_operation_merges_node_type_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_template_operation_merges_node_type_non_existing_interfaces(self):  # NOQA

        dsl = parse(
            'node_template_operation_merges_node_type_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_merges_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_template_operation_merges_node_type_operation.yaml'
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_merges_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_template_operation_merges_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_overrides_no_op_of_node_type(self):  # NOQA

        dsl = parse(
            'node_template_operation_overrides_node_type_no_op.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_overrides_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_template_operation_overrides_node_type_operation.yaml'
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_template_operation_overrides_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_template_operation_overrides_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)



    def test_node_type_no_op_merges_node_type_no_op(self):
        dsl = parse(
            'node_type_no_op_merges_node_type_no_op.yaml'  # NOQA
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_merges_node_type_non_existing_interface(self):
        dsl = parse(
            'node_type_no_op_merges_node_type_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_type_no_op_merges_node_type_non_existing_interfaces(self):
        dsl = parse(
            'node_type_no_op_merges_node_type_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_merges_node_type_operation(self):
        dsl = parse(
            'node_type_no_op_merges_node_type_operation.yaml'  # NOQA
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_merges_node_type_operation_mapping(self):
        dsl = parse(
            'node_type_no_op_merges_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_overrides_no_op_node_type(self):
        dsl = parse(
            'node_type_no_op_overrides_node_type_no_op.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_overrides_node_type_operation(self):
        dsl = parse(
            'node_type_no_op_overrides_node_type_operation.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_no_op_overrides_node_type_operation_mapping(self):
        dsl = parse(
            'node_type_no_op_overrides_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)



    def test_node_type_operation_mapping_merges_node_type_no_op(self):
        dsl = parse(
            'node_type_operation_mapping_merges_node_type_no_op.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_merges_node_type_non_existing_interface(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_merges_node_type_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_type_operation_mapping_merges_node_type_non_existing_interfaces(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_merges_node_type_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_merges_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_merges_node_type_operation.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_merges_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_merges_node_type_operation_mapping.yaml'  # NOQA
        )

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_overrides_no_op_node_type(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_overrides_node_type_no_op.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_overrides_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_overrides_node_type_operation.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_mapping_overrides_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_type_operation_mapping_overrides_node_type_operation_mapping.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value-overridden'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)



    def test_node_type_operation_merges_node_type_no_op(self):
        dsl = parse(
            'node_type_operation_merges_node_type_no_op.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': '',
            'plugin': '',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_node_type_operation_merges_node_type_non_existing_interface(self):  # NOQA

        dsl = parse(
            'node_type_operation_merges_node_type_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = dsl['nodes'][0]['operations']['create2']
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_node_type_operation_merges_node_type_non_existing_interfaces(self):  # NOQA

        dsl = parse(
            'node_type_operation_merges_node_type_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_merges_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_type_operation_merges_node_type_operation.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_node_type_operation_merges_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_type_operation_merges_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = dsl['nodes'][0]['operations']['start']
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_node_type_operation_overrides_no_op_node_type(self):  # NOQA

        dsl = parse(
            'node_type_operation_overrides_node_type_no_op.yaml'  # NOQA
        )

        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_overrides_node_type_operation(self):  # NOQA

        dsl = parse(
            'node_type_operation_overrides_node_type_operation.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_node_type_operation_overrides_node_type_operation_mapping(self):  # NOQA

        dsl = parse(
            'node_type_operation_overrides_node_type_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = dsl['nodes'][0]['operations']['create']
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)