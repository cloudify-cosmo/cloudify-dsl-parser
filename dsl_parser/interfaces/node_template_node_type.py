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

from dsl_parser import utils
from dsl_parser.interfaces.merging import InterfacesMerger
from dsl_parser.interfaces.merging import InterfaceMerger
from dsl_parser.interfaces.merging import OperationMerger
from dsl_parser.interfaces.interfaces_parser import operation_mapping
from dsl_parser.interfaces.interfaces_parser import NO_OP


class NodeTemplateNodeTypeInterfacesMerger(InterfacesMerger):

    def __init__(self,
                 overriding_interfaces,
                 overridden_interfaces):
        super(NodeTemplateNodeTypeInterfacesMerger, self).__init__(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            interface_merger=NodeTemplateNodeTypeInterfaceMerger)


class NodeTemplateNodeTypeInterfaceMerger(InterfaceMerger):

    def __init__(self,
                 overriding_interface,
                 overridden_interface):
        super(NodeTemplateNodeTypeInterfaceMerger, self).__init__(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            operation_merger=NodeTemplateNodeTypeInterfaceOperationMerger)


class NodeTemplateNodeTypeInterfaceOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        super(NodeTemplateNodeTypeInterfaceOperationMerger, self).__init__(
            overriding_operation=overriding_operation,
            overridden_operation=overridden_operation)
        self.node_type_operation = self._create_operation(overridden_operation)
        self.node_template_operation = self._create_operation(overriding_operation)

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
                node_name=None,
                is_interface_inputs=True
            )
        else:
            # the node template implementation overrides
            # the node type implementation. this means
            # we take the inputs defined in the node template
            merged_operation_inputs = self.node_template_operation['inputs']

        return merged_operation_inputs

    def merge(self):

        if self.node_type_operation is None:

            # the operation is not defined in the type
            # should be merged by the node template operation

            return self._create_operation(self.node_template_operation)

        if self.node_template_operation is None:

            # the operation is not defined in the template
            # should be merged by the node type operation

            return operation_mapping(
                implementation=self.node_type_operation['implementation'],
                inputs=utils.merge_schema_and_instance_properties(
                    instance_properties={},
                    impl_properties={},
                    schema_properties=self.node_type_operation['inputs'],
                    undefined_property_error_message=None,
                    missing_property_error_message=None,
                    node_name=None,
                    is_interface_inputs=True
                )
            )

        if self.node_template_operation == NO_OP:
            # no-op overrides
            return operation_mapping()
        if self.node_type_operation == NO_OP:
            # no-op overridden
            return self.node_template_operation

        merged_operation_implementation = self._derive_implementation()
        merged_operation_inputs = self._derive_inputs(merged_operation_implementation)

        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs
        )
