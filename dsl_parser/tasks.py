########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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


import json

import parser
import multi_instance

from dsl_parser import functions
from dsl_parser import exceptions
from dsl_parser.utils import scan_properties


def parse_dsl(dsl_location, alias_mapping_url,
              resources_base_url, **kwargs):
    result = parser.parse_from_url(dsl_url=dsl_location,
                                   alias_mapping_url=alias_mapping_url,
                                   resources_base_url=resources_base_url)
    return json.dumps(result)


def _set_plan_inputs(plan, inputs=None):
    inputs = inputs if inputs else {}
    # Verify inputs satisfied
    for input_name, input_def in plan['inputs'].iteritems():
        if input_name not in inputs:
            if 'default' in input_def and input_def['default'] is not None:
                inputs[input_name] = input_def['default']
            else:
                raise exceptions.MissingRequiredInputError(
                    'Required input \'{}\' was not specified - expected '
                    'inputs: {}'.format(input_name, plan['inputs'].keys()))
    # Verify all inputs appear in plan
    for input_name in inputs.keys():
        if input_name not in plan['inputs']:
            raise exceptions.UnknownInputError(
                'Unknown input \'{}\' specified - '
                'expected inputs: {}'.format(input_name,
                                             plan['inputs'].keys()))

    def handler(dict_, k, v, path):
        func = functions.parse(v, context=path)
        if isinstance(func, functions.GetInput):
            dict_[k] = inputs[func.input_name]

    for node_template in plan['nodes']:
        scan_properties(node_template['properties'],
                        handler,
                        '{0}.properties'.format(node_template['name']))
        for name, definition in node_template['operations'].items():
            if 'properties' in definition:
                scan_properties(definition['properties'],
                                handler,
                                '{0}.{1}.properties'.format(
                                    node_template['name'], name))
    plan['inputs'] = inputs


def prepare_deployment_plan(plan, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    plan = multi_instance.create_multi_instance_plan(plan)
    _set_plan_inputs(plan, inputs)
    return plan
