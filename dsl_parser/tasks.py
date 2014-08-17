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

from dsl_parser.functions import is_get_input, GET_INPUT_FUNCTION


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
            if 'default' in input_def and input_def['default']:
                inputs[input_name] = input_def['default']
            else:
                raise KeyError(
                    'Mandatory input: \'{}\' was not specified'.format(
                        input_name))
    # Replace get_input function with inputs
    for node_template in plan['nodes']:
        for k, v in node_template['properties'].iteritems():
            if is_get_input(v):
                input_name = v[GET_INPUT_FUNCTION]
                node_template['properties'][k] = inputs[input_name]


def prepare_deployment_plan(plan, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    plan = multi_instance.create_multi_instance_plan(plan)
    _set_plan_inputs(plan, inputs)
    return plan
