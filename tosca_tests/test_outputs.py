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

from unittest import skip

from tosca_parser.exceptions import (
    DSLParsingFormatException, FunctionEvaluationError,
)
from tosca_parser.functions import (
    parse, GetAttribute, evaluate_outputs,
)
# from dsl_parser.tasks import prepare_deployment_plan

from .suite import ParserTestCase


class TestOutputs(ParserTestCase):
    def test_outputs_definition(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs: {}
"""
        parsed = self.parse()
        self.assertEqual(0, len(parsed['outputs']))

    @skip('is not implemented yet')
    def test_outputs_valid_output(self):
        self.template.version_section('1.0')
        self.template += """
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
        parsed = self.parse()
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
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
"""
        self.assertRaises(DSLParsingFormatException, self.parse)

    @skip('is not implemented yet')
    def test_valid_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
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
        parsed = self.parse()
        outputs = parsed['outputs']
        func = parse(outputs['port']['value'])
        self.assertTrue(isinstance(func, GetAttribute))
        self.assertEqual('webserver', func.node_name)
        self.assertEqual('port', func.attribute_path[0])
        prepared = prepare_deployment_plan(parsed)
        self.assertEqual(parsed['outputs'], prepared['outputs'])

    def test_invalid_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        try:
            self.parse()
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))

        self.template.clear()
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: aaa }
"""
        try:
            self.parse()
            self.fail('Expected exception.')
        except ValueError, e:
            self.assertTrue('Illegal arguments passed' in str(e))

    def test_invalid_nested_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
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
            self.parse()
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))

    @skip('is not implemented yet')
    def test_valid_evaluation(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    input:
        default: input_value
node_types:
    webserver_type:
        properties:
            property:
                default: property_value
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
    endpoint:
        value:
            port: { get_attribute: [ webserver, port ] }
    concatenated:
        value: { concat: [one,
                          {get_property: [webserver, property]},
                          {get_attribute: [webserver, attribute]},
                          {get_input: input},
                          five] }
"""

        def assertion(tested):
            self.assertEqual('one', tested[0])
            self.assertEqual('property_value', tested[1])
            self.assertEqual({'get_attribute': ['webserver', 'attribute']},
                             tested[2])
            self.assertEqual('input_value', tested[3])
            self.assertEqual('five', tested[4])

        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        concatenated = parsed['outputs']['concatenated']['value']['concat']
        assertion(concatenated)

        def get_node_instances(node_id=None):
            return [
                NodeInstance({
                    'id': 'webserver1',
                    'node_id': 'webserver',
                    'runtime_properties': {
                        'port': 8080,
                        'attribute': 'attribute_value',
                    }
                })
            ]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        o = evaluate_outputs(parsed['outputs'],
                             get_node_instances,
                             get_node_instance,
                             get_node)
        self.assertEqual(8080, o['port'])
        self.assertEqual(8080, o['endpoint']['port'])
        self.assertEqual('oneproperty_valueattribute_valueinput_valuefive',
                         o['concatenated'])

    def test_unknown_node_instance_evaluation(self):
        self.template.version_section('1.0')
        self.template += """
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
        parsed = self.parse()

        def get_node_instances(node_id=None):
            return []

        try:
            evaluate_outputs(parsed['outputs'],
                                       get_node_instances,
                                       None, None)
            self.fail()
        except FunctionEvaluationError, e:
            self.assertIn('Node specified in function does not exist', str(e))
            self.assertIn('webserver', str(e))

    def test_invalid_multi_instance_evaluation(self):
        self.template.version_section('1.0')
        self.template += """
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
        parsed = self.parse()

        def get_node_instances(node_id=None):
            node_instance = NodeInstance({
                'id': 'webserver1',
                'node_id': 'webserver',
                'runtime_properties': {'port': 8080},
            })
            return [node_instance, node_instance]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        try:
            evaluate_outputs(parsed['outputs'],
                             get_node_instances,
                             get_node_instance,
                             get_node)
            self.fail()
        except FunctionEvaluationError, e:
            self.assertIn('Multi instances of node', str(e))
            self.assertIn('webserver', str(e))

    def test_get_attribute_nested_property(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        value: { get_attribute: [ webserver, endpoint, port ] }
    protocol:
        value: { get_attribute: [ webserver, endpoint, url, protocol ] }
    none:
        value: { get_attribute: [ webserver, endpoint, url, none ] }
"""
        parsed = self.parse()

        def get_node_instances(node_id=None):
            node_instance = NodeInstance({
                'id': 'webserver1',
                'node_id': 'webserver',
                'runtime_properties': {
                    'endpoint': {
                        'url': {'protocol': 'http'},
                        'port': 8080,
                    }}})
            return [node_instance]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        outputs = evaluate_outputs(parsed['outputs'],
                                   get_node_instances,
                                   get_node_instance,
                                   get_node)
        self.assertEqual(8080, outputs['port'])
        self.assertEqual('http', outputs['protocol'])
        self.assertIsNone(outputs['none'])


class NodeInstance(dict):
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
    @property
    def id(self):
        return self.get('id')

    @property
    def properties(self):
        return self.get('properties', {})
