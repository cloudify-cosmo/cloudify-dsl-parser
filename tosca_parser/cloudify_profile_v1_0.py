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

from aria.parser.framework.elements.node_templates import (
    NodeTemplateRelationships, NodeTemplates)
from aria.parser.framework.elements.node_types import NodeTypes
from aria.parser.framework.elements.blueprint import Blueprint
from aria.parser.framework.elements.policies import PolicyTriggers
from aria.parser.framework.elements.operation import OperationExecutor
from aria.parser.framework.elements.plugins import Plugin
from aria.parser.framework.elements import Element, Leaf
from aria.parser.constants import (
    CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT,
    POLICY_TRIGGERS, PLUGIN_EXECUTOR_KEY,
)
from aria.parser.extension_tools import ElementExtension
from aria.parser.exceptions import DSLParsingLogicException


def extend_cloudify_version_1_0():
    return dict(
        element_extensions=[
            cloudify_node_template_relationships_extension,
            cloudify_node_type_extension,
            cloudify_blueprint_extension,
            cloudify_blueprint_schema_extension,
            cloudify_operation_executor_extension,
            cloudify_plugin_extension_extension,
            cloudify_node_templates_extension,
        ])


class CloudifyNodeTemplateRelationships(NodeTemplateRelationships):
    CONTAINED_IN_REL_TYPE = 'cloudify.relationships.contained_in'


class CloudifyNodeTypes(NodeTypes):
    HOST_TYPE = 'cloudify.nodes.Compute'


class CloudifyBlueprint(Blueprint):
    def parse(self, *args, **kwargs):
        plan = super(CloudifyBlueprint, self).parse(*args, **kwargs)
        plan[POLICY_TRIGGERS] = self.child(PolicyTriggers).value
        return plan


class CloudifyOperationExecutor(OperationExecutor):
    valid_executors = (CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT)


class CloudifyPluginExecutor(Element):
    required = True
    schema = Leaf(type=str)

    def validate(self):
        if self.initial_value not in [CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT]:
            raise DSLParsingLogicException(
                18,
                "Plugin '{0}' has an illegal "
                "'{1}' value '{2}'; value "
                "must be either '{3}' or '{4}'"
                .format(self.ancestor(Plugin).name,
                        self.name,
                        self.initial_value,
                        CENTRAL_DEPLOYMENT_AGENT,
                        HOST_AGENT))


class CloudifyNodeTemplates(NodeTemplates):
    @staticmethod
    def check_executor_key(plugin):
        return plugin[PLUGIN_EXECUTOR_KEY] == HOST_AGENT


cloudify_node_template_relationships_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTemplateRelationships,
    new_element=CloudifyNodeTemplateRelationships)

cloudify_node_type_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTypes,
    new_element=CloudifyNodeTypes)

cloudify_blueprint_schema_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Blueprint,
    new_element=PolicyTriggers,
    schema_key='policy_triggers')

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
