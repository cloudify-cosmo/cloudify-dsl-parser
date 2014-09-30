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


def merge_type_and_node_interfaces(node_name, complete_type, node):

    from dsl_parser.parser import INTERFACES

    complete_node = copy.deepcopy(node)
    complete_node[INTERFACES] = {}

    if INTERFACES not in node:
        node[INTERFACES] = {}
    if INTERFACES not in complete_type:
        complete_node[INTERFACES] = {}
        for interface_name, interface in node[INTERFACES].items():
            complete_node[INTERFACES][interface_name] = {}
            for operation_name, operation in interface.items():
                complete_node[
                    INTERFACES][interface_name][operation_name] \
                    = augment_operation(operation)
        return complete_node
    for interface_name, interface in complete_type[INTERFACES].items():
        complete_node[INTERFACES][interface_name] = {}
        if interface_name not in node[INTERFACES]:
            node[INTERFACES][interface_name] = {}
        for operation_name, operation in interface.items():
            if operation_name not in node[INTERFACES][interface_name]:
                if isinstance(operation, str):
                    node[INTERFACES][interface_name][operation_name] = ''
                if isinstance(operation, dict):
                    node[INTERFACES][interface_name][operation_name] = {}

            complete_node[
                INTERFACES][interface_name][operation_name] = \
                _merge_operations(
                    node_name=node_name,
                    node_type_operation=operation,
                    node_template_operation=node[
                        INTERFACES][interface_name][operation_name]
                )

    # process operations that exist
    # on the node template but do not
    # exist on the node type
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

    return complete_node


def augment_operation(operation):
    if isinstance(operation, str):
        return {
            'implementation': operation,
            'inputs': {}
        }
    if isinstance(operation, dict):
        return {
            'implementation': operation.get('implementation', {}),
            'inputs': operation.get('inputs', {})
        }


def _merge_operation_dicts(node_name,
                           node_template_operation,
                           node_type_operation):

    from dsl_parser.parser import merge_schema_and_instance_properties

    return {

        # override implementation
        'implementation': node_template_operation.get(
            'implementation',
            node_type_operation.get(
                'implementation',
                {}
            )
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


def _merge_operation_strings(node_name,
                             node_template_operation,
                             node_type_operation):
    return {
        'implementation': node_template_operation or node_type_operation,
        'inputs': {}
    }


def _merge_mixed_operation(node_name,
                           node_template_operation,
                           node_type_operation):
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
        return node_template_operation


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
        return _merge_operation_strings(node_name, node_template_operation,
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
        from dsl_parser.parser import merge_sub_dicts
        return {
            'implementation': overriding_op['implementation'],
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
            'implementation': overriding_op['implementation'],
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
        if not value:
            # no-op mapping
            return key, key
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
