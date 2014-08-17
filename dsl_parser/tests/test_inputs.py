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
        self.assertRaises(ValueError, parse, yaml)
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

    def test_inputs_not_satisfied(self):
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
        self.assertRaises(KeyError, prepare_deployment_plan, parse(yaml))

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
