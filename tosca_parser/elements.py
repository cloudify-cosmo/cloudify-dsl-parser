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

from aria.parser import constants
from aria.parser.models import Plan
from aria.parser.extension_tools import VersionNumber
from aria.parser.exceptions import DSLParsingLogicException
from aria.parser.utils import merge_schema_and_instance_properties
from aria.parser.constants import (
    CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT, PLUGIN_EXECUTOR_KEY)
from aria.parser.framework.elements.imports import ImportsLoader
from aria.parser.framework.elements.policies import Group
from aria.parser.framework.elements.plugins import Plugin
from aria.parser.framework.elements.data_types import Schema, DataTypes
from aria.parser.framework.elements.node_templates import (
    NodeTemplateRelationships, NodeTemplates)
from aria.parser.framework.elements.blueprint import Blueprint
from aria.parser.framework.elements.node_types import NodeTypes
from aria.parser.framework.elements.operation import OperationExecutor
from aria.parser.framework.elements import Element, DictElement, Dict, Leaf
from aria.parser.framework.requirements import Value

POLICY_TRIGGERS = 'policy_triggers'
POLICY_TYPES = 'policy_types'


class CloudifyNodeTemplateRelationships(NodeTemplateRelationships):
    CONTAINED_IN_REL_TYPE = 'cloudify.relationships.contained_in'


class CloudifyNodeTypes(NodeTypes):
    HOST_TYPE = 'cloudify.nodes.Compute'


class CloudifyBlueprint(Blueprint):
    def parse(self, *args, **kwargs):
        return Plan({
            POLICY_TRIGGERS: self.child(PolicyTriggers).value,
            POLICY_TYPES: self.child(PolicyTypes).value,
        }, **super(CloudifyBlueprint, self).parse(*args, **kwargs))


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
    def should_install_plugin_on_compute_node(plugin):
        return plugin[PLUGIN_EXECUTOR_KEY] == HOST_AGENT


class CloudifyImportsLoader(ImportsLoader):
    MERGEABLE_FROM_DSL = [
        constants.INPUTS,
        constants.OUTPUTS,
        constants.NODE_TEMPLATES,
    ]

    def merge_parsed_into_combined(self, **kwargs):
        kwargs['merge_no_override'] = self.MERGE_NO_OVERRIDE.copy()
        version = kwargs['version']
        if version['definitions_version'].number > VersionNumber(1, 2):
            kwargs['merge_no_override'].update(self.MERGEABLE_FROM_DSL)
        super(CloudifyImportsLoader, self).merge_parsed_into_combined(**kwargs)

    def assert_mergeable(self, key_holder):
        if key_holder.value in self.MERGEABLE_FROM_DSL:
            raise DSLParsingLogicException(
                3,
                "Import failed: non-mergeable field: '{0}'. "
                "{0} can be imported multiple times only from "
                "cloudify_dsl_1_3 and above.".format(key_holder.value))
        super(CloudifyImportsLoader, self).assert_mergeable(key_holder)


class PolicyTypeSource(Element):
    required = True
    schema = Leaf(type=str)


class PolicyType(DictElement):
    schema = {
        'properties': Schema,
        'source': PolicyTypeSource,
    }


class PolicyTypes(DictElement):
    schema = Dict(type=PolicyType)


class PolicyTriggerSource(Element):
    required = True
    schema = Leaf(type=str)


class PolicyTrigger(DictElement):
    schema = {
        'parameters': Schema,
        'source': PolicyTriggerSource,
    }


class PolicyTriggers(DictElement):
    schema = Dict(type=PolicyTrigger)


class GroupPolicyTriggerType(Element):
    required = True
    schema = Leaf(type=str)
    requires = {PolicyTriggers: [Value('policy_triggers')]}

    def validate(self, policy_triggers):
        if self.initial_value not in policy_triggers:
            raise DSLParsingLogicException(
                42,
                "Trigger '{0}' of policy '{1}' of group '{2}' "
                "references a non existent "
                "'policy trigger '{3}'"
                .format(self.ancestor(GroupPolicyTrigger).name,
                        self.ancestor(GroupPolicy).name,
                        self.ancestor(Group).name,
                        self.initial_value))


class GroupPolicyTriggerParameters(Element):
    schema = Leaf(type=dict)
    requires = {
        GroupPolicyTriggerType: [],
        PolicyTriggers: [Value('policy_triggers')],
        DataTypes: [Value('data_types')],
    }

    def parse(self, policy_triggers, data_types):
        trigger_type = policy_triggers[
            self.sibling(GroupPolicyTriggerType).value]
        policy_trigger_parameters = trigger_type.get('parameters', {})
        return merge_schema_and_instance_properties(
            self.initial_value or {},
            policy_trigger_parameters,
            data_types,
            "{0} '{1}' property is not part of "
            "the policy type properties schema",
            "{0} does not provide a value for mandatory "
            "'{1}' property which is "
            "part of its policy type schema",
            node_name="group '{0}', policy '{1}' trigger '{2}'"
                      .format(self.ancestor(Group).name,
                              self.ancestor(GroupPolicy).name,
                              self.ancestor(GroupPolicyTrigger).name))


class GroupPolicyTrigger(DictElement):
    schema = {
        'type': GroupPolicyTriggerType,
        'parameters': GroupPolicyTriggerParameters,
    }


class GroupPolicyType(Element):
    required = True
    schema = Leaf(type=str)
    requires = {PolicyTypes: [Value('policy_types')]}

    def validate(self, policy_types):
        if self.initial_value not in policy_types:
            raise DSLParsingLogicException(
                41,
                "Policy '{0}' of group '{1}' references a non existent "
                "policy type '{2}'".format(
                    self.ancestor(GroupPolicy).name,
                    self.ancestor(Group).name,
                    self.initial_value))


class GroupPolicyProperties(Element):
    schema = Leaf(type=dict)
    requires = {
        GroupPolicyType: [],
        PolicyTypes: [Value('policy_types')],
        DataTypes: [Value('data_types')],
    }

    def parse(self, policy_types, data_types):
        policy_type = policy_types[self.sibling(GroupPolicyType).value]
        policy_type_properties = policy_type.get('properties', {})
        return merge_schema_and_instance_properties(
            self.initial_value or {},
            policy_type_properties,
            data_types,
            "{0} '{1}' property is not part of "
            "the policy type properties schema",
            "{0} does not provide a value for mandatory "
            "'{1}' property which is "
            "part of its policy type schema",
            node_name="group '{0}', policy '{1}'".format(
                self.ancestor(Group).name,
                self.ancestor(GroupPolicy).name))


class GroupPolicyTriggers(DictElement):
    schema = Dict(type=GroupPolicyTrigger)


class GroupPolicy(DictElement):
    schema = {
        'type': GroupPolicyType,
        'properties': GroupPolicyProperties,
        'triggers': GroupPolicyTriggers,
    }


class GroupPolicies(DictElement):
    required = True
    schema = Dict(type=GroupPolicy)
