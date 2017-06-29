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


class TestFunctionRegistration(AbstractTestParser):

    def setUp(self):
        super(TestFunctionRegistration, self).setUp()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        functions.unregister('to_upper')

    def test_registration(self):
        @functions.register(name='to_upper')
        class ToUpper(functions.Function):

            def __init__(self, args, **kwargs):
                self.arg = None
                super(ToUpper, self).__init__(args, **kwargs)

            def parse_args(self, args):
                self.arg = args

            def evaluate_runtime(self, storage):
                return self.evaluate(plan=None)

            def evaluate(self, plan):
                if functions.parse(self.arg) != self.arg:
                    return self.raw
                return str(self.arg).upper()

            def validate(self, plan):
                pass

        yaml = """
node_types:
    webserver_type:
        properties:
            property:
                default: property_value
node_templates:
    webserver:
        type: webserver_type
outputs:
    output1:
        value: { to_upper: first }
    output2:
        value: { to_upper: { get_property: [webserver, property] } }
    output3:
        value: { to_upper: { get_attribute: [webserver, attribute] } }
    output4:
        value: { to_upper: { get_secret: secret } }
"""
        parsed = prepare_deployment_plan(self.parse(yaml),
                                         self._get_secret_mock)
        outputs = parsed['outputs']
        self.assertEqual('FIRST', outputs['output1']['value'])
        self.assertEqual('PROPERTY_VALUE', outputs['output2']['value'])
        self.assertEqual({'to_upper': {'get_attribute': ['webserver',
                                                         'attribute']}},
                         outputs['output3']['value'])

        def get_node_instances(node_id=None):
            return [
                NodeInstance({
                    'id': 'webserver1',
                    'node_id': 'webserver',
                    'runtime_properties': {
                        'attribute': 'attribute_value'
                    }
                })
            ]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        o = functions.evaluate_outputs(parsed['outputs'],
                                       get_node_instances,
                                       get_node_instance,
                                       get_node,
                                       self._get_secret_mock)

        self.assertEqual('FIRST', o['output1'])
        self.assertEqual('PROPERTY_VALUE', o['output2'])
        self.assertEqual('ATTRIBUTE_VALUE', o['output3'])
        self.assertEqual('SECRET_VALUE', o['output4'])


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
