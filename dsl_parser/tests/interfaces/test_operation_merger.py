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
from dsl_parser.interfaces.utils import operation_mapping
from dsl_parser.interfaces.operation_merger import \
    NodeTemplateNodeTypeOperationMerger
from dsl_parser.interfaces.operation_merger import \
    NodeTypeNodeTypeOperationMerger
from dsl_parser.elements import operation

from dsl_parser.tests.interfaces import validate


def raw_operation_mapping(implementation=None,
                          inputs=None,
                          executor=None,
                          max_retries=None,
                          retry_interval=None):

    """
    Used to simulate a possible operation written in
    the blueprint.
    """

    result = {}
    if implementation is not None:
        result['implementation'] = implementation
    if inputs is not None:
        result['inputs'] = inputs
    if executor is not None:
        result['executor'] = executor
    if max_retries is not None:
        result['max_retries'] = max_retries
    if retry_interval is not None:
        result['retry_interval'] = retry_interval
    return result


class NodeTemplateNodeTypeOperationMergerTest(testtools.TestCase):

    def _assert_operations(self,
                           node_template_operation,
                           node_type_operation,
                           expected_merged_operation):

        if node_template_operation is not None:
            validate(node_template_operation, operation.NodeTemplateOperation)
        if node_type_operation is not None:
            validate(node_type_operation, operation.NodeTypeOperation)

        merger = NodeTemplateNodeTypeOperationMerger(
            overriding_operation=node_template_operation,
            overridden_operation=node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertEqual(expected_merged_operation,
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
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping_no_inputs(self):

        node_template_operation = {}
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
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

    def test_no_op_overrides_operation_mapping_with_executor(self):

        node_template_operation = {}
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
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

    def test_operation_overrides_no_op(self):

        node_template_operation = 'mock.tasks.create'
        node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping(self):

        node_template_operation = 'mock.tasks.create-overridden'
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_no_inputs(self):

        node_template_operation = 'mock.tasks.create-overridden'
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None)

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
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_with_executor(self):

        node_template_operation = 'mock.tasks.create-overridden'
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None)

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
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_no_op(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            }
        )
        node_type_operation = {}
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={'key': 'value'},
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value-overridden'
            }

        )
        node_type_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):
        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            }

        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_none(self):

        node_template_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_executor(self):
        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            }

        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            }

        )
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': 'value'
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

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
        node_type_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping_no_inputs(self):
        node_template_operation = None
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
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

    def test_none_overrides_operation_mapping_with_executor(self):
        node_template_operation = None
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )

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
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_no_op(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent'
        )
        node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_no_inputs(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_none(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
        )
        node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_with_executor(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation(self):

        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent'
        )
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_no_op(self):
        node_template_operation = raw_operation_mapping(
            inputs={},
            executor='host_agent'
        )
        node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_operation_mapping(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            inputs={
                'key': 'value'
            }
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': 'value'
            },
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_operation_mapping_no_inputs(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            inputs={},
            executor='host_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_none(self):

        node_template_operation = raw_operation_mapping(
            inputs={},
            executor='host_agent'
        )
        node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_operation_mapping_with_executor(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            inputs={},
            executor='central_deployment_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_implementation_overrides_operation(self):

        node_template_operation = raw_operation_mapping(
            inputs={},
            executor='central_deployment_agent'
        )
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_no_op(self):
        node_template_operation = raw_operation_mapping(
            executor='host_agent'
        )
        node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            executor='host_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            executor='host_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_none(self):

        node_template_operation = raw_operation_mapping(
            executor='host_agent'
        )
        node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_with_executor(self):  # NOQA

        node_template_operation = raw_operation_mapping(
            executor='central_deployment_agent'
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation(self):

        node_template_operation = raw_operation_mapping(
            executor='central_deployment_agent'
        )
        node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_retry(self):
        node_template_operation = raw_operation_mapping(
            inputs={'some': 'input'}
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={'some': 'input'},
            executor=None,
            max_retries=1,
            retry_interval=2
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry(self):  # noqa
        node_template_operation = raw_operation_mapping(
            max_retries=3,
            retry_interval=4
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=3,
            retry_interval=4
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry_zero_values(self):  # noqa
        node_template_operation = raw_operation_mapping(
            max_retries=0,
            retry_interval=0
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=0,
            retry_interval=0
        )
        self._assert_operations(
            node_template_operation=node_template_operation,
            node_type_operation=node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_impl_overrides_operation_mapping_with_retry(self):  # noqa
        node_template_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={'some': 'input'}
        )
        node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={'some': 'input'},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
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
                     operation.NodeTypeOperation)
        if overridden_node_type_operation is not None:
            validate(overridden_node_type_operation,
                     operation.NodeTypeOperation)

        merger = NodeTypeNodeTypeOperationMerger(
            overriding_operation=overriding_node_type_operation,
            overridden_operation=overridden_node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertEqual(expected_merged_operation,
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
        overridden_node_type_operation = raw_operation_mapping(
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
        overridden_node_type_operation = raw_operation_mapping(
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

    def test_no_op_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
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
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

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
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
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

    def test_none_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )
        overridden_node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        overridden_node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        overridden_node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='central_deployment_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_no_op(self):

        overriding_node_type_operation = 'mock.tasks.create'
        overridden_node_type_operation = {}

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_none(self):

        overriding_node_type_operation = 'mock.tasks.create'
        overridden_node_type_operation = None

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping(self):

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_retry(self):
        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry(self):  # noqa
        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
            max_retries=3,
            retry_interval=4
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={},
            executor=None,
            max_retries=3,
            retry_interval=4
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )
