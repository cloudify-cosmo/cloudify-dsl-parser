########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

import yaml

from dsl_parser import constants
from dsl_parser import exceptions
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestScalingPoliciesAndGroups(AbstractTestParser):

    def test_scaling_policy_and_group_default_properties(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group']
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': constants.UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_empty_properties(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group'],
            'properties': {}
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': constants.UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_groups_default_instances(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'default_instances': 3
            }
        }
        expected = {
            'default_instances': 3,
            'min_instances': 0,
            'max_instances': constants.UNBOUNDED,
            'current_instances': 3,
            'planned_instances': 3
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_max_instances(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'max_instances': 3,
            }
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': 3,
            'current_instances': 1,
            'planned_instances': 1
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_min_instances(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'min_instances': 1,
            }
        }
        expected = {
            'default_instances': 1,
            'min_instances': 1,
            'max_instances': constants.UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_unbounded_literal(self):
        policy = {
            'type': constants.SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'max_instances': constants.UNBOUNDED_LITERAL,
            }
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': constants.UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def assert_scaling_policy_and_group(self, policy, expected):
        policies = {'policy': policy}
        blueprint = base_blueprint(groups={'group': ['node']},
                                   nodes={'node': None},
                                   policies=policies)
        plan = self.parse(blueprint)
        self.assertEqual(
            expected,
            plan['policies']['policy']['properties'])
        self.assertEqual(
            expected,
            plan['scaling_groups']['group']['properties'])


class TestScalingPoliciesAndGroupsExtra(AbstractTestParser):

    def test_groups_parsed_with_no_policies(self):
        groups = {'group': ['node']}
        nodes = {'node': None}
        blueprint = base_blueprint(groups=groups, nodes=nodes,
                                   include_policies=False)
        plan = self.parse(blueprint)
        self.assertEqual({
            'group': {
                'members': ['node'],
                'policies': {}
            }
        }, plan['groups'])

    def test_groups_with_scaling_policies_and_other_policies(self):
        groups = {'group': {
            'members': ['node'],
            'policies': {
                'policy': {
                    'type': 'other_type'
                }
            }
        }}
        nodes = {'node': None}
        policy_types = {
            'other_type': {
                'properties': {},
                'source': 'stub'
            }
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group']
            }
        }
        blueprint = base_blueprint(groups=groups, nodes=nodes,
                                   policy_types=policy_types,
                                   policies=policies)
        plan = self.parse(blueprint)
        self.assertEqual({
            'group': {
                'members': ['node'],
                'policies': {
                    'policy': {
                        'type': 'other_type',
                        'properties': {},
                        'triggers': {}
                    }
                }
            }
        }, plan['groups'])
        self.assertEqual({
            'group': {
                'members': ['node'],
                'properties': {
                    'default_instances': 1,
                    'min_instances': 0,
                    'max_instances': constants.UNBOUNDED,
                    'current_instances': 1,
                    'planned_instances': 1
                }
            }
        }, plan['scaling_groups'])

    def test_group_as_group_member(self):
        nodes = {'node': None}
        groups = {
            'group': ['node'],
            'group2': ['group']
        }
        blueprint = base_blueprint(groups=groups, nodes=nodes)
        plan = self.parse(blueprint)
        self.assertEqual(['node'], plan['groups']['group']['members'])
        self.assertEqual(['group'], plan['groups']['group2']['members'])


