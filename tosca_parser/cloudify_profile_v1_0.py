#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from itertools import chain

from aria.parser.extension_tools import ElementExtension

from .elements import (
    PolicyTriggers, PolicyTypes, GroupPolicies, Group,
    NodeTemplateRelationships, CloudifyNodeTemplateRelationships,
    NodeTypes, CloudifyNodeTypes,
    Blueprint, CloudifyBlueprint,
    OperationExecutor, CloudifyOperationExecutor,
    Plugin, CloudifyPluginExecutor,
    NodeTemplates, CloudifyNodeTemplates,
    ImportsLoader, POLICY_TRIGGERS, POLICY_TYPES,
)


def extend_cloudify_version_1_0():
    _unofficial_extensions()
    return dict(
        element_extensions=chain([
            cloudify_node_template_relationships_extension,
            cloudify_node_type_extension,
            cloudify_operation_executor_extension,
            cloudify_plugin_extension_extension,
            cloudify_node_templates_extension,
            cloudify_group_schema_extension,
        ], _blueprint_element_extensions()))


def _unofficial_extensions():
    ImportsLoader.MERGE_NO_OVERRIDE.update((POLICY_TYPES, POLICY_TRIGGERS))


def _blueprint_element_extensions():
    return [
        cloudify_blueprint_extension,
        cloudify_blueprint_schema_policy_triggers_extension,
        cloudify_blueprint_schema_policy_type_extension,
    ]


cloudify_node_template_relationships_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTemplateRelationships,
    new_element=CloudifyNodeTemplateRelationships)

cloudify_node_type_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTypes,
    new_element=CloudifyNodeTypes)

cloudify_blueprint_schema_policy_triggers_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Blueprint,
    new_element=PolicyTriggers,
    schema_key='policy_triggers')
cloudify_blueprint_schema_policy_type_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Blueprint,
    new_element=PolicyTypes,
    schema_key='policy_types')

cloudify_blueprint_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=Blueprint,
    new_element=CloudifyBlueprint)

cloudify_operation_executor_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=OperationExecutor,
    new_element=CloudifyOperationExecutor)

cloudify_plugin_extension_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Plugin,
    new_element=CloudifyPluginExecutor,
    schema_key='executor')

cloudify_node_templates_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTemplates,
    new_element=CloudifyNodeTemplates)

cloudify_group_schema_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Group,
    new_element=GroupPolicies,
    schema_key='policies')
