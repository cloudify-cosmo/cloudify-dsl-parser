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

NO_OP = {
    'operation': '',
    'plugin': '',
    'inputs': {}
}


def get_operation(dsl, operation_name):

    """
    Extracts the operation with the given name
    from the parsed DSL.

    :param dsl: The parsed dsl.
    :param operation_name: The operation name.
    :return: The operation with the given name.
    :rtype: dict
    """

    return dsl['nodes'][0]['operations'][operation_name]


class TestInterfacesMerge(unittest.TestCase):

    """
    Test case for various interface merges.
    """

    def _parse(self, name):
        return utils.parse_dsl_resource(
            os.path.join('interfaces', name)
        )


class TestMergeNodeTemplateWithNodeType(TestInterfacesMerge):

    def _parse(self, name):
        return super(TestMergeNodeTemplateWithNodeType,
                     self)._parse(os.path.join('node_template_node_type',
                                               name))

    def test_no_op_merges_no_op(self):
        dsl = self._parse('no_op_merges_no_op.yaml')

        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_non_existing_interface(self):
        dsl = self._parse('no_op_merges_non_existing_interface.yaml')

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

        actual_create2_operation = get_operation(dsl, 'create2')
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_no_op_merges_non_existing_interfaces(self):
        dsl = self._parse('no_op_merges_non_existing_interfaces.yaml')

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_operation(self):
        dsl = self._parse('no_op_merges_operation.yaml')

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_operation_mapping(self):
        dsl = self._parse('no_op_merges_operation_mapping.yaml')

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_no_op(self):
        dsl = self._parse('no_op_overrides_no_op.yaml')

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_operation(self):
        dsl = self._parse('no_op_overrides_operation.yaml')

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_operation_mapping(self):
        dsl = self._parse('no_op_overrides_operation_mapping.yaml')

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_non_existing_interfaces_merges_no_op(self):
        dsl = self._parse('non_existing_interfaces_merges_no_op.yaml')
        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_non_existing_interfaces_merges_non_existing_interfaces(self):
        dsl = self._parse('non_existing_interfaces_merges_non_existing_interfaces.yaml')
        self.assertEqual(dsl['nodes'][0]['operations'], {})

    def test_non_existing_interfaces_merges_operation(self):
        dsl = self._parse('non_existing_interfaces_merges_operation.yaml')
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_non_existing_interfaces_merges_operation_mapping(self):
        dsl = self._parse('non_existing_interfaces_merges_operation_mapping.yaml')
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_operation_mapping_merges_no_op(self):
        dsl = self._parse(
            'operation_mapping_merges_no_op.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_non_existing_interface(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = get_operation(dsl, 'create2')
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_operation_mapping_merges_non_existing_interfaces(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_operation(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_operation.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_operation_mapping.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_no_op(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_no_op.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_operation(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_operation.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_operation_mapping.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value-overridden'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_no_op(self):
        dsl = self._parse(
            'operation_merges_no_op.yaml'
        )
        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_non_existing_interface(self):  # NOQA

        dsl = self._parse(
            'operation_merges_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = get_operation(dsl, 'create2')
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_operation_merges_non_existing_interfaces(self):  # NOQA

        dsl = self._parse(
            'operation_merges_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_operation(self):  # NOQA

        dsl = self._parse(
            'operation_merges_operation.yaml'
        )
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_merges_operation_mapping.yaml'  # NOQA
        )
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_overrides_no_op_of(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_no_op.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_overrides_operation(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_operation.yaml'
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_overrides_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)


class TestMergeNodeTypeWithNodeType(TestInterfacesMerge):

    def _parse(self, name):
        return super(TestMergeNodeTypeWithNodeType,
                     self)._parse(os.path.join('node_type_node_type',
                                               name))

    def test_no_op_merges_no_op(self):
        dsl = self._parse(
            'no_op_merges_no_op.yaml'  # NOQA
        )
        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_non_existing_interface(self):
        dsl = self._parse(
            'no_op_merges_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = get_operation(dsl, 'create2')
        self.assertEqual(actual_create2_operation, NO_OP)

    def test_no_op_merges_non_existing_interfaces(self):
        dsl = self._parse(
            'no_op_merges_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_operation(self):
        dsl = self._parse(
            'no_op_merges_operation.yaml'  # NOQA
        )
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_merges_operation_mapping(self):
        dsl = self._parse(
            'no_op_merges_operation_mapping.yaml'  # NOQA
        )
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_no_op(self):
        dsl = self._parse(
            'no_op_overrides_no_op.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_operation(self):
        dsl = self._parse(
            'no_op_overrides_operation.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_no_op_overrides_operation_mapping(self):
        dsl = self._parse(
            'no_op_overrides_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        self.assertEqual(actual_create_operation, NO_OP)

    def test_non_existing_interfaces_merges_existing_interfaces(self):
        dsl = self._parse(
            'non_existing_interfaces_merges_existing_interfaces.yaml'  # NOQA
        )
        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_non_existing_interfaces_merges_non_existing_interfaces(self):
        dsl = self._parse(
            'non_existing_interfaces_merges_non_existing_interfaces.yaml'  # NOQA
        )
        operations = dsl['nodes'][0]['operations']
        self.assertEqual(operations, {})

    def test_operation_mapping_merges_no_op(self):
        dsl = self._parse(
            'operation_mapping_merges_no_op.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_non_existing_interface(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = get_operation(dsl, 'create2')
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_operation_mapping_merges_non_existing_interfaces(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_operation(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_operation.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_merges_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_merges_operation_mapping.yaml'  # NOQA
        )

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_no_op(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_no_op.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_operation(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_operation.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_mapping_overrides_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_mapping_overrides_operation_mapping.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value-overridden'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_no_op(self):
        dsl = self._parse(
            'operation_merges_no_op.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = get_operation(dsl, 'start')
        self.assertEqual(actual_start_operation, NO_OP)

    def test_operation_merges_non_existing_interface(self):  # NOQA

        dsl = self._parse(
            'operation_merges_non_existing_interface.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_create2_operation = get_operation(dsl, 'create2')
        expected_create2_operation = {
            'operation': 'tasks.create2',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create2_operation, expected_create2_operation)

    def test_operation_merges_non_existing_interfaces(self):  # NOQA

        dsl = self._parse(
            'operation_merges_non_existing_interfaces.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_merges_operation(self):  # NOQA

        dsl = self._parse(
            'operation_merges_operation.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_operation_merges_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_merges_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

        actual_start_operation = get_operation(dsl, 'start')
        expected_start_operation = {
            'operation': 'tasks.start',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_start_operation, expected_start_operation)

    def test_operation_overrides_no_op(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_no_op.yaml'  # NOQA
        )

        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_overrides_operation(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_operation.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {}
        }
        self.assertEqual(actual_create_operation, expected_create_operation)

    def test_operation_overrides_operation_mapping(self):  # NOQA

        dsl = self._parse(
            'operation_overrides_operation_mapping.yaml'  # NOQA
        )
        actual_create_operation = get_operation(dsl, 'create')
        expected_create_operation = {
            'operation': 'tasks.create-overridden',
            'plugin': 'mock',
            'inputs': {
                'key': 'value'
            }
        }
        self.assertEqual(actual_create_operation, expected_create_operation)
