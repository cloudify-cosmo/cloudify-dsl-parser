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
from dsl_parser.interfaces.operation_merger import NodeTypeNodeTypeInterfaceOperationMerger
from dsl_parser.interfaces.operation_merger import RelationshipTypeRelationshipInstanceInterfaceOperationMerger
from dsl_parser.interfaces.operation_merger import RelationshipTypeRelationshipTypeInterfaceOperationMerger
from dsl_parser.interfaces.operation_merger import NodeTemplateNodeTypeInterfaceOperationMerger
from dsl_parser.interfaces.constants import INTERFACES, SOURCE_INTERFACES, TARGET_INTERFACES


def merge_node_type_interfaces(overriding_node_type,
                               overridden_node_type):
    merger = InterfacesMerger(
        overriding_interfaces=overriding_node_type.get(INTERFACES, {}),
        overridden_interfaces=overridden_node_type.get(INTERFACES, {}),
        operation_merger=NodeTypeNodeTypeInterfaceOperationMerger
    )
    return merger.merge()


def merge_node_type_and_node_template_interfaces(node_type,
                                                 node_template):
    merger = InterfacesMerger(
        overriding_interfaces=node_template.get(INTERFACES, {}),
        overridden_interfaces=node_type.get(INTERFACES, {}),
        operation_merger=NodeTemplateNodeTypeInterfaceOperationMerger
    )
    return merger.merge()


def merge_relationship_type_interfaces(overriding_relationship_type,
                                       overridden_relationship_type,
                                       interfaces_attribute):
    merger = InterfacesMerger(
        overriding_interfaces=overriding_relationship_type.get(interfaces_attribute, {}),
        overridden_interfaces=overridden_relationship_type.get(interfaces_attribute, {}),
        operation_merger=RelationshipTypeRelationshipTypeInterfaceOperationMerger
    )
    return merger.merge()


def merge_relationship_type_and_instance_source_interfaces(relationship_type,
                                                           relationship_instance):

    source_interfaces_merger = InterfacesMerger(
        overriding_interfaces=relationship_instance.get(SOURCE_INTERFACES, {}),
        overridden_interfaces=relationship_type.get(SOURCE_INTERFACES, {}),
        operation_merger=RelationshipTypeRelationshipInstanceInterfaceOperationMerger
    )
    return source_interfaces_merger.merge()


def merge_relationship_type_and_instance_target_interfaces(relationship_type,
                                                           relationship_instance):

    target_interfaces_merger = InterfacesMerger(
        overriding_interfaces=relationship_instance.get(TARGET_INTERFACES, {}),
        overridden_interfaces=relationship_type.get(TARGET_INTERFACES, {}),
        operation_merger=RelationshipTypeRelationshipInstanceInterfaceOperationMerger
    )
    return target_interfaces_merger.merge()
