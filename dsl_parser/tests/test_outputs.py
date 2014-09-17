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

from dsl_parser import exceptions
from dsl_parser import functions
from dsl_parser.parser import DSLParsingFormatException
from dsl_parser.tasks import prepare_deployment_plan
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestOutputs(AbstractTestParser):

    def test_outputs_definition(self):
        yaml = """
node_templates: {}
outputs: {}
"""
        parsed = self.parse(yaml)
        self.assertEqual(0, len(parsed['outputs']))

    def test_outputs_valid_output(self):
        yaml = """
node_templates: {}
outputs:
    port0:
        description: p0
        value: 1234
    port1:
        description: p1
        value: some_port
    port2:
        description: p2
        value: {}
    port3:
        description: p3
        value: []
    port4:
        description: p4
        value: false
"""
        parsed = self.parse(yaml)
        outputs = parsed['outputs']
        self.assertEqual(5, len(parsed['outputs']))
        self.assertEqual('p0', outputs['port0']['description'])
        self.assertEqual(1234, outputs['port0']['value'])
        self.assertEqual('p1', outputs['port1']['description'])
        self.assertEqual('some_port', outputs['port1']['value'])
        self.assertEqual('p2', outputs['port2']['description'])
        self.assertEqual({}, outputs['port2']['value'])
        self.assertEqual('p3', outputs['port3']['description'])
        self.assertEqual([], outputs['port3']['value'])
        self.assertEqual('p4', outputs['port4']['description'])
        self.assertFalse(outputs['port4']['value'])
        prepared = prepare_deployment_plan(parsed)
        self.assertEqual(parsed['outputs'], prepared['outputs'])

    def test_invalid_outputs(self):
        yaml = """
node_templates: {}
outputs:
    port:
        description: p0
"""
        self.assertRaises(DSLParsingFormatException, self.parse, yaml)

    def test_valid_get_attribute(self):
        yaml = """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        parsed = self.parse(yaml)
        outputs = parsed['outputs']
        func = functions.parse(outputs['port']['value'])
        self.assertTrue(isinstance(func, functions.GetAttribute))
        self.assertEqual('webserver', func.node_name)
        self.assertEqual('port', func.attribute_name)
        prepared = prepare_deployment_plan(parsed)
        self.assertEqual(parsed['outputs'], prepared['outputs'])

    def test_invalid_get_attribute(self):
        yaml = """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        try:
            self.parse(yaml)
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))
        yaml = """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: aaa }
"""
        try:
            self.parse(yaml)
            self.fail('Expected exception.')
        except ValueError, e:
            self.assertTrue('Illegal arguments passed' in str(e))

    def test_invalid_nested_get_attribute(self):
        yaml = """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    endpoint:
        description: p0
        value:
            ip: 10.0.0.1
            port: { get_attribute: [ aaa, port ] }
"""
        try:
            self.parse(yaml)
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))

    def test_valid_evaluation(self):
        yaml = """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        parsed = self.parse(yaml)

        def get_node_instances():
            return [
                NodeInstance({
                    'node_id': 'webserver',
                    'runtime_properties': {
                        'port': 8080
                    }
                })
            ]
        o = functions.evaluate_outputs(parsed['outputs'], get_node_instances)
        self.assertEqual(8080, o['port'])

    def test_unknown_node_instance_evaluation(self):
        yaml = """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        parsed = self.parse(yaml)

        def get_node_instances():
            return []

        try:
            functions.evaluate_outputs(parsed['outputs'], get_node_instances)
            self.fail()
        except exceptions.FunctionEvaluationError, e:
            self.assertIn('Node specified in function does not exist', str(e))
            self.assertIn('webserver', str(e))

    def test_invalid_multi_instance_evaluation(self):
        yaml = """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        parsed = self.parse(yaml)

        def get_node_instances():
            node_instance = NodeInstance({
                'node_id': 'webserver',
                'runtime_properties': {
                    'port': 8080
                }
            })
            return [node_instance, node_instance]

        try:
            functions.evaluate_outputs(parsed['outputs'], get_node_instances)
            self.fail()
        except exceptions.FunctionEvaluationError, e:
            self.assertIn('Multi instances of node', str(e))
            self.assertIn('webserver', str(e))


class NodeInstance(dict):

    def __init__(self, values):
        self.update(values)

    @property
    def node_id(self):
        return self.get('node_id')

    @property
    def runtime_properties(self):
        return self.get('runtime_properties')
