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

import unittest

from dsl_parser.parser import parse
from dsl_parser.tasks import prepare_deployment_plan
from dsl_parser.exceptions import MissingRequiredInputError, UnknownInputError


class TestInputs(unittest.TestCase):

    def test_inputs_definition(self):
        yaml = """
inputs: {}
node_templates: {}
"""
        parsed = parse(yaml)
        self.assertEqual(0, len(parsed['inputs']))

    def test_input_definition(self):
        yaml = """
inputs:
    port:
        description: the port
        default: 8080
node_templates: {}
"""
        parsed = parse(yaml)
        self.assertEqual(1, len(parsed['inputs']))
        self.assertEqual(8080, parsed['inputs']['port']['default'])
        self.assertEqual('the port', parsed['inputs']['port']['description'])

    def test_two_inputs(self):
        yaml = """
inputs:
    port:
        description: the port
        default: 8080
    ip: {}
node_templates: {}
"""
        parsed = parse(yaml)
        self.assertEqual(2, len(parsed['inputs']))
        self.assertEqual(8080, parsed['inputs']['port']['default'])
        self.assertEqual('the port', parsed['inputs']['port']['description'])
        self.assertEqual(0, len(parsed['inputs']['ip']))

    def test_verify_get_input_in_properties(self):
        yaml = """
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        self.assertRaises(UnknownInputError, parse, yaml)
        yaml = """
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: {} }
"""
        self.assertRaises(ValueError, parse, yaml)
        yaml = """
inputs:
    port: {}
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        parse(yaml)

    def test_inputs_provided_to_plan(self):
        yaml = """
inputs:
    port:
        default: 9000
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        parsed = prepare_deployment_plan(parse(yaml), inputs={'port': 8000})
        self.assertEqual(8000,
                         parsed['nodes'][0]['properties']['port'])

    def test_missing_input(self):
        yaml = """
inputs:
    port: {}
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        self.assertRaises(MissingRequiredInputError,
                          prepare_deployment_plan,
                          parse(yaml))

    def test_inputs_default_value(self):
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        self.assertEqual(8080,
                         parsed['nodes'][0]['properties']['port'])

    def test_unknown_input_provided(self):
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        self.assertRaises(UnknownInputError,
                          prepare_deployment_plan,
                          parse(yaml),
                          inputs={'a': 'b'})

    def test_get_input_in_nested_property(self):
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                port: { get_input: port }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        self.assertEqual(8080,
                         parsed['nodes'][0]['properties']['server']['port'])
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                port: { get_input: port }
                some_prop: { get_input: unknown }
"""
        self.assertRaises(UnknownInputError, parse, yaml)

    def test_get_input_list_property(self):
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                - item1
                - port: { get_input: port }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        self.assertEqual(8080,
                         parsed['nodes'][0]['properties']['server'][1]['port'])
        yaml = """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                - item1
                - port: { get_input: port1122 }
"""
        self.assertRaises(UnknownInputError, parse, yaml)

    def test_input_in_interface(self):
        yaml = """
plugins:
    plugin:
        derived_from: cloudify.plugins.remote_plugin

inputs:
    port:
        default: 8080
node_types:
    webserver_type: {}
relationships:
    cloudify.relationships.contained_in: {}
    rel:
        derived_from: cloudify.relationships.contained_in
        source_interfaces:
            source_interface:
                -   op1:
                        mapping: plugin.operation
                        properties:
                            source_port: { get_input: port }
        target_interfaces:
            target_interface:
                -   op2:
                        mapping: plugin.operation
                        properties:
                            target_port: { get_input: port }
node_templates:
    ws1:
        type: webserver_type
    webserver:
        type: webserver_type
        interfaces:
            lifecycle:
                -   configure:
                        mapping: plugin.operation
                        properties:
                            port: { get_input: port }
        relationships:
            -   type: rel
                target: ws1
"""
        prepared = prepare_deployment_plan(parse(yaml))

        node_template = \
            [x for x in prepared['nodes'] if x['name'] == 'webserver'][0]
        op = node_template['operations']['lifecycle.configure']
        self.assertEqual(8080, op['properties']['port'])
        op = node_template['operations']['configure']
        self.assertEqual(8080, op['properties']['port'])
        # relationship interfaces
        source_ops = node_template['relationships'][0]['source_operations']
        self.assertEqual(
            8080,
            source_ops['source_interface.op1']['properties']['source_port'])
        self.assertEqual(8080, source_ops['op1']['properties']['source_port'])
        target_ops = node_template['relationships'][0]['target_operations']
        self.assertEqual(
            8080,
            target_ops['target_interface.op2']['properties']['target_port'])
        self.assertEqual(8080, target_ops['op2']['properties']['target_port'])

        prepared = prepare_deployment_plan(parse(yaml), inputs={'port': 8000})
        node_template = \
            [x for x in prepared['nodes'] if x['name'] == 'webserver'][0]
        op = node_template['operations']['lifecycle.configure']
        self.assertEqual(8000, op['properties']['port'])
        op = node_template['operations']['configure']
        self.assertEqual(8000, op['properties']['port'])
        # relationship interfaces
        source_ops = node_template['relationships'][0]['source_operations']
        self.assertEqual(
            8000,
            source_ops['source_interface.op1']['properties']['source_port'])
        self.assertEqual(8000, source_ops['op1']['properties']['source_port'])
        target_ops = node_template['relationships'][0]['target_operations']
        self.assertEqual(
            8000,
            target_ops['target_interface.op2']['properties']['target_port'])
        self.assertEqual(8000, target_ops['op2']['properties']['target_port'])

    def test_invalid_input_in_interfaces(self):
        yaml = """
plugins:
    plugin:
        derived_from: cloudify.plugins.remote_plugin
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
        interfaces:
            lifecycle:
                -   configure:
                        mapping: plugin.operation
                        properties:
                            port: { get_input: aaa }
"""
        self.assertRaises(UnknownInputError, parse, yaml)
