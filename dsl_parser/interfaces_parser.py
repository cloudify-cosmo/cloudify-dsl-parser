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
from dsl_parser.utils import merge_sub_dicts
from dsl_parser.utils import merge_schema_and_instance_properties


def _operation(implementation=None,
               inputs=None):
    return {
        'implementation': implementation or '',
        'inputs': inputs or {}
    }


class NodeTemplateNodeTypeOperationMerger(object):

    def __init__(self,
                 node_name,
                 operation_name,
                 node_type_operation,
                 node_template_operation):

        """
        :param node_name: The node name.
        :param node_type_operation: The node type operation.
        :param node_template_operation: The node template operation.
        """

        self.node_name = node_name
        self.operation_name = operation_name
        self.node_type_operation = node_type_operation
        self.node_template_operation = node_template_operation

    def _merge_operation_mappings(self):

        if not self.node_template_operation:
            # no-op overrides
            return _operation()
        if not self.node_type_operation:
            # no-op overridden
            return self.node_template_operation

        return _operation(
            implementation=self.node_template_operation['implementation'],
            inputs=merge_schema_and_instance_properties(
                instance_properties=self.node_template_operation['inputs'],
                impl_properties={},
                schema_properties=self.node_type_operation['inputs'],
                undefined_property_error_message=None,
                missing_property_error_message=None,
                node_name=self.node_name,
                is_interface_inputs=True
            )
        )

    def _merge_operations(self):
        return _operation(
            implementation=self.node_template_operation,
            inputs={}
        )

    def _merge_mixed_operation(self):

        if self.node_template_operation is None and isinstance(self.node_type_operation, dict):

            return _operation(
                implementation=self.node_type_operation.get('implementation', ''),
                inputs=merge_schema_and_instance_properties(
                    instance_properties={},
                    impl_properties={},
                    schema_properties=self.node_type_operation.get('inputs', {}),
                    undefined_property_error_message=None,
                    missing_property_error_message=None,
                    node_name=self.node_name,
                    is_interface_inputs=True
                )
            )

        if self.node_template_operation is None and isinstance(self.node_type_operation, str):

            return _operation(
                implementation=self.node_type_operation,
                inputs={}
            )

        if isinstance(self.node_template_operation, str):
            # this means the node_type_operation is a dict
            # which means it defines inputs.

            return _operation(
                implementation=self.node_template_operation,
                inputs=merge_schema_and_instance_properties(
                    instance_properties={},
                    impl_properties={},
                    schema_properties=self.node_type_operation.get('inputs', {}),
                    undefined_property_error_message=None,
                    missing_property_error_message=None,
                    node_name=self.node_name,
                    is_interface_inputs=True
                )
            )

        if isinstance(self.node_type_operation, str):

            return _operation(
                implementation=self.node_template_operation.get('implementation', ''),
                inputs=self.node_template_operation.get('inputs', {})
            )

    def merge(self):

        """
        Merges a node template operation with
        a node type operation.
        Node template operation will override in case
        of conflict.

        :return The merged operation.
        :rtype dict
        """

        # 1. both operations are operation mappings
        if isinstance(self.node_type_operation, dict) and \
                isinstance(self.node_template_operation, dict):
            return self._merge_operation_mappings()

        # 2. both operations are operations
        if isinstance(self.node_type_operation, str) and \
                isinstance(self.node_template_operation, str):
            return self._merge_operations()

        # 3. mixed
        return self._merge_mixed_operation()


class NodeTemplateNodeTypeInterfaceMerger(object):

    def __init__(self,
                 node_name,
                 interface_name,
                 node_type_interface,
                 node_template_interface):

        """
        :param node_name: The node name.
        :param interface_name: The interface name.
        :param node_type_interface: The node type interface.
        :param node_template_interface: The node template interface.
        """

        self.node_name = node_name
        self.interface_name = interface_name
        self.node_type_interface = node_type_interface
        self.node_template_interface = node_template_interface

        self._merged_interface = {}

    def merge(self):

        """
        Merges a node template interface with
        a node type interface.

        :return: The merged interface.
        :rtype dict
        """

        for node_type_operation_name, node_type_operation \
                in self.node_type_interface.items():

            if node_type_operation_name not in self.node_template_interface:

                # operation is defined in the type but
                # is not defined in the template.
                # set the operation on the template as None,
                # indicating that it doesn't really exist.

                self.node_template_interface[node_type_operation_name] = None

            node_template_operation = self.node_template_interface[node_type_operation_name]

            operation_merger = NodeTemplateNodeTypeOperationMerger(
                node_name=self.node_name,
                operation_name=node_type_operation_name,
                node_type_operation=node_type_operation,
                node_template_operation=node_template_operation)
            merged_operation = operation_merger.merge()
            self._merged_interface[node_type_operation_name] = merged_operation

        return self._merged_interface


