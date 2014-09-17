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


class TestGetProperty(unittest.TestCase):

    def _get_node(self, nodes, node_name):
        return [x for x in nodes if x['name'] == node_name][0]

    def test_node_template_properties(self):
        yaml = """
node_types:
    vm_type:
        properties:
            ip: {}
            ip_duplicate: {}
    server_type:
        properties:
            endpoint: {}
node_templates:
    vm:
        type: vm_type
        properties:
            ip: 10.0.0.1
            ip_duplicate: { get_property: [ SELF, ip ] }
    server:
        type: server_type
        properties:
            endpoint: { get_property: [ vm, ip ] }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        vm = self._get_node(parsed['nodes'], 'vm')
        self.assertEqual('10.0.0.1', vm['properties']['ip_duplicate'])
        server = self._get_node(parsed['nodes'], 'server')
        self.assertEqual('10.0.0.1', server['properties']['endpoint'])

    def test_illegal_property_in_property(self):
        self.fail()

    def test_illegal_property_in_interface(self):
        self.fail()

    def test_illegal_property_in_groups(self):
        self.fail()

    def test_illegal_property_in_outputs(self):
        self.fail()

    def test_node_template_interfaces(self):
        yaml = """
plugins:
    plugin:
        derived_from: cloudify.plugins.remote_plugin
node_types:
    vm_type:
        properties:
            ip:
                type: string
node_templates:
    vm:
        type: vm_type
        properties:
            ip: 10.0.0.1
        interfaces:
            interface:
                -   op:
                        mapping: plugin.op
                        properties:
                            x: { get_property: [vm, ip] }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        vm = [x for x in parsed.node_templates if x.name == 'vm'][0]
        self.assertEqual('10.0.0.1', vm.operations['op']['properties']['x'])
        self.assertEqual('10.0.0.1',
                         vm.operations['interface.op']['properties']['x'])

    def test_recursive(self):
        yaml = """
inputs:
    i:
        default: 1
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
            x: { type: string }
            y: { type: string }
            z: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 0
            b: { get_property: [ SELF, a ] }
            c: { get_property: [ SELF, b ] }
            x: { get_property: [ SELF, z ] }
            y: { get_property: [ SELF, x ] }
            z: { get_input: i }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        vm = [x for x in parsed.node_templates if x.name == 'vm'][0]
        self.assertEqual(0, vm.properties['b'])
        self.assertEqual(1, vm.properties['x'])
        self.assertEqual(1, vm.properties['y'])
        self.assertEqual(1, vm.properties['z'])

    def test_outputs(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 0
            b: { get_property: [vm, a] }
outputs:
    a:
        value: { get_property: [vm, a] }
    b:
        value: { get_property: [vm, b] }
"""
        parsed = prepare_deployment_plan(parse(yaml))
        outputs = parsed.outputs
        self.assertEqual(0, outputs['a']['value'])
        self.assertEqual(0, outputs['b']['value'])

    def test_illegal_property_in_output(self):
        yaml = """
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
outputs:
    a:
        value: { get_property: [vm, a] }
"""
        try:
            parse(yaml)
            self.fail()
        except KeyError, e:
            self.assertIn('Property of node template', str(e))
            self.assertIn("doesn't exist", str(e))
            self.assertIn('vm.properties.a', str(e))
            self.assertIn('output.a.value', str(e))

    def test_groups(self):
        self.fail()

    def test_illegal_property_in_groups(self):
        self.fail()
