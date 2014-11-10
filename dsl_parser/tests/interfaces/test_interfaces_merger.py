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

import testtools

from dsl_parser.interfaces.interfaces_merger import InterfaceMerger
from dsl_parser.interfaces.interfaces_merger import InterfacesMerger
from dsl_parser.interfaces.operation_merger import OperationMerger


class InterfaceMergerTest(testtools.TestCase):

    def _assert_interface(self,
                          overriding_interface,
                          overridden_interface,
                          expected_merged_interface_keys):

        class MockOperationMerger(OperationMerger):

            def __init__(self,
                         overriding_operation,
                         overridden_operation):
                pass

            def merge(self):
                return None

        merger = InterfaceMerger(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            operation_merger=MockOperationMerger
        )
        actual_merged_interface_keys = set(merger.merge().keys())
        self.assertEqual(expected_merged_interface_keys,
                         actual_merged_interface_keys)

    def test_merge_operations(self):

        overriding_interface = {
            'stop': None
        }
        overridden_interface = {
            'start': None
        }

        expected_merged_interface_keys = set(['stop', 'start'])

        self._assert_interface(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            expected_merged_interface_keys=expected_merged_interface_keys
        )

    def test_override_operation(self):

        overriding_interface = {
            'stop': None
        }
        overridden_interface = {
            'stop': None
        }

        expected_merged_interface_keys = set(['stop'])

        self._assert_interface(
            overriding_interface=overriding_interface,
            overridden_interface=overridden_interface,
            expected_merged_interface_keys=expected_merged_interface_keys
        )


class InterfacesMergerTest(testtools.TestCase):

    def _assert_interfaces(self,
                           overriding_interfaces,
                           overridden_interfaces,
                           expected_merged_interfaces_keys):

        class MockOperationMerger(OperationMerger):

            def __init__(self,
                         overriding_operation,
                         overridden_operation):
                pass

            def merge(self):
                return None

        merger = InterfacesMerger(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            operation_merger=MockOperationMerger
        )
        actual_merged_interfaces_keys = set(merger.merge().keys())
        self.assertEqual(expected_merged_interfaces_keys,
                         actual_merged_interfaces_keys)

    def test_merge_interfaces(self):

        overriding_interfaces = {
            'interface1': {}
        }
        overridden_interfaces = {
            'interface2': {}
        }

        expected_merged_interfaces_keys = set(['interface1', 'interface2'])
        self._assert_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            expected_merged_interfaces_keys=expected_merged_interfaces_keys
        )

    def test_override_interface(self):

        overriding_interfaces = {
            'interface1': {}
        }
        overridden_interfaces = {
            'interface1': {}
        }

        expected_merged_interfaces_keys = set(['interface1'])
        self._assert_interfaces(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            expected_merged_interfaces_keys=expected_merged_interfaces_keys
        )
