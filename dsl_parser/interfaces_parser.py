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

def merge_type_operation_to_complete_node(operation_name,
                                          operation,
                                          node,
                                          interface_name,
                                          complete_node,
                                          node_name):

    if operation_name not in node[INTERFACES][interface_name]:

        # operation is defined in the type but
        # is not defined in the template
        # set the operation on the node as None,
        # indicating that it doesn't really exist.
        node[INTERFACES][interface_name][operation_name] = None

    complete_node[
        INTERFACES][interface_name][operation_name] = \
        _merge_operations(
            node_name=node_name,
            node_type_operation=operation,
            node_template_operation=node[
                INTERFACES][interface_name][operation_name]
        )


def merge_type_interface_to_complete_node(interface_name,
                                          interface,
                                          node,
                                          node_name,
                                          complete_node):

    if interface_name not in node[INTERFACES]:

        # interface exists in the type but doesnt
        # exist in the template.
        # the complete node will have this interface
        # so we can treat the complete node as if
        # it defined this interface empty.

        node[INTERFACES][interface_name] = {}

    for operation_name, operation in interface.items():
        merge_type_operation_to_complete_node(
            operation_name,
            operation,
            node,
            interface_name,
            complete_node,
            node_name
        )


def merge_type_interfaces_to_complete_node(
        complete_node,
        complete_type,
        node,
        node_name):

    for interface_name, interface in complete_type[INTERFACES].items():

        # initialize interface on complete node.
        complete_node[INTERFACES][interface_name] = {}

        merge_type_interface_to_complete_node(
            interface_name,
            interface,
            node,
            node_name,
            complete_node)


def merge_template_interfaces_to_complete_node(complete_node, node):

    for interface_name, interface in node[INTERFACES].items():
        if interface_name not in complete_node[INTERFACES]:
            complete_node[INTERFACES][interface_name] = {}
            for operation_name, operation in interface.items():
                complete_node[
                    INTERFACES][interface_name][operation_name] \
                    = augment_operation(operation)
        else:
            # interface exists
            # check per operation
            for operation_name, operation in interface.items():
                if operation_name not in \
                        complete_node[INTERFACES][interface_name]:
                    complete_node[
                        INTERFACES][interface_name][operation_name] \
                        = augment_operation(operation)


def merge_node_type_and_node_template_interfaces(
        node_name,
        complete_type,
        node):

    """
    Merges a node template with a node type.
    Node template values always override
    the node type values or merges with it.
    Never the other way around.

    :param node_name: The node name.
    :param complete_type: The node complete type
                          including all derived types.
    :param node: The actual node template.
    :return: The node augmented with the 'interfaces' key
             The return value is a copy of the original value.
             It does not mutate the original 'node'.
    :rtype dict
    """

    complete_node = copy.deepcopy(node)
    complete_node[INTERFACES] = {}

    if INTERFACES not in node:
        # node templates doesn't define
        # interfaces
        node[INTERFACES] = {}

    if INTERFACES not in complete_type:
        # node type doesn't define
        # interfaces
        complete_type[INTERFACES] = {}

    # iterate over the type interfaces and merge
    # them to the result (complete_node)
    merge_type_interfaces_to_complete_node(complete_node, complete_type, node, node_name)

    # iterate over the template interfaces and merge
    # them to the result (complete_node)
    merge_template_interfaces_to_complete_node(complete_node, node)

    return complete_node


def augment_operation(operation):
    if isinstance(operation, str):
        return {
            'implementation': operation,
            'inputs': {}
        }
    if isinstance(operation, dict):
        return {
            'implementation': operation.get('implementation', ''),
            'inputs': operation.get('inputs', {})
        }


def _merge_operation_dicts(node_name,
                           node_template_operation,
                           node_type_operation):

    from dsl_parser.parser import merge_schema_and_instance_properties

    if not node_template_operation:
        # no-op mapping
        return {
            'implementation': '',
            'inputs': {}
        }

    return {

        # override implementation
        'implementation': node_template_operation.get(
            'implementation',
            node_type_operation.get('implementation', '')
        ),

        # validate and merge with inputs schema
        'inputs': merge_schema_and_instance_properties(
            instance_properties=node_template_operation.get('inputs', {}),
            impl_properties={},
            schema_properties=node_type_operation.get('inputs', {}),
            undefined_property_error_message=None,
            missing_property_error_message=None,
            node_name=node_name,
            is_interface_inputs=True
        )
    }


def _merge_operation_strings(node_template_operation,
                             node_type_operation):
    return {
        'implementation': node_template_operation or node_type_operation,
        'inputs': {}
    }


def _merge_mixed_operation(node_name,
                           node_template_operation,
                           node_type_operation):

    if node_template_operation is None and isinstance(node_type_operation, dict):

        from dsl_parser.parser import merge_schema_and_instance_properties

        return {

            # override implementation
            'implementation': node_type_operation.get('implementation', ''),

            # validate and merge with inputs schema
            'inputs': merge_schema_and_instance_properties(
                instance_properties={},
                impl_properties={},
                schema_properties=node_type_operation.get('inputs', {}),
                undefined_property_error_message=None,
                missing_property_error_message=None,
                node_name=node_name,
                is_interface_inputs=True
            )
        }

    if node_template_operation is None and isinstance(node_type_operation, str):

        from dsl_parser.parser import merge_schema_and_instance_properties

        return {

            # override implementation
            'implementation': node_type_operation,

            # no inputs since its a string mapping
            'inputs': {}
        }

    if isinstance(node_template_operation, str):
        # this means the node_type_operation is a dict
        # which means it defines inputs.

        from dsl_parser.parser import merge_schema_and_instance_properties

        return {

            # override implementation
            'implementation': node_template_operation,

            # validate and merge with inputs schema
            'inputs': merge_schema_and_instance_properties(
                instance_properties={},
                impl_properties={},
                schema_properties=node_type_operation.get('inputs', {}),
                undefined_property_error_message=None,
                missing_property_error_message=None,
                node_name=node_name,
                is_interface_inputs=True
            )
        }

    if isinstance(node_type_operation, str):

        return {

            # override implementation
            'implementation': node_template_operation.get('implementation', ''),

            'inputs': node_template_operation.get('inputs', {})
        }


def _merge_operations(node_name, node_template_operation,
                      node_type_operation):

    # 1. both operations are dicts
    if isinstance(node_type_operation, dict) and \
       isinstance(node_template_operation, dict):
        return _merge_operation_dicts(node_name, node_template_operation,
                                      node_type_operation)

    # 2. both operations are strings
    if isinstance(node_type_operation, str) and \
       isinstance(node_template_operation, str):
        return _merge_operation_strings(node_template_operation,
                                        node_type_operation)

    # 3. mixed
    return _merge_mixed_operation(node_name, node_template_operation,
                                  node_type_operation)


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
        from dsl_parser.parser import merge_sub_dicts
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

        from dsl_parser.parser import merge_sub_dicts

        return {
            'implementation': overriding_op,
            'inputs': merge_sub_dicts(
                overridden_dict=overridden_op,
                overriding_dict={},
                sub_dict_key='inputs'
            )
        }

    if isinstance(overridden_op, str):

        from dsl_parser.parser import merge_sub_dicts

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
