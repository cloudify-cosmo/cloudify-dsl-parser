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

import copy
from collections import OrderedDict

from dsl_parser.constants import INTERFACES
from dsl_parser import utils


def _operation(implementation=None,
               inputs=None):
    return {
        'implementation': implementation or '',
        'inputs': inputs or {}
    }


NO_OP = _operation()


class NodeTemplateNodeTypeInterfaceOperationMerger(object):

    def __init__(self,
                 node_template_name,
                 operation_name,
                 node_type_operation,
                 node_template_operation):

        """
        :param node_template_name: The node template name.
        :param node_type_operation: The node type operation.
        :param node_template_operation: The node template operation.

        """

        self.node_template_name = node_template_name
        self.operation_name = operation_name
        self.node_type_operation = self._create_operation(node_type_operation)
        self.node_template_operation = self._create_operation(node_template_operation)

    @staticmethod
    def _create_operation(operation):
        if operation is None:
            return None
        if isinstance(operation, str):
            return _operation(
                implementation=operation,
                inputs={}
            )
        if isinstance(operation, dict):
            return _operation(
                implementation=operation.get('implementation', ''),
                inputs=operation.get('inputs', {})
            )
        raise TypeError('Operation is of an unsupported type --> {0}'
                        .format(type(operation)))

    def _derive_implementation(self):
        merged_operation_implementation = self.node_template_operation['implementation']
        if not merged_operation_implementation:
            # node template does not define an implementation
            # this means we want to inherit the implementation
            # from the type
            merged_operation_implementation = self.node_type_operation['implementation']
        return merged_operation_implementation

    def _derive_inputs(self, merged_operation_implementation):
        if merged_operation_implementation == self.node_type_operation['implementation']:
            # this means the node template inputs should adhere to
            # the node type inputs schema (since its the same implementation)
            merged_operation_inputs = utils.merge_schema_and_instance_properties(
                instance_properties=self.node_template_operation['inputs'],
                impl_properties={},
                schema_properties=self.node_type_operation['inputs'],
                undefined_property_error_message=None,
                missing_property_error_message=None,
                node_name=self.node_template_name,
                is_interface_inputs=True
            )
        else:
            # the node template implementation overrides
            # the node type implementation. this means
            # we take the inputs defined in the node template
            merged_operation_inputs = self.node_template_operation['inputs']

        return merged_operation_inputs

    def merge(self):

        """
        Merges a node template interface operation with
        a node type interface operation.
        Node template operation will override in case
        of conflict.

        :return The merged operation.
        :rtype dict
        """

        if self.node_type_operation is None:

            # the operation is not defined in the type
            # should be merged by the node template operation

            return self._create_operation(self.node_template_operation)

        if self.node_template_operation is None:

            # the operation is not defined in the template
            # should be merged by the node type operation

            return _operation(
                implementation=self.node_type_operation['implementation'],
                inputs=utils.merge_schema_and_instance_properties(
                    instance_properties={},
                    impl_properties={},
                    schema_properties=self.node_type_operation['inputs'],
                    undefined_property_error_message=None,
                    missing_property_error_message=None,
                    node_name=self.node_template_name,
                    is_interface_inputs=True
                )
            )

        if self.node_template_operation == NO_OP:
            # no-op overrides
            return _operation()
        if self.node_type_operation == NO_OP:
            # no-op overridden
            return self.node_template_operation

        merged_operation_implementation = self._derive_implementation()
        merged_operation_inputs = self._derive_inputs(merged_operation_implementation)

        return _operation(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs
        )