class NodeTemplateNodeTypeInterfacesMerger(object):

    def __init__(self, node_type, node_template, node_name):

        """
        :param node_name: The node name.
        :param node_type: The node type.
        :param node_template: The node template.
        """

        self.node_template = copy.deepcopy(node_template)
        self.node_template.setdefault(INTERFACES, {})
        self.node_type = copy.deepcopy(node_type)
        self.node_type.setdefault(INTERFACES, {})
        self.node_name = node_name

        self._merged_interfaces = {}

    def _merge_type_interfaces_to_complete_node(self):

        for node_type_interface_name, node_type_interface \
                in self.node_type[INTERFACES].items():

            if node_type_interface_name not in self.node_template[INTERFACES]:

                # interface exists in the type but doesnt
                # exist in the template.
                # the complete node will have this interface
                # so we can treat the complete node as if
                # it defined this interface empty.

                self.node_template[INTERFACES][node_type_interface_name] = {}
                
            node_template_interface = self.node_template[
                INTERFACES][node_type_interface_name]

            interface_merger = NodeTemplateNodeTypeInterfaceMerger(
                node_name=self.node_name,
                interface_name=node_type_interface_name,
                node_type_interface=node_type_interface,
                node_template_interface=node_template_interface
            )
            merged_interface = interface_merger.merge()
            self._merged_interfaces[node_type_interface_name] = merged_interface

    def _merge_template_interfaces_to_complete_node(self):

        def augment_operation(op):
            if isinstance(op, str):
                return _operation(
                    implementation=op,
                    inputs={}
                )
            if isinstance(op, dict):
                return _operation(
                    implementation=op.get('implementation', ''),
                    inputs=op.get('inputs', {})
                )

        for interface_name, interface in self.node_template[INTERFACES].items():
            if interface_name not in self._merged_interfaces:
                self._merged_interfaces[interface_name] = {}
                for operation_name, operation in interface.items():
                    self._merged_interfaces[interface_name][operation_name] \
                        = augment_operation(operation)
            else:
                # interface exists
                # check per operation
                for operation_name, operation in interface.items():
                    if operation_name not in \
                            self._merged_interfaces[interface_name]:
                        self._merged_interfaces[interface_name][operation_name] \
                            = augment_operation(operation)

    def merge(self):

        """
        Merges node template 'interfaces' section with
        a node type 'interfaces' section.

        :return: The merged interfaces.
        :rtype dict
        """

        # iterate over the type interfaces and merge
        # them to the result (complete_node)
        self._merge_type_interfaces_to_complete_node()

        # iterate over the template interfaces and merge
        # them to the result (complete_node)
        self._merge_template_interfaces_to_complete_node()

        return self._merged_interfaces


def merge_node_type_and_node_template_interfaces(
        node_name,
        complete_type,
        node):

    merger = NodeTemplateNodeTypeInterfacesMerger(
        node_type=complete_type,
        node_template=node,
        node_name=node_name)

    node_with_interfaces = copy.deepcopy(node)
    node_with_interfaces[INTERFACES] = merger.merge()
    return node_with_interfaces


def merge_interface_dicts(overridden, overriding, interfaces_attribute):
    if interfaces_attribute not in overridden and \
       interfaces_attribute not in overriding:
        return {}
    if interfaces_attribute not in overridden:
        return overriding[interfaces_attribute]
    if interfaces_attribute not in overriding:
        return overridden[interfaces_attribute]
    merged_interfaces = copy.deepcopy(overridden[interfaces_attribute])
    for overriding_interface, interface_obj in \
            overriding[interfaces_attribute].items():
        interface_obj_copy = copy.deepcopy(interface_obj)
        if overriding_interface not in overridden[interfaces_attribute]:
            merged_interfaces[overriding_interface] = interface_obj_copy
        else:
            merged_interfaces[overriding_interface] = _merge_interface_dict(
                overridden[interfaces_attribute][overriding_interface],
                interface_obj_copy)
    return merged_interfaces


def _merge_node_type_interface_operations(overriding_op, overridden_op):

    if isinstance(overriding_op, dict) and \
       isinstance(overridden_op, dict):
        if not overriding_op:
            # no-op overriding
            return overriding_op
        return {
            'implementation': overriding_op.get('implementation', ''),
            'inputs': merge_sub_dicts(
                overridden_dict=overridden_op,
                overriding_dict=overriding_op,
                sub_dict_key='inputs'
            )
        }
    if isinstance(overriding_op, str) and \
       isinstance(overridden_op, str):
        return {
            'implementation': overriding_op or overridden_op,
            'inputs': {}
        }

    if isinstance(overriding_op, str):

        return {
            'implementation': overriding_op,
            'inputs': merge_sub_dicts(
                overridden_dict=overridden_op,
                overriding_dict={},
                sub_dict_key='inputs'
            )
        }

    if isinstance(overridden_op, str):

        return {
            'implementation': overriding_op.get('implementation', ''),
            'inputs': merge_sub_dicts(
                overridden_dict={},
                overriding_dict=overriding_op,
                sub_dict_key='inputs'
            )
        }


def _merge_interface_dict(overridden_interface, overriding_interface):

    def op_and_op_name(op):
        key = op[0]
        value = op[1]
        return key, value

    # OrderedDict for easier testability
    overridden = OrderedDict((x, y) for x, y in map(
        op_and_op_name,
        overridden_interface.items()))
    overriding = OrderedDict((x, y) for x, y in map(
        op_and_op_name,
        overriding_interface.items()))
    result = {}
    for op_name, operation in overridden.items():
        if op_name not in overriding:
            result[op_name] = operation
        else:

            overriding_op = overriding[op_name]
            overridden_op = overridden[op_name]
            result[op_name] = \
                _merge_node_type_interface_operations(
                    overriding_op,
                    overridden_op
                )

    for op_name, operation in overriding.items():
        if op_name not in overridden:
            result[op_name] = operation
    return result
