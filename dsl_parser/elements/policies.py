########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

from dsl_parser import (exceptions,
                        utils)
from dsl_parser.elements import (node_templates,
                                 data_types)
from dsl_parser.framework.requirements import Value
from dsl_parser.framework.elements import (DictElement,
                                           Element,
                                           Leaf,
                                           List,
                                           Dict)


class PolicyTriggerSource(Element):

    required = True
    schema = Leaf(type=str)


class PolicyTrigger(DictElement):

    schema = {
        'parameters': data_types.Schema,
        'source': PolicyTriggerSource,
    }


class PolicyTypeSource(Element):

    required = True
    schema = Leaf(type=str)


class PolicyType(DictElement):

    schema = {
        'properties': data_types.Schema,
        'source': PolicyTypeSource,
    }


class PolicyTypes(DictElement):

    schema = Dict(type=PolicyType)


class PolicyTriggers(DictElement):

    schema = Dict(type=PolicyTrigger)


class GroupPolicyType(Element):

    required = True
    schema = Leaf(type=str)
    requires = {
        PolicyTypes: [Value('policy_types')]
    }

    def validate(self, policy_types):
        if self.initial_value not in policy_types:
            raise exceptions.DSLParsingLogicException(
                41,
                "Policy '{0}' of group '{1}' references a non existent "
                "policy type '{2}'"
                .format(self.ancestor(GroupPolicy).name,
                        self.ancestor(Group).name,
                        self.initial_value))


class GroupPolicyProperties(Element):

    schema = Leaf(type=dict)
    requires = {
        GroupPolicyType: [],
        PolicyTypes: [Value('policy_types')],
        data_types.DataTypes: [Value('data_types')]
    }

    def parse(self, policy_types, data_types):
        policy_type = policy_types[self.sibling(GroupPolicyType).value]
        policy_type_properties = policy_type.get('properties', {})
        return utils.merge_schema_and_instance_properties(
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


class GroupPolicyTriggerType(Element):

    required = True
    schema = Leaf(type=str)
    requires = {
        PolicyTriggers: [Value('policy_triggers')]
    }

    def validate(self, policy_triggers):
        if self.initial_value not in policy_triggers:
            raise exceptions.DSLParsingLogicException(
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
        data_types.DataTypes: [Value('data_types')]
    }

    def parse(self, policy_triggers, data_types):
        trigger_type = policy_triggers[
            self.sibling(GroupPolicyTriggerType).value]
        policy_trigger_parameters = trigger_type.get('parameters', {})
        return utils.merge_schema_and_instance_properties(
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


class GroupPolicyTriggers(DictElement):

    schema = Dict(type=GroupPolicyTrigger)


class GroupPolicy(DictElement):

    schema = {
        'type': GroupPolicyType,
        'properties': GroupPolicyProperties,
        'triggers': GroupPolicyTriggers,
    }


class GroupMember(Element):

    schema = Leaf(type=basestring)
    requires = {
        node_templates.NodeTemplates: ['node_template_names']
    }

    def validate(self, node_template_names):
        if self.initial_value not in node_template_names:
            raise exceptions.DSLParsingLogicException(
                40,
                "Member '{0}' of group '{1}' does not "
                "match any defined node".format(
                    self.initial_value,
                    self.ancestor(Group).name))


class GroupMembers(Element):

    required = True
    schema = List(type=GroupMember)

    def validate(self):
        if len(self.children()) < 1:
            raise exceptions.DSLParsingFormatException(
                1, "At least one member should be specified")

    def parse(self):
        # ensure uniqueness
        return list(set([c.value for c in self.children()]))


class GroupPolicies(DictElement):

    required = True
    schema = Dict(type=GroupPolicy)


class Group(DictElement):

    schema = {
        'members': GroupMembers,
        'policies': GroupPolicies,
    }


class Groups(DictElement):

    schema = Dict(type=Group)
