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
import yaml

from dsl_parser.interfaces_parser import NodeTemplateNodeTypeInterfacesMerger, NodeTypeNodeTypeInterfacesMerger
from dsl_parser.tests.resources.dsl.interfaces import node_template_node_type
from dsl_parser.tests.resources.dsl.interfaces import node_type_node_type
from os import path
from dsl_parser.interfaces_parser import _operation

NO_OP = _operation()


class NodeTemplateNodeTypeInterfacesMergerTest(unittest.TestCase):

    NODE_TEMPLATE_NAME = 'base'
    NODE_TYPE_NAME = 'cloudify.types.base'

    def _assert_interfaces(self,
                           resource_path,
                           expected_interfaces):

        merger = self._create_merger(
            resource_path=resource_path
        )
        result = merger.merge()
        self.assertDictEqual(result, expected_interfaces)

    def _create_merger(self,
                       resource_path,
                       node_template_name=NODE_TEMPLATE_NAME,
                       node_type_name=NODE_TYPE_NAME):

        dir_path = path.dirname(node_template_node_type.__file__)
        full_path = path.join(dir_path, resource_path)

        with open(full_path, mode='r') as f:
            yaml_stream = f.read()

        yaml_dict = yaml.safe_load(yaml_stream)
        node_type = yaml_dict['node_types'][node_type_name]
        node_template = yaml_dict['node_templates'][node_template_name]

        merger = NodeTemplateNodeTypeInterfacesMerger(
            node_template_name=self.NODE_TEMPLATE_NAME,
            node_type=node_type,
            node_template=node_template
        )
        return merger

    def test_different_interfaces(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP,
                'start': _operation(
                    implementation='mock.tasks.start',
                    inputs={'key': 'value'}
                ),
                'stop': _operation(
                    implementation='mock.tasks.stop'
                )
            },
            'cloudify.interfaces.lifecycle2': {
                'create2': NO_OP,
                'start2': _operation(
                    implementation='mock.tasks.start2',
                    inputs={'key2': 'value2'}
                ),
                'stop2': _operation(
                    implementation='mock.tasks.stop2'
                )
            }
        }
        self._assert_interfaces(
            resource_path='different_interfaces.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_interfaces_on_node_template(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP,
                'start': _operation(
                    implementation='mock.tasks.start',
                    inputs={'key': 'value'}
                ),
                'stop': _operation(
                    implementation='mock.tasks.stop'
                )
            }
        }

        self._assert_interfaces(
            resource_path='no_interfaces_on_node_template.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_interfaces_on_node_type(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP,
                'start': _operation(
                    implementation='mock.tasks.start',
                    inputs={'key': 'value'}
                ),
                'stop': _operation(
                    implementation='mock.tasks.stop'
                )
            }
        }

        self._assert_interfaces(
            resource_path='no_interfaces_on_node_type.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_op_merges(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'start': NO_OP,
                'create': NO_OP
            }
        }

        self._assert_interfaces(
            resource_path='no_op_merges.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_op_overrides_no_op(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP
            }
        }

        self._assert_interfaces(
            resource_path='no_op_overrides_no_op.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_op_overrides_operation(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP
            }
        }

        self._assert_interfaces(
            resource_path='no_op_overrides_operation.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_op_overrides_operation_mapping(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': NO_OP
            }
        }

        self._assert_interfaces(
            resource_path='no_op_overrides_operation_mapping.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_mapping_implementation_overrides(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create-overridden',
                    inputs={})
            }
        }

        self._assert_interfaces(
            resource_path='operation_mapping_implementation_overrides.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_mapping_inputs_overrides(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create',
                    inputs={'key': 'value-overridden'})
            }
        }

        self._assert_interfaces(
            resource_path='operation_mapping_inputs_overrides.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_mapping_merges(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create',
                    inputs={'key': 'value'})
                ,
                'start': _operation(
                    implementation='mock.tasks.start',
                    inputs={'key': 'value'})
            }
        }

        self._assert_interfaces(
            resource_path='operation_mapping_merges.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_mapping_overrides_no_op(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create',
                    inputs={'key': 'value'})
            }
        }

        self._assert_interfaces(
            resource_path='operation_mapping_overrides_no_op.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_mapping_overrides_operation(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create-overridden',
                    inputs={'key': 'value'})
            }
        }

        self._assert_interfaces(
            resource_path='operation_mapping_overrides_operation.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_merges(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create'
                ),
                'start': _operation(
                    implementation='mock.tasks.start'
                )
            }
        }

        self._assert_interfaces(
            resource_path='operation_merges.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_overrides_no_op(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create'
                )
            }
        }

        self._assert_interfaces(
            resource_path='operation_overrides_no_op.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_overrides_operation(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create-overridden'
                )
            }
        }

        self._assert_interfaces(
            resource_path='operation_overrides_operation.yaml',
            expected_interfaces=expected_interfaces)

    def test_operation_overrides_operation_mapping(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'create': _operation(
                    implementation='mock.tasks.create-overridden'
                )
            }
        }

        self._assert_interfaces(
            resource_path='operation_overrides_operation_mapping.yaml',
            expected_interfaces=expected_interfaces)


class NodeTypeNodeTypeInterfacesMergerTest(unittest.TestCase):

    OVERRIDDEN_NODE_TYPE_NAME = 'cloudify.types.base1'
    OVERRIDING_NODE_TYPE_NAME = 'cloudify.types.base2'

    def _assert_interfaces(self,
                           resource_path,
                           expected_interfaces):

        merger = self._create_merger(
            resource_path=resource_path
        )
        result = merger.merge()
        self.assertDictEqual(result, expected_interfaces)

    def _create_merger(self,
                       resource_path,
                       overriding_node_type_name=OVERRIDING_NODE_TYPE_NAME,
                       overridden_node_type_name=OVERRIDDEN_NODE_TYPE_NAME):

        dir_path = path.dirname(node_type_node_type.__file__)
        full_path = path.join(dir_path, resource_path)

        with open(full_path, mode='r') as f:
            yaml_stream = f.read()

        yaml_dict = yaml.safe_load(yaml_stream)
        overriding_node_type = yaml_dict['node_types'][overriding_node_type_name]
        overridden_node_type = yaml_dict['node_types'][overridden_node_type_name]

        merger = NodeTypeNodeTypeInterfacesMerger(
            overriding_node_type=overriding_node_type,
            overridden_node_type=overridden_node_type
        )

        return merger

    def test_no_interfaces(self):
        pass

    def test_different_interfaces(self):
        pass

    def test_no_op_merges(self):

        expected_interfaces = {
            'cloudify.interfaces.lifecycle': {
                'start': NO_OP,
                'create': NO_OP
            }
        }

        self._assert_interfaces(
            resource_path='no_op_merges.yaml',
            expected_interfaces=expected_interfaces)

    def test_no_op_overrides_no_op(self):
        pass

    def test_no_op_overrides_operation(self):
        pass

    def test_no_op_overrides_operation_mapping(self):
        pass

    def test_operation_merges(self):
        pass

    def test_operation_overrides_no_op(self):
        pass

    def test_operation_overrides_operation(self):
        pass

    def test_operation_overrides_operation_mapping(self):
        pass

    def test_operation_mapping_merges(self):
        pass

    def test_operation_mapping_overrides_no_op(self):
        pass

    def test_operation_mapping_overrides_operation(self):
        pass

    def test_operation_mapping_overrides_operation_mapping(self):
        pass
