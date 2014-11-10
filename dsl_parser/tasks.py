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
from dsl_parser import scan


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
                    'Required input \'{0}\' was not specified - expected '
                    'inputs: {1}'.format(input_name, plan['inputs'].keys()))
    # Verify all inputs appear in plan
    for input_name in inputs.keys():
        if input_name not in plan['inputs']:
            raise exceptions.UnknownInputError(
                'Unknown input \'{0}\' specified - '
                'expected inputs: {1}'.format(input_name,
                                              plan['inputs'].keys()))
    plan['inputs'] = inputs


def _process_functions(plan):
    def handler(v, scope, context, path):
        func = functions.parse(v, scope=scope, context=context, path=path)
        evaluated_value = v
        while isinstance(func, functions.Function):
            if isinstance(func, functions.GetAttribute):
                if 'operation' in context:
                    context['operation']['has_intrinsic_functions'] = True
                return func.raw
            evaluated_value = func.evaluate(plan)
            scan.scan_properties(evaluated_value,
                                 handler,
                                 scope=scope,
                                 context=context,
                                 path=path,
                                 replace=True)
            func = functions.parse(evaluated_value,
                                   scope=scope,
                                   context=context,
                                   path=path)
        return evaluated_value

    scan.scan_service_template(plan, handler, replace=True)


def prepare_deployment_plan(plan, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    plan = multi_instance.create_deployment_plan(plan)
    _set_plan_inputs(plan, inputs)
    _process_functions(plan)
    return plan


def modify_deployment(nodes, previous_node_instances, modified_nodes):
    return multi_instance.modify_deployment(nodes,
                                            previous_node_instances,
                                            modified_nodes)