class NodeTemplateNodeTypeInterfaceMerger(object):

    def __init__(self,
                 node_template_name,
                 interface_name,
                 node_type_interface,
                 node_template_interface):

        """
        :param node_template_name: The node template name.
        :param interface_name: The interface name.
        :param node_type_interface: The node type interface.
        :param node_template_interface: The node template interface.
        """

        self.node_template_name = node_template_name
        self.interface_name = interface_name
        self.node_type_interface = node_type_interface
        self.node_template_interface = node_template_interface

    def merge(self):

        """
        Merges a node template interface with
        a node type interface.

        :return: The merged interface.
        :rtype dict
        """

        merged_interface = {}

        for node_type_operation_name, node_type_operation in self.node_type_interface.items():

            node_template_operation = self.node_template_interface.get(
                node_type_operation_name,
                None)

            operation_merger = NodeTemplateNodeTypeInterfaceOperationMerger(
                node_template_name=self.node_template_name,
                operation_name=node_type_operation_name,
                node_type_operation=node_type_operation,
                node_template_operation=node_template_operation)
            merged_operation = operation_merger.merge()
            merged_interface[node_type_operation_name] = merged_operation

        for node_template_operation_name, node_template_operation in self.node_template_interface.items():

            node_type_operation = self.node_type_interface.get(
                node_template_operation_name,
                None)

            operation_merger = NodeTemplateNodeTypeInterfaceOperationMerger(
                node_template_name=self.node_template_name,
                operation_name=node_template_operation_name,
                node_type_operation=node_type_operation,
                node_template_operation=node_template_operation)
            merged_operation = operation_merger.merge()
            merged_interface[node_template_operation_name] = merged_operation

        return merged_interface


class NodeTemplateNodeTypeInterfacesMerger(object):

    def __init__(self,
                 node_template_name,
                 node_type,
                 node_template):

        """
        :param node_template_name: The node template name.
        :param node_type: The node type.
        :param node_template: The node template.
        """

        self.node_template = copy.deepcopy(node_template)
        self.node_template.setdefault(INTERFACES, {})
        self.node_type = copy.deepcopy(node_type)
        self.node_type.setdefault(INTERFACES, {})
        self.node_template_name = node_template_name

    def merge(self):

        """
        Merges node template 'interfaces' section with
        a node type 'interfaces' section.

        :return: The merged interfaces.
        :rtype dict
        """

        merged_interfaces = {}

        for node_type_interface_name, node_type_interface in self.node_type[INTERFACES].items():

            node_template_interface = self.node_template[
                INTERFACES].get(node_type_interface_name, {})

            interface_merger = NodeTemplateNodeTypeInterfaceMerger(
                node_template_name=self.node_template_name,
                interface_name=node_type_interface_name,
                node_type_interface=node_type_interface,
                node_template_interface=node_template_interface
            )
            merged_interface = interface_merger.merge()
            merged_interfaces[node_type_interface_name] = merged_interface

        for node_template_interface_name, node_template_interface in self.node_template[INTERFACES].items():

            node_type_interface = self.node_type[
                INTERFACES].get(node_template_interface_name, {})

            interface_merger = NodeTemplateNodeTypeInterfaceMerger(
                node_template_name=self.node_template_name,
                interface_name=node_template_interface_name,
                node_type_interface=node_type_interface,
                node_template_interface=node_template_interface
            )
            merged_interface = interface_merger.merge()
            merged_interfaces[node_template_interface_name] = merged_interface

        return merged_interfaces


class NodeTypeNodeTypeInterfaceOperationMerger(object):

    def __init__(self,
                 overriding_node_type_operation,
                 overridden_node_type_operation):

        """
        :param overriding_node_type_operation: The overriding node type operation.
        :param overridden_node_type_operation: The overridden node type operation.

        """

        self.overriding_node_type_operation = overriding_node_type_operation
        self.overridden_node_type_operation = overridden_node_type_operation

    def merge(self):
        if isinstance(self.overriding_node_type_operation, dict) and \
                isinstance(self.overridden_node_type_operation, dict):
            if not self.overriding_node_type_operation:
                # no-op overriding
                return self.overriding_node_type_operation
            return {
                'implementation': self.overriding_node_type_operation.get('implementation', ''),
                'inputs': utils.merge_sub_dicts(
                    overridden_dict=self.overridden_node_type_operation,
                    overriding_dict=self.overriding_node_type_operation,
                    sub_dict_key='inputs'
                )
            }
        if isinstance(self.overriding_node_type_operation, str) and \
                isinstance(self.overridden_node_type_operation, str):
            return {
                'implementation': self.overriding_node_type_operation or self.overridden_node_type_operation,
                'inputs': {}
            }

        if isinstance(self.overriding_node_type_operation, str):

            return {
                'implementation': self.overriding_node_type_operation,
                'inputs': utils.merge_sub_dicts(
                    overridden_dict=self.overridden_node_type_operation,
                    overriding_dict={},
                    sub_dict_key='inputs'
                )
            }

        if isinstance(self.overridden_node_type_operation, str):

            return {
                'implementation': self.overriding_node_type_operation.get('implementation', ''),
                'inputs': utils.merge_sub_dicts(
                    overridden_dict={},
                    overriding_dict=self.overriding_node_type_operation,
                    sub_dict_key='inputs'
                )
            }


