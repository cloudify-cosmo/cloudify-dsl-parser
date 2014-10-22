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

from dsl_parser.interfaces.constants import NO_OP
from dsl_parser.interfaces.utils import operation_mapping
from dsl_parser.interfaces.operation_merger import \
    NodeTemplateNodeTypeOperationMerger
from dsl_parser.interfaces.operation_merger import \
    NodeTypeNodeTypeOperationMerger
from dsl_parser.schemas import NODE_TEMPLATE_OPERATION_SCHEMA
from dsl_parser.schemas import NODE_TYPE_OPERATION_SCHEMA


class NodeTemplateNodeTypeOperationMergerTest(testtools.TestCase):

    def _assert_operations(self,
                           node_template_operation,
                           node_type_operation,
                           expected_merged_operation):

        if node_template_operation is not None:
            validate(node_template_operation, NODE_TEMPLATE_OPERATION_SCHEMA)
        if node_type_operation is not None:
            validate(node_type_operation, NODE_TYPE_OPERATION_SCHEMA)

        merger = NodeTemplateNodeTypeOperationMerger(
            overriding_operation=node_template_operation,
            overridden_operation=node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertDictEqual(expected_merged_operation,
                                 actual_merged_operation)

    def test_no_op_overrides_no_op(self):

        node_template_operation = {}
        node_type_operation = {}
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


class NodeTypeNodeTypeOperationMergerTest(testtools.TestCase):

    def _assert_operations(self,
                           overriding_node_type_operation,
                           overridden_node_type_operation,
                           expected_merged_operation):

        if overriding_node_type_operation is not None:
            validate(overriding_node_type_operation,
                     NODE_TYPE_OPERATION_SCHEMA)
        if overridden_node_type_operation is not None:
            validate(overridden_node_type_operation,
                     NODE_TYPE_OPERATION_SCHEMA)

        merger = NodeTypeNodeTypeOperationMerger(
            overriding_operation=overriding_node_type_operation,
            overridden_operation=overridden_node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertDictEqual(expected_merged_operation,
                                 actual_merged_operation)

    def test_no_op_overrides_no_op(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = {}
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create'
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_none(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = None
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_no_op(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        overridden_node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            })

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = operation_mapping(
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
                'key': {
                    'default': 'value-overridden'
                }
            })

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            })

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_none(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        overridden_node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            })

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_no_op(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = {}

        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_none(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = None

        expected_merged_operation = None

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_no_op(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create'
        )
        overridden_node_type_operation = NO_OP

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={}
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={}
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_none(self):

        overriding_node_type_operation = operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={}
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )
