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
from dsl_parser import utils

GET_INPUT_FUNCTION = 'get_input'
GET_ATTRIBUTE_FUNCTION = 'get_attribute'


class GetInput(object):

    def __init__(self, context, args):
        self.context = context
        self.input_name = None
        self._parse_args(args)

    def _parse_args(self, args):
        valid_args_type = isinstance(args, str) or isinstance(args, unicode)
        if not valid_args_type:
            raise ValueError(
                "get_input function argument should be a string in "
                "{} but is '{}'.".format(self.context, args))
        self.input_name = args

    def validate(self, inputs):
        if self.input_name not in inputs:
            raise exceptions.UnknownInputError(
                "{} get_input function references an "
                "unknown input '{}'.".format(self.context, self.input_name))


class GetAttribute(object):

    def __init__(self, context, args):
        self.context = context
        self.node_name = None
        self.attribute_name = None
        self._parse_args(args)

    def _parse_args(self, args):
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError(
                'Illegal arguments passed to {0} function. Expected: '
                '[ node_name, attribute_name ] but got: {1}.'.format(
                    GET_ATTRIBUTE_FUNCTION, args))
        self.node_name = args[0]
        self.attribute_name = args[1]

    def validate(self, node_templates):
        found = [x for x in node_templates if self.node_name in x['id']]
        if len(found) == 0:
            raise KeyError(
                "{0} function node reference '{1}' does not exist.".format(
                    GET_ATTRIBUTE_FUNCTION, self.node_name))


TEMPLATE_FUNCTIONS = {
    GET_ATTRIBUTE_FUNCTION: GetAttribute,
    GET_INPUT_FUNCTION: GetInput
}


def parse(raw_function, context=None):
    if isinstance(raw_function, dict) and len(raw_function) == 1:
        func_name = raw_function.keys()[0]
        if func_name in TEMPLATE_FUNCTIONS:
            func_args = raw_function.values()[0]
            return TEMPLATE_FUNCTIONS[func_name](context, func_args)
    return raw_function


def evaluate_outputs(outputs_def, get_node_instances_method):
    """Evaluates an outputs definition containing intrinsic functions.

    :param outputs_def: Outputs definition.
    :param get_node_instances_method: A method for getting node instances.
    :return: Outputs dict.
    """
    context = {}
    outputs = {k: v['value'] for k, v in outputs_def.iteritems()}

    def handler(dict_, k, v, _):
        func = parse(v)
        if isinstance(func, GetAttribute):
            attributes = []
            if 'node_instances' not in context:
                context['node_instances'] = get_node_instances_method()
            for instance in context['node_instances']:
                if instance.node_id == func.node_name:
                    attributes.append(
                        instance.runtime_properties.get(
                            func.attribute_name) if
                        instance.runtime_properties else None)
            if len(attributes) == 1:
                dict_[k] = attributes[0]
            elif len(attributes) == 0:
                raise exceptions.FunctionEvaluationError(
                    GET_ATTRIBUTE_FUNCTION,
                    'Node specified in function does not exist: {0}.'.format(
                        func.node_name)
                )
            elif len(attributes) > 1:
                raise exceptions.FunctionEvaluationError(
                    GET_ATTRIBUTE_FUNCTION,
                    'Multi instances of node "{0}" are not supported by '
                    'function.'.format(func.node_name))

    utils.scan_properties(outputs, handler, 'outputs')
    return outputs
