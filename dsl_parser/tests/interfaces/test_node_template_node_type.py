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

import unittest
from jsonschema import validate

from dsl_parser.interfaces.interfaces_parser import NO_OP
from dsl_parser.interfaces.interfaces_parser import operation_mapping
from dsl_parser.interfaces.merging import OperationMerger, InterfaceMerger
from dsl_parser.interfaces.node_template_node_type import NodeTemplateNodeTypeInterfaceOperationMerger
from dsl_parser.interfaces.node_template_node_type import NodeTemplateNodeTypeInterfaceMerger
from dsl_parser.interfaces.node_template_node_type import NodeTemplateNodeTypeInterfacesMerger
from dsl_parser.schemas import NODE_TEMPLATE_OPERATION_SCHEMA
from dsl_parser.schemas import NODE_TYPE_OPERATION_SCHEMA


class NodeTemplateNodeTypeOperationMergerTest(unittest.TestCase):

    NODE_TEMPLATE_NAME = 'base'
    NODE_TYPE_NAME = 'cloudify.types.base'

    def _assert_operations(self,
                           node_template_operation,
                           node_type_operation,
                           expected_merged_operation):

        if node_template_operation is not None:
            validate(node_template_operation, NODE_TEMPLATE_OPERATION_SCHEMA)
        if node_type_operation is not None:
            validate(node_type_operation, NODE_TYPE_OPERATION_SCHEMA)

        merger = NodeTemplateNodeTypeInterfaceOperationMerger(
            overriding_operation=node_template_operation,
            overridden_operation=node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertDictEqual(expected_merged_operation, actual_merged_operation)

    def test_no_op_overrides_no_op(self):

        node_template_operation = {}
        node_type_operation = {}
        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation(self):

        node_template_operation = {}
        node_type_operation = 'mock.tasks.create'
        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping(self):

        node_template_operation = {}
        node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_none(self):

        node_template_operation = {}
        node_type_operation = None

        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_no_op(self):

        node_template_operation = 'mock.tasks.create'
        node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation(self):

        node_template_operation = 'mock.tasks.create-overridden'
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping(self):

        node_template_operation = 'mock.tasks.create-overridden'
        node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_none(self):

        node_template_operation = 'mock.tasks.create'
        node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_no_op(self):

        node_template_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            }
        )
        node_type_operation = {}
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={'key': 'value'})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation(self):

        node_template_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            }
        )
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={'key': 'value'})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping(self):

        node_template_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value-overridden'
            }

        )
        node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value-overridden'
            })

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_none(self):

        node_template_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            }
        )
        node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            }
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_inputs_overrides(self):

        node_template_operation = operation_mapping(
            inputs={
                'key': 'value-overridden'
            }
        )
        node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={'key': 'value-overridden'})

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_no_op(self):

        node_template_operation = None
        node_type_operation = {}

        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation(self):

        node_template_operation = None
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping(self):

        node_template_operation = None
        node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            }
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_none(self):

        node_template_operation = None
        node_type_operation = None

        expected_merged_operation = None

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )


class NodeTemplateNodeTypeInterfaceMergerTest(unittest.TestCase):

    def _assert_interface(self,
                          overriding_interface,
                          overridden_interface,
                          expected_merged_interface_keys):

        class MockOperationMerger(OperationMerger):

            def merge(self):
                return None

        merger = NodeTemplateNodeTypeInterfaceMerger(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface
        )
        merger.operation_merger = MockOperationMerger
        actual_merged_interface_keys = set(merger.merge().keys())
        self.assertEqual(expected_merged_interface_keys, actual_merged_interface_keys)

    def test_merge_operations(self):

        overriding_interface = {
            'stop': None
        }
        overridden_interface = {
            'start': None
        }

        expected_merged_interface_keys = {'stop', 'start'}

        self._assert_interface(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            expected_merged_interface_keys=expected_merged_interface_keys
        )

    def test_override_operation(self):

        overriding_interface = {
            'stop': None
        }
        overridden_interface = {
            'stop': None
        }

        expected_merged_interface_keys = {'stop'}

        self._assert_interface(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            expected_merged_interface_keys=expected_merged_interface_keys
        )


class NodeTemplateNodeTypeInterfacesMergerTest(unittest.TestCase):

    def _assert_interfaces(self,
                           overriding_interfaces,
                           overridden_interfaces,
                           expected_merged_interfaces_keys):

        class MockOperationMerger(OperationMerger):

            def merge(self):
                return None

        class MockInterfaceMerger(InterfaceMerger):

            def __init__(self,
                         overriding_interface,
                         overridden_interface):
                super(MockInterfaceMerger, self).__init__(
                    overriding_interface=overriding_interface,
                    overridden_interface=overridden_interface,
                    operation_merger=MockOperationMerger)

            def merge(self):
                return None

        merger = NodeTemplateNodeTypeInterfacesMerger(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
        )
        merger.interface_merger = MockInterfaceMerger
        actual_merged_interfaces_keys = merger.merge().keys()
        self.assertEqual(expected_merged_interfaces_keys, actual_merged_interfaces_keys)

    def test_merge_interfaces(self):

        overriding_interfaces = {
            'interface1': None
        }
        overridden_interfaces = {
            'interface2': None
        }

        expected_merged_interfaces_keys = ['interface1', 'interface2']
        self._assert_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            expected_merged_interfaces_keys=expected_merged_interfaces_keys
        )

    def test_override_interface(self):

        overriding_interfaces = {
            'interface1': None
        }
        overridden_interfaces = {
            'interface1': None
        }

        expected_merged_interfaces_keys = ['interface1']
        self._assert_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            expected_merged_interfaces_keys=expected_merged_interfaces_keys
        )
