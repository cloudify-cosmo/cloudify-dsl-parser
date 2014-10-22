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

from dsl_parser.interfaces.interfaces_merger import InterfacesMerger
from dsl_parser.interfaces.operation_merger import \
    NodeTypeNodeTypeOperationMerger
from dsl_parser.interfaces.operation_merger import \
    RelationshipTypeRelationshipInstanceOperationMerger
from dsl_parser.interfaces.operation_merger import \
    RelationshipTypeRelationshipTypeOperationMerger
from dsl_parser.interfaces.operation_merger import \
    NodeTemplateNodeTypeOperationMerger
from dsl_parser.interfaces.constants import INTERFACES
from dsl_parser.interfaces.constants import SOURCE_INTERFACES
from dsl_parser.interfaces.constants import TARGET_INTERFACES


def merge_node_type_interfaces(overriding_node_type,
                               overridden_node_type):

    # using this pattern for the sake of
    # code coverage tools

    overriding_interfaces = overriding_node_type.get(INTERFACES)
    if not overriding_interfaces:
        overriding_interfaces = {}

    overridden_interfaces = overridden_node_type.get(INTERFACES)
    if not overridden_interfaces:
        overridden_interfaces = {}

    merger = InterfacesMerger(
        overriding_interfaces=overriding_interfaces,
        overridden_interfaces=overridden_interfaces,
        operation_merger=NodeTypeNodeTypeOperationMerger
    )
    return merger.merge()


def merge_node_type_and_node_template_interfaces(node_type,
                                                 node_template):

    # using this pattern for the sake of
    # code coverage tools

    overriding_interfaces = node_template.get(INTERFACES)
    if not overriding_interfaces:
        overriding_interfaces = {}

    overridden_interfaces = node_type.get(INTERFACES)
    if not overridden_interfaces:
        overridden_interfaces = {}

    merger = InterfacesMerger(
        overriding_interfaces=overriding_interfaces,
        overridden_interfaces=overridden_interfaces,
        operation_merger=NodeTemplateNodeTypeOperationMerger
    )
    return merger.merge()


def merge_relationship_type_interfaces(overriding_relationship_type,
                                       overridden_relationship_type):
    # using this pattern for the sake of
    # code coverage tools

    overriding_source_interfaces = overriding_relationship_type.get(
        SOURCE_INTERFACES)
    if not overriding_source_interfaces:
        overriding_source_interfaces = {}

    overridden_source_interfaces = overridden_relationship_type.get(
        SOURCE_INTERFACES)
    if not overridden_source_interfaces:
        overridden_source_interfaces = {}

    overriding_target_interfaces = overriding_relationship_type.get(
        TARGET_INTERFACES)
    if not overriding_target_interfaces:
        overriding_target_interfaces = {}

    overridden_target_interfaces = overridden_relationship_type.get(
        TARGET_INTERFACES)
    if not overridden_target_interfaces:
        overridden_target_interfaces = {}

    source_interfaces_merger = InterfacesMerger(
        overriding_interfaces=overriding_source_interfaces,
        overridden_interfaces=overridden_source_interfaces,
        operation_merger=RelationshipTypeRelationshipTypeOperationMerger
    )
    target_interfaces_merger = InterfacesMerger(
        overriding_interfaces=overriding_target_interfaces,
        overridden_interfaces=overridden_target_interfaces,
        operation_merger=RelationshipTypeRelationshipTypeOperationMerger
    )

    return {
        SOURCE_INTERFACES: source_interfaces_merger.merge(),
        TARGET_INTERFACES: target_interfaces_merger.merge()
    }


def merge_relationship_type_and_instance_interfaces(
        relationship_type,
        relationship_instance):

    # using this pattern for the sake of
    # code coverage tools

    overriding_source_interfaces = relationship_instance.get(SOURCE_INTERFACES)
    if not overriding_source_interfaces:
        overriding_source_interfaces = {}

    overridden_source_interfaces = relationship_type.get(SOURCE_INTERFACES)
    if not overridden_source_interfaces:
        overridden_source_interfaces = {}

    overriding_target_interfaces = relationship_instance.get(TARGET_INTERFACES)
    if not overriding_target_interfaces:
        overriding_target_interfaces = {}

    overridden_target_interfaces = relationship_type.get(TARGET_INTERFACES)
    if not overridden_target_interfaces:
        overridden_target_interfaces = {}

    source_interfaces_merger = InterfacesMerger(
        overriding_interfaces=overriding_source_interfaces,
        overridden_interfaces=overridden_source_interfaces,
        operation_merger=RelationshipTypeRelationshipInstanceOperationMerger
    )
    target_interfaces_merger = InterfacesMerger(
        overriding_interfaces=overriding_target_interfaces,
        overridden_interfaces=overridden_target_interfaces,
        operation_merger=RelationshipTypeRelationshipInstanceOperationMerger
    )

    return {
        SOURCE_INTERFACES: source_interfaces_merger.merge(),
        TARGET_INTERFACES: target_interfaces_merger.merge()
    }
