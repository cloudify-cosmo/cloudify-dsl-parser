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

    @staticmethod
    def _create_operation(raw_operation):
        if raw_operation is None:
            return None
        if isinstance(raw_operation, str):
            return operation_mapping(
                implementation=raw_operation,
                inputs={},
                executor=None
            )
        if isinstance(raw_operation, dict):
            return operation_mapping(
                implementation=raw_operation.get('implementation', ''),
                inputs=raw_operation.get('inputs', {}),
                executor=raw_operation.get('executor', None)
            )

    def merge(self):
        raise NotImplementedError('Must be implemented by subclasses')


class NodeTemplateNodeTypeOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
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

    def _derive_executor(self, merged_operation_implementation):

        node_type_operation_executor = self.node_type_operation[
            'executor']
        node_template_operation_executor = self.node_template_operation[
            'executor']

        if merged_operation_implementation != \
                self.node_type_operation['implementation']:
            # this means the node template operation executor will take
            # precedence (even if it is None, in which case,
            # the default plugin executor will be used eventually)
            return node_template_operation_executor
        if node_template_operation_executor is not None:
            # node template operation executor is declared
            # explicitly, use it
            return node_template_operation_executor

        return node_type_operation_executor

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
                ),
                executor=self.node_type_operation['executor']
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
        merged_operation_executor = self._derive_executor(
            merged_operation_implementation)

        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs,
            executor=merged_operation_executor
        )


class NodeTypeNodeTypeOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        self.overridden_node_type_operation = self._create_operation(
            overridden_operation)
        self.overriding_node_type_operation = self._create_operation(
            overriding_operation)

    def merge(self):

        if self.overriding_node_type_operation is None:
            return self.overridden_node_type_operation

        if self.overriding_node_type_operation == NO_OP:
            return NO_OP

        merged_operation_implementation = \
            self.overriding_node_type_operation['implementation']

        merged_operation_inputs = \
            self.overriding_node_type_operation['inputs']

        merged_operation_executor = \
            self.overriding_node_type_operation['executor']

        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs,
            executor=merged_operation_executor
        )


RelationshipTypeRelationshipTypeOperationMerger = \
    NodeTypeNodeTypeOperationMerger
RelationshipTypeRelationshipInstanceOperationMerger = \
    NodeTemplateNodeTypeOperationMerger
