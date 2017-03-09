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

from dsl_parser import functions
from dsl_parser.tasks import prepare_deployment_plan
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestGetSecret(AbstractTestParser):

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
                op_with_no_get_secret:
                    implementation: p.p
                    inputs:
                        a: 1
                op_with_get_secret:
                    implementation: p.p
                    inputs:
                        a: { get_secret: node_template_secret_id }
        relationships:
            -   type: cloudify.relationships.contained_in
                target: node
                source_interfaces:
                    test:
                        op_with_no_get_secret:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_secret:
                            implementation: p.p
                            inputs:
                                a: { get_secret: source_op_secret_id }
                target_interfaces:
                    test:
                        op_with_no_get_secret:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_secret:
                            implementation: p.p
                            inputs:
                                a: { get_secret: target_op_secret_id }
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        webserver_node = None
        for node in parsed.node_templates:
            if node['id'] == 'webserver':
                webserver_node = node
                break
        self.assertIsNotNone(webserver_node)

        def assertion(operations):
            op = operations['test.op_with_no_get_secret']
            self.assertIs(False, op.get('has_intrinsic_functions'))
            op = operations['test.op_with_get_secret']
            self.assertIs(True, op.get('has_intrinsic_functions'))

        assertion(webserver_node['operations'])
        assertion(webserver_node['relationships'][0]['source_operations'])
        assertion(webserver_node['relationships'][0]['target_operations'])


class TestEvaluateFunctions(AbstractTestParser):

    def test_evaluate_functions(self):

        payload = {
            'a': {'get_secret': 'id_a'},
            'b': {'get_secret': 'id_b'},
            'c': {'get_secret': 'id_c'},
            'd': {'get_secret': 'id_d'},
            'f': {'concat': [
                {'get_secret': 'id_a'},
                {'get_secret': 'id_b'},
                {'get_secret': 'id_c'},
                {'get_secret': 'id_d'}
            ]}
        }

        functions.evaluate_functions(payload,
                                     {},
                                     None,
                                     None,
                                     None,
                                     self._get_secret_mock)

        self.assertEqual(payload['a'], 'id_a_value')
        self.assertEqual(payload['b'], 'id_b_value')
        self.assertEqual(payload['c'], 'id_c_value')
        self.assertEqual(payload['d'], 'id_d_value')
        self.assertEqual(payload['f'], 'id_a_valueid_b_value'
                                       'id_c_valueid_d_value')

    def test_node_template_properties_simple(self):
        yaml = """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: { get_secret: secret }
"""
        parsed = prepare_deployment_plan(self.parse_1_3(yaml))
        node = self.get_node_by_name(parsed, 'node')
        self.assertEqual({'get_secret': 'secret'},
                         node['properties']['property'])

        functions.evaluate_functions(
            parsed,
            {},
            None,
            None,
            None,
            self._get_secret_mock
        )
        self.assertEqual(node['properties']['property'], 'secret_value')
