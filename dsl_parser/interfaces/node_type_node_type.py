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

from dsl_parser.interfaces.merging import InterfacesMerger
from dsl_parser.interfaces.merging import InterfaceMerger
from dsl_parser.interfaces.merging import OperationMerger
from dsl_parser.interfaces.interfaces_parser import operation_mapping


class NodeTypeNodeTypeInterfacesMerger(InterfacesMerger):

    def __init__(self,
                 overriding_interfaces,
                 overridden_interfaces):
        super(NodeTypeNodeTypeInterfacesMerger, self).__init__(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            interface_merger=NodeTypeNodeTypeInterfaceMerger)


class NodeTypeNodeTypeInterfaceMerger(InterfaceMerger):

    def __init__(self,
                 overriding_interface,
                 overridden_interface):
        super(NodeTypeNodeTypeInterfaceMerger, self).__init__(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            operation_merger=NodeTypeNodeTypeInterfaceOperationMerger)


class NodeTypeNodeTypeInterfaceOperationMerger(OperationMerger):

    def __init__(self,
                 overriding_operation,
                 overridden_operation):
        super(NodeTypeNodeTypeInterfaceOperationMerger, self).__init__(
            overriding_operation=overriding_operation,
            overridden_operation=overridden_operation)
        self.overridden_node_type_operation = self._create_operation(overridden_operation)
        self.overriding_node_type_operation = self._create_operation(overriding_operation)

    def merge(self):

        merged_operation_implementation = self.overriding_operation['implementation']
        merged_operation_inputs = self.overriding_operation['inputs']
        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=merged_operation_inputs
        )