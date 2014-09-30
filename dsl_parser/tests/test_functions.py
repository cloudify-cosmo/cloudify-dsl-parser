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


from dsl_parser.tasks import prepare_deployment_plan
from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser.tests.abstract_test_parser import timeout


class TestGetProperty(AbstractTestParser):

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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['properties']['ip_duplicate'])
        server = self.get_node_by_name(parsed, 'server')
        self.assertEqual('10.0.0.1', server['properties']['endpoint'])

    def test_illegal_property_in_property(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: { get_property: [SELF, notfound] }
"""
        try:
            self.parse(yaml)
            self.fail()
        except KeyError, e:
            self.assertIn('Node template property', str(e))
            self.assertIn("doesn't exist", str(e))
            self.assertIn('vm.properties.notfound', str(e))
            self.assertIn('vm.properties.a', str(e))

    def test_node_template_interfaces(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
        install: false
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['operations']['op']['properties']['x'])
        self.assertEqual('10.0.0.1',
                         vm['operations']['interface.op']['properties']['x'])

    def test_illegal_property_in_interface(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
        install: false
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
        interfaces:
            interface:
                op:
                    implementation: plugin.op
                    inputs:
                        x: { get_property: [vm, notfound] }
"""
        try:
            a = self.parse(yaml)
            self.fail()
        except KeyError, e:
            self.assertIn('Node template property', str(e))
            self.assertIn("doesn't exist", str(e))
            self.assertIn('vm.properties.notfound', str(e))
            self.assertIn('vm.operations.interface.op.properties.x', str(e))

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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(0, vm['properties']['b'])
        self.assertEqual(1, vm['properties']['x'])
        self.assertEqual(1, vm['properties']['y'])
        self.assertEqual(1, vm['properties']['z'])

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
        parsed = prepare_deployment_plan(self.parse(yaml))
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
            self.parse(yaml)
            self.fail()
        except KeyError, e:
            self.assertIn('Node template property', str(e))
            self.assertIn("doesn't exist", str(e))
            self.assertIn('vm.properties.a', str(e))
            self.assertIn('outputs.a.value', str(e))

    def test_source_and_target_interfaces(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
        source: dummy
node_types:
    some_type:
        properties:
            a: { type: string }
relationships:
    cloudify.relationships.contained_in: {}
    rel:
        derived_from: cloudify.relationships.contained_in
        source_interfaces:
            source_interface:
                -   op1:
                        mapping: plugin.operation
                        properties:
                            source_a: { get_property: [%(source)s, a] }
                            target_a: { get_property: [%(target)s, a] }
        target_interfaces:
            target_interface:
                -   op2:
                        mapping: plugin.operation
                        properties:
                            source_a: { get_property: [%(source)s, a] }
                            target_a: { get_property: [%(target)s, a] }
node_templates:
    node1:
        type: some_type
        properties:
            a: 1
    node2:
        type: some_type
        properties:
            a: 2
        relationships:
            -   type: rel
                target: node1
"""

        def do_assertions():
            """
            Assertions are made for explicit node names in a relationship
            and another time for SOURCE & TARGET keywords.
            """
            node = self.get_node_by_name(prepared, 'node2')
            source_ops = node['relationships'][0]['source_operations']
            self.assertEqual(2,
                             source_ops['source_interface.op1']['properties']
                             ['source_a'])
            self.assertEqual(1,
                             source_ops['source_interface.op1']['properties']
                             ['target_a'])
            target_ops = node['relationships'][0]['target_operations']
            self.assertEqual(2,
                             target_ops['target_interface.op2']['properties']
                             ['source_a'])
            self.assertEqual(1,
                             target_ops['target_interface.op2']['properties']
                             ['target_a'])

        # Explicit node template names
        prepared = prepare_deployment_plan(self.parse(yaml % {
            'source': 'node2', 'target': 'node1'}))
        do_assertions()

        # SOURCE & TARGET
        prepared = prepare_deployment_plan(self.parse(yaml % {
            'source': 'SOURCE', 'target': 'TARGET'}))
        do_assertions()

    def test_recursive_with_nesting(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 1
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, a ] }, 2 ]
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(1, vm['properties']['b'][0])
        self.assertEqual(2, vm['properties']['b'][1])
        self.assertEqual(1, vm['properties']['c'][0])
        self.assertEqual(2, vm['properties']['c'][1])

    @timeout(seconds=10)
    def test_circular_get_property(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: { get_property: [SELF, b] }
            b: { get_property: [SELF, c] }
            c: { get_property: [SELF, a] }
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except RuntimeError, e:
            self.assertIn('Circular get_property function call detected',
                          str(e))

    @timeout(seconds=10)
    def test_circular_get_property_with_nesting(self):
        yaml = """
node_types:
    vm_type:
        properties:
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, b ] }, 2 ]
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except RuntimeError, e:
            self.assertIn('Circular get_property function call detected',
                          str(e))

    def test_recursive_get_property_in_outputs(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 1
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, a ] }, 2 ]
outputs:
    o:
        value:
            a: { get_property: [vm, b] }
            b: [0, { get_property: [vm, b] }]
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        outputs = parsed.outputs
        self.assertEqual(1, outputs['o']['value']['a'][0])
        self.assertEqual(2, outputs['o']['value']['a'][1])
        self.assertEqual(0, outputs['o']['value']['b'][0])
        self.assertEqual(1, outputs['o']['value']['b'][1][0])
        self.assertEqual(2, outputs['o']['value']['b'][1][1])

    @timeout(seconds=10)
    def test_circular_get_property_from_outputs(self):
        yaml = """
node_types:
    vm_type:
        properties:
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, b ] }, 2 ]
outputs:
    o:
        value:
            a: 1
            b: { get_property: [vm, b] }
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except RuntimeError, e:
            self.assertIn('Circular get_property function call detected',
                          str(e))

    @timeout(seconds=10)
    def test_circular_self_get_property(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: [ { get_property: [SELF, a ] } ]
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except RuntimeError, e:
            self.assertIn('Circular get_property function call detected',
                          str(e))

    def test_nested_property_path(self):
        yaml = """