class TestRemovedContainedInMember(AbstractTestParser):

    def test_removed_contained_in_member1(self):
        groups = {
            'group': ['node1', 'node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1'
        }
        expected = {
            'group': ['node1']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member2(self):
        groups = {
            'group1': ['node1', 'group2'],
            'group2': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
        }
        expected = {
            'group1': ['node1'],
            'group2': ['node2']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member3(self):
        groups = {
            'group': ['node1', 'node3'],
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node2'
        }
        expected = {
            'group': ['node1']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member4(self):
        groups = {
            'group': ['node1', 'group2'],
            'group2': ['group3'],
            'group3': ['node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node2'
        }
        expected = {
            'group': ['node1'],
            'group2': ['group3'],
            'group3': ['node3']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member5(self):
        groups = {
            'group': ['group2'],
            'group2': ['node1', 'node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
        }
        expected = {
            'group': ['group2'],
            'group2': ['node1']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member6(self):
        groups = {
            'group1': ['group2', 'group3', 'node4'],
            'group2': ['node1'],
            'group3': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node1',
            'node4': None
        }
        expected = {
            'group1': ['group2', 'node4'],
            'group2': ['node1'],
            'group3': ['node2', 'node3']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member7(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node1', 'node2', 'node3', 'group3'],
            'group3': ['node4']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None,
            'node4': None
        }
        expected = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3'],
            'group3': ['node4']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member8(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3', 'group4'],
            'group3': ['node4'],
            'group4': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None,
            'node4': None
        }
        expected = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3'],
            'group3': ['node4'],
            'group4': ['node2']
        }
        self.assert_removal(groups, nodes, expected)

    def assert_removal(self, groups, nodes, expected):
        blueprint = base_blueprint(groups=groups, nodes=nodes)
        plan = self.parse(blueprint)
        for group, expected_members in expected.items():
            self.assertEqual(set(expected_members),
                             set(plan['scaling_groups'][group]['members']))


class TestScalingPoliciesAndGroupsValidation(AbstractTestParser):

    def test_missing_policy_type(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'targets': ['group']
            }
        }
        self.assert_validation(expected_error_code=1,
                               groups=groups,
                               nodes=nodes,
                               policies=policies)

    def test_non_scaling_policy_type(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': 'some_policy',
                'targets': ['group']
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_UNSUPPORTED_POLICY,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_non_group_target(self):
        nodes = {'node': None}
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['node']
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_NON_GROUP_TARGET,
            policies=policies,
            nodes=nodes)

    def test_no_targets(self):
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY
            }
        }
        self.assert_validation(
            expected_error_code=1,
            policies=policies)

    def test_empty_targets(self):
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': []
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_NO_TARGETS,
            policies=policies)

    def test_invalid_min_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'min_instances': -1
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_max_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'max_instances': 0
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_max_instances_string_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'max_instances': 'illegal_value'
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_LITERAL_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_default_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': -1
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_min_instances_greater_than_max_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'min_instances': 5,
                    'max_instances': 1,
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_default_instances_greater_than_max_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': 5,
                    'max_instances': 4,
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_default_instances_smaller_than_min_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': constants.SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': 2,
                    'min_instances': 4,
                }
            }
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_INVALID_INSTANCES,
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_validate_no_group_cycles1(self):
        groups = {
            'group1': ['group2'],
            'group2': ['group1']
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_GROUP_CYCLE,
            groups=groups)

    def test_validate_no_group_cycles2(self):
        groups = {
            'group1': ['group2'],
            'group2': ['group3'],
            'group3': ['group4'],
            'group4': ['group1'],
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_GROUP_CYCLE,
            groups=groups)

    def test_validate_node_type_group_members_in_one_group_only(self):
        groups = {
            'group1': ['node'],
            'group2': ['node']
        }
        nodes = {
            'node': None
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_MULTIPLE_GROUPS,
            groups=groups,
            nodes=nodes)

    def test_validate_group_type_group_members_in_one_group_only(self):
        groups = {
            'group1': ['node'],
            'group2': ['group1'],
            'group3': ['group1']
        }
        nodes = {
            'node': None
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_MULTIPLE_GROUPS,
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members1(self):
        groups = {
            'group': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_NON_CONTAINED_GROUP_MEMBERS,
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members2(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_NON_CONTAINED_GROUP_MEMBERS,
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members3(self):
        groups = {
            'group1': ['node4', 'group2'],
            'group2': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node1',
            'node4': None
        }
        self.assert_validation(
            expected_error_code=exceptions.ERROR_NON_CONTAINED_GROUP_MEMBERS,
            groups=groups,
            nodes=nodes)

    def test_validate_policies_spec_version(self):
        nodes = {
            'node': None
        }
        groups = {
            'group': ['node']
        }
        for version in ['1_0', '1_1', '1_2']:
            self.assert_validation(
                exceptions.ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                groups=groups, nodes=nodes,
                version=version)

    def test_validate_illegal_instances_dict_value(self):
        nodes = {
            'node': None
        }
        groups = {
            'group': ['node']
        }
        for instances in ['default', 'min', 'max']:
            policies = {
                'policy': {
                    'type': constants.SCALING_POLICY,
                    'targets': ['group'],
                    'properties': {
                        '{0}_instances'.format(instances): {},
                    }
                }
            }
            self.assert_validation(
                exceptions.ERROR_INVALID_DICT_VALUE,
                groups=groups, nodes=nodes, policies=policies)

    def test_validate_group_and_node_template_same_name(self):
        groups = {
            'node1': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': None,
        }
        expected_code = exceptions.ERROR_GROUP_AND_NODE_TEMPLATE_SAME_NAME
        self.assert_validation(
            expected_error_code=expected_code,
            groups=groups,
            nodes=nodes)

    def assert_validation(self, expected_error_code,
                          groups=None, nodes=None, policies=None,
                          version=None):
        blueprint = base_blueprint(groups=groups, nodes=nodes,
                                   policies=policies,
                                   version=version)
        self._assert_dsl_parsing_exception_error_code(
            blueprint, expected_error_code=expected_error_code)


class TestNodeTemplateDefaultScalableProperties(AbstractTestParser):

    def test_default_scalable(self):
        self.assert_scalable_properties(self.MINIMAL_BLUEPRINT)

    def test_default_scalable_empty_capabilities(self):
        self.assert_scalable_properties(self.MINIMAL_BLUEPRINT + """
        capabilities: {}
""")

    def test_default_scalable_empty_scalable(self):
        self.assert_scalable_properties(self.MINIMAL_BLUEPRINT + """
        capabilities:
            scalable: {}
""")

    def test_default_scalable_single_property_defined(self):
        self.assert_scalable_properties(self.MINIMAL_BLUEPRINT + """
        capabilities:
            scalable:
                properties:
                    default_instances: 2
""", expected_default=2)

    def test_instances_deploy_fallback(self):
        # tests backwards compatibility
        self.assert_scalable_properties(self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: 2
""", expected_default=2)

    def assert_scalable_properties(self, blueprint, expected_default=1):
        plan = self.parse_1_3(blueprint)
        self.assertEquals({
            'default_instances': expected_default,
            'min_instances': 0,
            'max_instances': constants.UNBOUNDED,
            'current_instances': expected_default,
            'planned_instances': expected_default
        }, plan['nodes'][0]['capabilities']['scalable']['properties'])

    def test_capabilities_spec_version_validation(self):
        blueprint = self.MINIMAL_BLUEPRINT + """
        capabilities: {}
"""
        for parsing_method in [self.parse_1_0, self.parse_1_1, self.parse_1_2]:
            self._assert_dsl_parsing_exception_error_code(
                blueprint,
                exceptions.ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH,
                parsing_method=parsing_method)

    def test_capabilities_and_instances_deploy_validation(self):
        blueprint = self.MINIMAL_BLUEPRINT + """
        instances:
          deploy: 1
        capabilities: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            blueprint,
            exceptions.ERROR_INSTANCES_DEPLOY_AND_CAPABILITIES,
            parsing_method=self.parse_1_3)


def base_blueprint(groups=None,
                   nodes=None,
                   policies=None,
                   include_policies=True,
                   policy_types=None,
                   version=None):
    version = version or '1_3'
    version = 'cloudify_dsl_{0}'.format(version)
    groups = groups or {}
    nodes = nodes or {'node': None}
    node_templates = {}
    for node, contained_in in nodes.items():
        node_template = {'type': 'type'}
        if contained_in:
            node_template['relationships'] = [
                {'type': 'cloudify.relationships.contained_in',
                 'target': contained_in}
            ]
        node_templates[node] = node_template
    blueprint_groups = {}
    for group, item in groups.items():
        if isinstance(item, dict):
            group_obj = item
        else:
            group_obj = {'members': item}
        blueprint_groups[group] = group_obj
    if policies is None:
        policies = {'policy': {'type': constants.SCALING_POLICY,
                               'targets': groups.keys()}}
    blueprint = {
        'tosca_definitions_version': version,
        'node_types': {'type': {}},
        'relationships': {'cloudify.relationships.contained_in': {}},
        'node_templates': node_templates,
        'groups': blueprint_groups,
    }
    if include_policies:
        blueprint['policies'] = policies
    if policy_types is not None:
        blueprint['policy_types'] = policy_types
    return yaml.safe_dump(blueprint)
