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

from dsl_parser.interfaces.utils import operation_mapping
from dsl_parser.interfaces.constants import NO_OP
from dsl_parser.interfaces.utils import merge_schema_and_instance_inputs


class OperationMerger(object):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        self.overriding_operation = overriding_operation
        self.overridden_operation = overridden_operation

    @staticmethod
    def _create_operation(raw_operation):
        if raw_operation is None:
            return None
        if isinstance(raw_operation, str):
            return operation_mapping(
                implementation=raw_operation,
                inputs={}
            )
        if isinstance(raw_operation, dict):
            return operation_mapping(
                implementation=raw_operation.get('implementation', ''),
                inputs=raw_operation.get('inputs', {})
            )

    def merge(self):
        raise NotImplementedError('Must be implemented by subclasses')


class NodeTemplateNodeTypeOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        super(NodeTemplateNodeTypeOperationMerger, self).__init__(
            overriding_operation=overriding_operation,
            overridden_operation=overridden_operation)
        self.node_type_operation = self._create_operation(
            overridden_operation)
        self.node_template_operation = self._create_operation(
            overriding_operation)

    def _derive_implementation(self):
        merged_operation_implementation = \
            self.node_template_operation['implementation']
        if not merged_operation_implementation:
            # node template does not define an implementation
            # this means we want to inherit the implementation
            # from the type
            merged_operation_implementation = \
                self.node_type_operation['implementation']
        return merged_operation_implementation

    def _derive_inputs(self, merged_operation_implementation):
        if merged_operation_implementation == \
                self.node_type_operation['implementation']:
            # this means the node template inputs should adhere to
            # the node type inputs schema (since its the same implementation)
            merged_operation_inputs = merge_schema_and_instance_inputs(
                schema_inputs=self.node_type_operation['inputs'],
                instance_inputs=self.node_template_operation['inputs']
            )
        else:
            # the node template implementation overrides
            # the node type implementation. this means
            # we take the inputs defined in the node template
            merged_operation_inputs = \
                self.node_template_operation['inputs']

        return merged_operation_inputs

    def merge(self):

        if self.node_type_operation is None:

            # the operation is not defined in the type
            # should be merged by the node template operation

            return self.node_template_operation

        if self.node_template_operation is None:

            # the operation is not defined in the template
            # should be merged by the node type operation
            # this will validate that all schema inputs have
            # default values

            return operation_mapping(
                implementation=self.node_type_operation['implementation'],
                inputs=merge_schema_and_instance_inputs(
                    schema_inputs=self.node_type_operation['inputs'],
                    instance_inputs={}
                )
            )

        if self.node_template_operation == NO_OP:
            # no-op overrides
            return NO_OP
        if self.node_type_operation == NO_OP:
            # no-op overridden
            return self.node_template_operation

        merged_operation_implementation = self._derive_implementation()
        merged_operation_inputs = self._derive_inputs(
            merged_operation_implementation)

        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs
        )


class NodeTypeNodeTypeOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        super(NodeTypeNodeTypeOperationMerger, self).__init__(
            overriding_operation=overriding_operation,
            overridden_operation=overridden_operation)
        self.overridden_node_type_operation = self._create_operation(
            overridden_operation)
        self.overriding_node_type_operation = self._create_operation(
            overriding_operation)

    def merge(self):

        if self.overriding_node_type_operation is None:
            return self.overridden_node_type_operation

        if self.overriding_node_type_operation == NO_OP:
            return NO_OP

        # operation in node type must
        # contain 'implementation' (validated by schema)
        merged_operation_implementation = \
            self.overriding_operation['implementation']

        # operation in node type doe's not
        # have to contain 'inputs' (allowed by schema)
        merged_operation_inputs = \
            self.overriding_operation.get('inputs', {})
        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs
        )


RelationshipTypeRelationshipTypeOperationMerger = \
    NodeTypeNodeTypeOperationMerger
RelationshipTypeRelationshipInstanceOperationMerger = \
    NodeTemplateNodeTypeOperationMerger
