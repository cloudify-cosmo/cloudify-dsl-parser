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

import collections

import testtools.testcase

from dsl_parser import constants
from dsl_parser import exceptions
from dsl_parser import functions
from dsl_parser.tasks import prepare_deployment_plan
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestGetAttribute(AbstractTestParser):

    def test_has_intrinsic_functions_property(self):
        yaml = """
relationships:
    cloudify.relationships.contained_in: {}
plugins:
    p:
        executor: central_deployment_agent
        install: false
node_types:
    webserver_type: {}
node_templates:
    node:
        type: webserver_type
    webserver:
        type: webserver_type
        interfaces:
            test:
                op_with_no_get_attribute:
                    implementation: p.p
                    inputs:
                        a: 1
                op_with_get_attribute:
                    implementation: p.p
                    inputs:
                        a: { get_attribute: [SELF, a] }
        relationships:
            -   type: cloudify.relationships.contained_in
                target: node
                source_interfaces:
                    test:
                        op_with_no_get_attribute:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_attribute:
                            implementation: p.p
                            inputs:
                                a: { get_attribute: [SOURCE, a] }
                target_interfaces:
                    test:
                        op_with_no_get_attribute:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_attribute:
                            implementation: p.p
                            inputs:
                                a: { get_attribute: [TARGET, a] }
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        webserver_node = None
        for node in parsed.node_templates:
            if node['id'] == 'webserver':
                webserver_node = node
                break
        self.assertIsNotNone(webserver_node)

        def assertion(operations):
            op = operations['test.op_with_no_get_attribute']
            self.assertIs(False, op.get('has_intrinsic_functions'))
            op = operations['test.op_with_get_attribute']
            self.assertIs(True, op.get('has_intrinsic_functions'))

        assertion(webserver_node['operations'])
        assertion(webserver_node['relationships'][0]['source_operations'])
        assertion(webserver_node['relationships'][0]['target_operations'])


class TestEvaluateFunctions(AbstractTestParser):

    def test_evaluate_functions(self):

        def get_node_instances(node_id=None):
            return [get_node_instance(node_id)]

        def get_node_instance(node_instance_id):
            result = NodeInstance({
                'id': node_instance_id,
                'node_id': 'webserver',
                'runtime_properties': {
                }
            })
            if node_instance_id == 'node1':
                result.runtime_properties['a'] = 'a_val'
            elif node_instance_id == 'node2':
                result.runtime_properties['b'] = 'b_val'
            elif node_instance_id == 'node3':
                result.runtime_properties['c'] = 'c_val'
            elif node_instance_id == 'node4':
                result.runtime_properties['d'] = 'd_val'
            return result

        def get_node(node_id):
            return Node({
                'id': node_id,
            })

        payload = {
            'a': {'get_attribute': ['SELF', 'a']},
            'b': {'get_attribute': ['node2', 'b']},
            'c': {'get_attribute': ['SOURCE', 'c']},
            'd': {'get_attribute': ['TARGET', 'd']},
            'f': {'concat': [
                {'get_attribute': ['SELF', 'a']},
                {'get_attribute': ['node2', 'b']},
                {'get_attribute': ['SOURCE', 'c']},
                {'get_attribute': ['TARGET', 'd']}
            ]}
        }

        context = {
            'self': 'node1',
            'source': 'node3',
            'target': 'node4'
        }

        functions.evaluate_functions(payload,
                                     context,
                                     get_node_instances,
                                     get_node_instance,
                                     get_node,
                                     None)

        self.assertEqual(payload['a'], 'a_val')
        self.assertEqual(payload['b'], 'b_val')
        self.assertEqual(payload['c'], 'c_val')
        self.assertEqual(payload['d'], 'd_val')
        self.assertEqual(payload['f'], 'a_valb_valc_vald_val')

    def test_process_attribute_relationship_ambiguity_resolution(self):

        node_instances = {
            'node1_1': {
                'node_id': 'node1',
                'relationships': [
                    {'target_name': 'node2', 'target_id': 'node2_1'}
                ]
            },
            'node2_1': {
                'node_id': 'node2',
                'runtime_properties': {
                    'key': 'value1'
                }
            },
            'node2_2': {
                'node_id': 'node2',
                'runtime_properties': {
                    'key': 'value2'
                }
            }
        }

        node_instances = dict(
            (node_instance_id, NodeInstance(node_instance))
            for node_instance_id, node_instance in node_instances.items())

        nodes = {}

        node_to_node_instances = collections.defaultdict(list)
        for node_instance_id, node_instance in node_instances.items():
            nodes[node_instance.node_id] = Node({})
            node_instance['id'] = node_instance_id
            node_to_node_instances[node_instance.node_id].append(node_instance)

        def get_node_instances(node_id):
            return node_to_node_instances[node_id]

        def get_node_instance(node_instance_id):
            return node_instances[node_instance_id]

        def get_node(node_id):
            return nodes[node_id]

        def evaluate():
            payload = {'a': {'get_attribute': ['node2', 'key']}}
            context = {'self': 'node1_1'}
            functions.evaluate_functions(payload,
                                         context,
                                         get_node_instances,
                                         get_node_instance,
                                         get_node,
                                         None)
            return payload

        payload = evaluate()
        self.assertEqual(payload['a'], 'value1')

        # sanity
        node_instances['node1_1']['relationships'] = []
        self.assertRaises(exceptions.FunctionEvaluationError, evaluate)

    def test_process_attribute_scaling_group_ambiguity_resolution_node_operation(self):  # noqa
        for index in [1, 2]:
            context = {'self': 'node3_{0}'.format(index)}
            self._test_process_attribute_scaling_group_ambiguity_resolution(
                context, index)

    def test_process_attribute_scaling_group_ambiguity_resolution_relationship_operation_source(self):  # noqa
        for index in [1, 2]:
            context = {'source': 'node3_{0}'.format(index),
                       'target': 'stub'}
            self._test_process_attribute_scaling_group_ambiguity_resolution(
                context, index)

    def test_process_attribute_scaling_group_ambiguity_resolution_relationship_operation_target(self):  # noqa
        for index in [1, 2]:
            context = {'target': 'node3_{0}'.format(index),
                       'source': 'stub'}

            self._test_process_attribute_scaling_group_ambiguity_resolution(
                context, index)

    def _test_process_attribute_scaling_group_ambiguity_resolution(
            self, context, index):

        node_instances = {
            'node1_1': {
                'node_id': 'node1',
                'scaling_groups': [{'name': 'g1', 'id': 'g1_1'}]
            },

            'node2_1': {
                'node_id': 'node2',
                'scaling_groups': [{'name': 'g2', 'id': 'g2_1'}],
                'relationships': [{
                    'target_name': 'node1',
                    'target_id': 'node1_1'}]
            },

            'node3_1': {
                'node_id': 'node3',
                'scaling_groups': [{'name': 'g3', 'id': 'g3_1'}],
                'relationships': [{
                    'target_name': 'node2',
                    'target_id': 'node2_1'}]
            },

            'node4_1': {
                'node_id': 'node4',
                'scaling_groups': [{'name': 'g1', 'id': 'g1_1'}]
            },

            'node5_1': {
                'node_id': 'node5',
                'scaling_groups': [{'name': 'g5', 'id': 'g5_1'}],
                'relationships': [{
                    'target_name': 'node4',
                    'target_id': 'node4_1'}]
            },

            'node6_1': {
                'node_id': 'node6',
                'scaling_groups': [{'name': 'g6', 'id': 'g6_1'}],
                'relationships': [{
                    'target_name': 'node5',
                    'target_id': 'node5_1'}],
                'runtime_properties': {
                    'key': 'value6_1'
                }
            },

            'node1_2': {
                'node_id': 'node1',
                'scaling_groups': [{'name': 'g1', 'id': 'g1_2'}]
            },

            'node2_2': {
                'node_id': 'node2',
                'scaling_groups': [{'name': 'g2', 'id': 'g2_2'}],
                'relationships': [{
                    'target_name': 'node1',
                    'target_id': 'node1_2'}]
            },

            'node3_2': {
                'node_id': 'node3',
                'scaling_groups': [{'name': 'g3', 'id': 'g3_2'}],
                'relationships': [{
                    'target_name': 'node2',
                    'target_id': 'node2_2'}],
            },

            'node4_2': {
                'node_id': 'node4',
                'scaling_groups': [{'name': 'g1', 'id': 'g1_2'}]
            },

            'node5_2': {
                'node_id': 'node5',
                'scaling_groups': [{'name': 'g5', 'id': 'g5_2'}],
                'relationships': [{
                    'target_name': 'node4',
                    'target_id': 'node4_2'}]
            },

            'node6_2': {
                'node_id': 'node6',
                'scaling_groups': [{'name': 'g6', 'id': 'g6_2'}],
                'relationships': [{
                    'target_name': 'node5',
                    'target_id': 'node5_2'}],
                'runtime_properties': {
                    'key': 'value6_2'
                }
            },
            'stub': {'node_id': 'stub'}
        }

        node_instances = dict(
            (node_instance_id, NodeInstance(node_instance))
            for node_instance_id, node_instance in node_instances.items())

        node_to_node_instances = collections.defaultdict(list)
        for node_instance_id, node_instance in node_instances.items():
            node_instance['id'] = node_instance_id
            node_to_node_instances[node_instance.node_id].append(node_instance)

        nodes = {}
        for node_instance in node_instances.values():
            nodes[node_instance.node_id] = Node({
                'relationships': [
                    {'target_id': r['target_name'],
                     'type_hierarchy': [constants.CONTAINED_IN_REL_TYPE]}
                    for r in node_instance.get('relationships', [])],
            })

        def get_node_instances(node_id):
            return node_to_node_instances[node_id]

        def get_node_instance(node_instance_id):
            return node_instances[node_instance_id]

        def get_node(node_id):
            return nodes[node_id]

        payload = {'a': {'get_attribute': ['node6', 'key']}}
        functions.evaluate_functions(payload,
                                     context,
                                     get_node_instances,
                                     get_node_instance,
                                     get_node,
                                     None)

        self.assertEqual(payload['a'], 'value6_{0}'.format(index))

    def test_process_attributes_properties_fallback(self):

        def get_node_instances(node_id=None):
            return [get_node_instance(node_id)]

        def get_node_instance(node_instance_id):
            return NodeInstance({
                'id': node_instance_id,
                'node_id': 'webserver',
                'runtime_properties': {}
            })

        def get_node(node_id):
            return Node({
                'id': node_id,
                'properties': {
                    'a': 'a_val',
                    'b': 'b_val',
                    'c': 'c_val',
                    'd': 'd_val',
                }
            })

        payload = {
            'a': {'get_attribute': ['SELF', 'a']},
            'b': {'get_attribute': ['node', 'b']},
            'c': {'get_attribute': ['SOURCE', 'c']},
            'd': {'get_attribute': ['TARGET', 'd']},
        }

        context = {
            'self': 'node',
            'source': 'node',
            'target': 'node'
        }

        functions.evaluate_functions(payload,
                                     context,
                                     get_node_instances,
                                     get_node_instance,
                                     get_node,
                                     None)

        self.assertEqual(payload['a'], 'a_val')
        self.assertEqual(payload['b'], 'b_val')
        self.assertEqual(payload['c'], 'c_val')
        self.assertEqual(payload['d'], 'd_val')

    def test_process_attributes_no_value(self):

        def get_node_instances(node_id=None):
            return [get_node_instance(node_id)]

        def get_node_instance(node_instance_id):
            return NodeInstance({
                'id': node_instance_id,
                'node_id': 'webserver',
                'runtime_properties': {}
            })

        def get_node(node_id):
            return Node({
                'id': node_id,
            })

        payload = {
            'a': {'get_attribute': ['node', 'a']},
        }

        functions.evaluate_functions(payload,
                                     {},
                                     get_node_instances,
                                     get_node_instance,
                                     get_node,
                                     None)

        self.assertIsNone(payload['a'])

    def test_missing_self_ref(self):
        payload = {'a': {'get_attribute': ['SELF', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*SELF is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None, None)

    def test_missing_source_ref(self):
        payload = {'a': {'get_attribute': ['SOURCE', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*SOURCE is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None, None)

    def test_missing_target_ref(self):
        payload = {'a': {'get_attribute': ['TARGET', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*TARGET is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None, None)

    def test_no_instances(self):
        def get_node_instances(node_id):
            return []
        payload = {'a': {'get_attribute': ['node', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*does not exist.*'):
            functions.evaluate_functions(payload, {}, get_node_instances, None,
                                         None, None)

    def test_too_many_instances(self):
        instances = [NodeInstance({'id': '1'}), NodeInstance({'id': '2'})]

        def get_node_instances(node_id):
            return instances

        def get_node_instance(node_instance_id):
            return instances[0]

        payload = {'a': {'get_attribute': ['node', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*unambiguously.*'):
            functions.evaluate_functions(payload, {},
                                         get_node_instances,
                                         get_node_instance,
                                         None,
                                         None)


class NodeInstance(dict):

    def __init__(self, values):
        self.update(values)

    @property
    def id(self):
        return self.get('id')

    @property
    def node_id(self):
        return self.get('node_id')

    @property
    def runtime_properties(self):
        return self.get('runtime_properties')

    @property
    def relationships(self):
        return self.get('relationships')

    @property
    def scaling_groups(self):
        return self.get('scaling_groups')


class Node(dict):

    def __init__(self, values):
        self.update(values)

    @property
    def id(self):
        return self.get('id')

    @property
    def properties(self):
        return self.get('properties', {})

    @property
    def relationships(self):
        return self.get('relationships')
