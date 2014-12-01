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


import testtools.testcase

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
            'e': {'fn.join': [':', [
                {'get_attribute': ['SELF', 'a']},
                {'get_attribute': ['node2', 'b']},
                {'get_attribute': ['SOURCE', 'c']},
                {'get_attribute': ['TARGET', 'd']}
            ]]},
            'f': {'fn.concat': [
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
                                     get_node)

        self.assertEqual(payload['a'], 'a_val')
        self.assertEqual(payload['b'], 'b_val')
        self.assertEqual(payload['c'], 'c_val')
        self.assertEqual(payload['d'], 'd_val')
        self.assertEqual(payload['e'], 'a_val:b_val:c_val:d_val')
        self.assertEqual(payload['f'], 'a_valb_valc_vald_val')

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
                                     get_node)

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
                                     get_node)

        self.assertIsNone(payload['a'])

    def test_missing_self_ref(self):
        payload = {'a': {'get_attribute': ['SELF', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*SELF is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None)

    def test_missing_source_ref(self):
        payload = {'a': {'get_attribute': ['SOURCE', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*SOURCE is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None)

    def test_missing_target_ref(self):
        payload = {'a': {'get_attribute': ['TARGET', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*TARGET is missing.*'):
            functions.evaluate_functions(payload, {}, None, None, None)

    def test_no_instances(self):
        def get_node_instances(node_id):
            return []
        payload = {'a': {'get_attribute': ['node', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*does not exist.*'):
            functions.evaluate_functions(payload, {}, get_node_instances, None,
                                         None)

    def test_too_many_instances(self):
        def get_node_instances(node_id):
            return [1, 1]
        payload = {'a': {'get_attribute': ['node', 'a']}}
        with testtools.testcase.ExpectedException(
                exceptions.FunctionEvaluationError,
                '.*Multi instances.*'):
            functions.evaluate_functions(payload, {}, get_node_instances, None,
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


class Node(dict):

    def __init__(self, values):
        self.update(values)

    @property
    def id(self):
        return self.get('id')

    @property
    def properties(self):
        return self.get('properties', {})