node_types:
    vm_type:
        properties:
            endpoint: {}
            a: { type: integer }
    server_type:
        properties:
            port: { type: integer }
node_templates:
    vm:
        type: vm_type
        properties:
            endpoint:
                url:
                    protocol: http
                port: 80
            a: { get_property: [ SELF, endpoint, port ] }
    server:
        type: server_type
        properties:
            port: { get_property: [ vm, endpoint, port ] }
outputs:
    a:
        value: { get_property: [ vm, endpoint, port ] }
    b:
        value: { get_property: [ vm, endpoint, url, protocol ] }

"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(80, vm['properties']['a'])
        server = self.get_node_by_name(parsed, 'server')
        self.assertEqual(80, server['properties']['port'])
        outputs = parsed.outputs
        self.assertEqual(80, outputs['a']['value'])
        self.assertEqual('http', outputs['b']['value'])

    def test_invalid_nested_property(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a:
                a0: { get_property: [ SELF, a, notfound ] }
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except KeyError, e:
            self.assertIn(
                "Node template property 'vm.properties.a.notfound' "
                "referenced from 'vm.properties.a.a0' doesn't exist.", str(e))

    @timeout(seconds=10)
    def test_circular_nested_property_path(self):
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
            a:
                a0: { get_property: [ SELF, b, b0 ] }
            b:
                b0: { get_property: [ SELF, a, a0 ] }
"""
        try:
            prepare_deployment_plan(self.parse(yaml))
            self.fail()
        except RuntimeError, e:
            self.assertIn('Circular get_property function call detected: '
                          'vm.b,b0 -> vm.a,a0 -> vm.b,b0',
                          str(e))


class TestGetAttribute(AbstractTestParser):

    def test_used_only_in_outputs(self):
        yaml = """
node_types:
    vm_type:
        properties:
            a: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: { get_attribute: [SELF, aaa] }
"""
        try:
            self.parse(yaml)
            self.fail()
        except ValueError, e:
            self.assertIn('get_attribute function can only be used in outputs '
                          'but is used in vm.properties.a', str(e))

    def test_illegal_safe_in_outputs(self):
        yaml = """
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
outputs:
    a:
        value: { get_attribute: [SELF, aaa] }
"""
        try:
            self.parse(yaml)
            self.fail()
        except ValueError, e:
            self.assertIn('SELF cannot be used with get_attribute function in '
                          'outputs.a.value', str(e))