class NodeTypeNodeTypeInterfaceMerger(object):

    def __init__(self,
                 overriding_node_type_interface,
                 overridden_node_type_interface):

        """
        :param overriding_node_type_interface: The overriding node type interface.
        :param overridden_node_type_interface: The overridden node type interface.

        """

        self.overriding_node_type_interface = overriding_node_type_interface
        self.overridden_node_type_interface = overridden_node_type_interface

    def merge(self):

        def op_and_op_name(op):
            key = op[0]
            value = op[1]
            return key, value

        # OrderedDict for easier testability
        overridden = OrderedDict((x, y) for x, y in map(
            op_and_op_name,
            self.overridden_node_type_interface.items()))
        overriding = OrderedDict((x, y) for x, y in map(
            op_and_op_name,
            self.overriding_node_type_interface.items()))
        result = {}
        for op_name, operation in overridden.items():
            if op_name not in overriding:
                result[op_name] = operation
            else:

                overriding_op = overriding[op_name]
                overridden_op = overridden[op_name]

                merger = NodeTypeNodeTypeInterfaceOperationMerger(
                    overridden_node_type_operation=overridden_op,
                    overriding_node_type_operation=overriding_op
                )
                result[op_name] = merger.merge()

        for op_name, operation in overriding.items():
            if op_name not in overridden:
                result[op_name] = operation
        return result


class NodeTypeNodeTypeInterfacesMerger(object):

    def __init__(self,
                 overriding_node_type,
                 overridden_node_type):

        """
        :param overriding_node_type: The overriding node type.
        :param overridden_node_type: The overridden node type.

        """

        self.overriding_node_type = copy.deepcopy(overriding_node_type)
        self.overriding_node_type.setdefault(INTERFACES, {})
        self.overridden_node_type = copy.deepcopy(overridden_node_type)
        self.overridden_node_type.setdefault(INTERFACES, {})

    def merge(self):
        merged_interfaces = self.overridden_node_type[INTERFACES]
        for overriding_interface_name, overriding_interface in self.overriding_node_type[INTERFACES].items():
            if overriding_interface_name not in self.overridden_node_type[INTERFACES]:
                merged_interfaces[overriding_interface_name] = overriding_interface
            else:
                merger = NodeTypeNodeTypeInterfaceMerger(
                    overridden_node_type_interface=self.overridden_node_type[INTERFACES][overriding_interface_name],
                    overriding_node_type_interface=overriding_interface
                )
                merged_interfaces[overriding_interface_name] = merger.merge()
        return merged_interfaces


def merge_node_type_and_node_template_interfaces(
        node_name,
        complete_type,
        node):

    merger = NodeTemplateNodeTypeInterfacesMerger(
        node_type=complete_type,
        node_template=node,
        node_template_name=node_name)

    node_with_interfaces = copy.deepcopy(node)
    node_with_interfaces[INTERFACES] = merger.merge()
    return node_with_interfaces


def merge_node_type_and_node_type_interfaces(overriding_node_type,
                                             overridden_node_type):

    merger = NodeTypeNodeTypeInterfacesMerger(
        overriding_node_type=overriding_node_type,
        overridden_node_type=overridden_node_type
    )
    return merger.merge()
