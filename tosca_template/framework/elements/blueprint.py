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

from ... import constants, models
from .. import Value
from .imports import ImportsLoader, Imports
from .version import ToscaDefinitionsVersion
from .misc import DSLDefinitions, Description, Inputs, Outputs
from .plugins import Plugins
from .node_types import NodeTypes
from .relationships import Relationships
from .node_templates import NodeTemplates
from .policies import PolicyTypes, PolicyTriggers, Groups
from .workflows import Workflows
from .data_types import DataTypes
from . import Element


class BlueprintVersionExtractor(Element):
    schema = {
        'tosca_definitions_version': ToscaDefinitionsVersion,
        # here so it gets version validated
        'dsl_definitions': DSLDefinitions,
    }
    requires = {
        ToscaDefinitionsVersion: ['version', Value('plan_version')],
    }

    def parse(self, version, plan_version):
        return {
            'version': version,
            'plan_version': plan_version
        }


class BlueprintImporter(Element):
    schema = {
        'imports': ImportsLoader,
    }
    requires = {
        ImportsLoader: ['resource_base'],
    }

    def parse(self, resource_base):
        return {
            'merged_blueprint': self.child(ImportsLoader).value,
            'resource_base': resource_base,
        }


class Blueprint(Element):
    schema = {
        'tosca_definitions_version': ToscaDefinitionsVersion,
        'description': Description,
        'imports': Imports,
        'dsl_definitions': DSLDefinitions,
        'inputs': Inputs,
        'plugins': Plugins,
        'node_types': NodeTypes,
        'relationships': Relationships,
        'node_templates': NodeTemplates,
        'policy_types': PolicyTypes,
        'policy_triggers': PolicyTriggers,
        'groups': Groups,
        'workflows': Workflows,
        'outputs': Outputs,
        'data_types': DataTypes,
    }
    requires = {
        NodeTemplates: ['deployment_plugins_to_install'],
        Workflows: ['workflow_plugins_to_install'],
    }

    def parse(
            self, workflow_plugins_to_install, deployment_plugins_to_install):
        return models.Plan({
            constants.DEPLOYMENT_PLUGINS_TO_INSTALL:
                deployment_plugins_to_install,
            constants.WORKFLOW_PLUGINS_TO_INSTALL:
                workflow_plugins_to_install,
            constants.DESCRIPTION: self.child(Description).value,
            constants.NODES: self.child(NodeTemplates).value,
            constants.RELATIONSHIPS: self.child(Relationships).value,
            constants.WORKFLOWS: self.child(Workflows).value,
            constants.POLICY_TYPES: self.child(PolicyTypes).value,
            constants.POLICY_TRIGGERS: self.child(PolicyTriggers).value,
            constants.GROUPS: self.child(Groups).value,
            constants.INPUTS: self.child(Inputs).value,
            constants.OUTPUTS: self.child(Outputs).value,
            constants.VERSION: self.child(ToscaDefinitionsVersion).value,
        })
