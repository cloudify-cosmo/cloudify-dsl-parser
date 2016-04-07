# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .operation_merger import OperationMerger


class InterfaceMerger(object):
    def __init__(self,
                 overriding_interface,
                 overridden_interface,
                 operation_merger=OperationMerger):
        self.overriding_interface = overriding_interface
        self.overridden_interface = overridden_interface
        self.operation_merger = operation_merger

    def merge(self):
        merged_interface = {}

        for overridden_name, overridden in self.overridden_interface.items():
            overriding = self.overriding_interface.get(overridden_name, None)
            merger = self.operation_merger(
                overriding_operation=overriding,
                overridden_operation=overridden)
            merged_operation = merger.merge()
            merged_interface[overridden_name] = merged_operation

        for overriding_name, overriding in self.overriding_interface.items():
            overridden = self.overridden_interface.get(
                overriding_name, None)
            merger = self.operation_merger(
                overriding_operation=overriding,
                overridden_operation=overridden)
            merged_operation = merger.merge()
            merged_interface[overriding_name] = merged_operation

        return merged_interface


class InterfacesMerger(object):
    def __init__(self,
                 overriding_interfaces,
                 overridden_interfaces,
                 operation_merger):
        self.overriding_interfaces = overriding_interfaces
        self.overridden_interfaces = overridden_interfaces
        self.operation_merger = operation_merger
        self.interface_merger = InterfaceMerger

    def merge(self):
        merged_interfaces = {}

        for overridden_name, overridden in self.overridden_interfaces.items():
            overriding = self.overriding_interfaces.get(overridden_name, {})
            interface_merger = self.interface_merger(
                overriding_interface=overriding,
                overridden_interface=overridden,
                operation_merger=self.operation_merger)
            merged_interface = interface_merger.merge()
            merged_interfaces[overridden_name] = merged_interface

        for overriding_name, overriding in self.overriding_interfaces.items():
            overridden = self.overridden_interfaces.get(overriding_name, {})
            interface_merger = self.interface_merger(
                overriding_interface=overriding,
                overridden_interface=overridden,
                operation_merger=self.operation_merger)
            merged_interface = interface_merger.merge()
            merged_interfaces[overriding_name] = merged_interface
        return merged_interfaces
