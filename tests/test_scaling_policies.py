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

from aria.exceptions import ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH
from aria.parser.constants import UNBOUNDED
from aria.parser.framework.elements.policies import PolicyInstanceType

from .suite import ParserTestCase


class TestNodeTemplateDefaultScalableProperties(ParserTestCase):
    def test_capabilities_spec_version_validation(self):
        for index in xrange(3):
            self.template.clear()
            self.template.version_section('1.{0}'.format(index))
            self.template.node_type_section()
            self.template.node_template_section()
            self.template += """
        capabilities: {}
    """
            self.assert_parser_raise_exception(
                error_code=ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH)

    def test_groups_parsed_with_no_policies(self):
        self.template.from_members(
            groups={'group': ['node']},
            nodes={'node': None},
        )
        plan = self.parse()
        self.assertEqual(
            {'group': {
                'members': ['node'],
                'policies': {},
            }},
            plan['groups'])

    def test_groups_with_scaling_policies_and_other_policies(self):
        self.template.from_members(
            groups={
                'group': {
                    'members': ['node'],
                    'policies': {
                        'policy': {'type': 'other_type'},
                    },
                },
            },
            nodes={'node': None},
            policy_types={
                'other_type': {
                    'properties': {},
                    'source': 'stub'
                }
            },
            policies={
                'policy': {
                    'type': PolicyInstanceType.SCALING_POLICY,
                    'targets': ['group']
                }
            },
            version='1_3',
        )
        plan = self.parse()
        self.assertEqual({
            'group': {
                'members': ['node'],
                'policies': {
                    'policy': {
                        'type': 'other_type',
                        'properties': {},
                        'triggers': {},
                    },
                },
            },
        }, plan['groups'])
        self.assertEqual({
            'group': {
                'members': ['node'],
                'properties': {
                    'default_instances': 1,
                    'min_instances': 0,
                    'max_instances': UNBOUNDED,
                    'current_instances': 1,
                    'planned_instances': 1,
                },
            },
        }, plan['scaling_groups'])

    def test_validate_policies_spec_version(self):
        nodes = {
            'node': None
        }
        groups = {
            'group': ['node']
        }
        for version in ['1_0', '1_1', '1_2']:
            self.assert_validation(
                ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                groups=groups, nodes=nodes,
                version=version)

    def assert_validation(
            self,
            expected_error_code,
            groups=None,
            nodes=None,
            policies=None,
            version=None):
        if policies is None:
            policies = {
                'policy': {
                    'type': PolicyInstanceType.SCALING_POLICY,
                    'targets': groups.keys(),
                },
            }
        self.template.from_members(
            groups=groups,
            nodes=nodes,
            policies=policies,
            version=version)
        self.assert_parser_raise_exception(error_code=expected_error_code)
