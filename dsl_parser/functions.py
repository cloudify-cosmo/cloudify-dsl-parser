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

import abc

from dsl_parser import exceptions
from dsl_parser import scan

GET_INPUT_FUNCTION = 'get_input'
GET_PROPERTY_FUNCTION = 'get_property'
GET_ATTRIBUTE_FUNCTION = 'get_attribute'

SELF = 'SELF'
SOURCE = 'SOURCE'
TARGET = 'TARGET'


class Function(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, args, scope=None, context=None, path=None, raw=None):
        self.scope = scope
        self.context = context
        self.path = path
        self.raw = raw
        self._parse_args(args)

    @abc.abstractmethod
    def _parse_args(self, args):
        pass

    @abc.abstractmethod
    def validate(self, plan):
        pass

    @abc.abstractmethod
    def evaluate(self, plan):
        pass


class GetInput(Function):

    def __init__(self, args, **kwargs):
        self.input_name = None
        super(GetInput, self).__init__(args, **kwargs)

    def _parse_args(self, args):
        valid_args_type = isinstance(args, basestring)
        if not valid_args_type:
            raise ValueError(
                "get_input function argument should be a string in "
                "{0} but is '{1}'.".format(self.context, args))
        self.input_name = args

    def validate(self, plan):
        if self.input_name not in plan.inputs:
            raise exceptions.UnknownInputError(
                "{0} get_input function references an "
                "unknown input '{1}'.".format(self.context, self.input_name))

    def evaluate(self, plan):
        return plan.inputs[self.input_name]


class GetProperty(Function):

    def __init__(self, args, **kwargs):
        self.node_name = None
        self.property_path = None
        super(GetProperty, self).__init__(args, **kwargs)

    def _parse_args(self, args):
        if not isinstance(args, list) or len(args) < 2:
            raise ValueError(
                'Illegal arguments passed to {0} function. Expected: '
                '<node_name, property_name [, nested-property-1, ... ]> but '
                'got: {1}.'.format(GET_PROPERTY_FUNCTION, args))
        self.node_name = args[0]
        self.property_path = args[1:]

    def validate(self, plan):
        self.evaluate(plan)

    def get_node_template(self, plan):
        if self.node_name == SELF:
            if self.scope != scan.NODE_TEMPLATE_SCOPE:
                raise ValueError(
                    '{0} can only be used in a context of node template but '
                    'appears in {1}.'.format(SELF, self.scope))
            node = self.context
        elif self.node_name in [SOURCE, TARGET]:
            if self.scope != scan.NODE_TEMPLATE_RELATIONSHIP_SCOPE:
                raise ValueError(
                    '{0} can only be used within a relationship but is used '
                    'in {1}'.format(self.node_name, self.path))
            if self.node_name == SOURCE:
                node = self.context['node_template']
            else:
                target_node = self.context['relationship']['target_id']
                node = [
                    x for x in plan.node_templates
                    if x['name'] == target_node][0]
        else:
            found = [
                x for x in plan.node_templates if self.node_name == x['id']]
            if len(found) == 0:
                raise KeyError(
                    "{0} function node reference '{1}' does not exist.".format(
                        GET_PROPERTY_FUNCTION, self.node_name))
            node = found[0]
        self._get_property_value(node)
        return node

    def _get_property_value(self, node_template):
        return _get_property_value(node_template['name'],
                                   node_template['properties'],
                                   self.property_path,
                                   self.path)

    def evaluate(self, plan):
        return self._get_property_value(self.get_node_template(plan))


class GetAttribute(Function):

    def __init__(self, args, **kwargs):
        self.node_name = None
        self.attribute_path = None
        super(GetAttribute, self).__init__(args, **kwargs)

    def _parse_args(self, args):
        if not isinstance(args, list) or len(args) < 2:
            raise ValueError(
                'Illegal arguments passed to {0} function. '
                'Expected: <node_name, attribute_name [, nested-attr-1, ...]>'
                'but got: {1}.'.format(GET_ATTRIBUTE_FUNCTION, args))
        self.node_name = args[0]
        self.attribute_path = args[1:]

    def validate(self, plan):
        if self.scope == scan.OUTPUTS_SCOPE and self.node_name in [SELF,
                                                                   SOURCE,
                                                                   TARGET]:
            raise ValueError('{0} cannot be used with {1} function in '
                             '{2}.'.format(self.node_name,
                                           GET_ATTRIBUTE_FUNCTION,
                                           self.path))
        if self.scope == scan.NODE_TEMPLATE_SCOPE and \
                self.node_name in [SOURCE, TARGET]:
            raise ValueError('{0} cannot be used with {1} function in '
                             '{2}.'.format(self.node_name,
                                           GET_ATTRIBUTE_FUNCTION,
                                           self.path))
        if self.scope == scan.NODE_TEMPLATE_RELATIONSHIP_SCOPE and \
                self.node_name == SELF:
            raise ValueError('{0} cannot be used with {1} function in '
                             '{2}.'.format(self.node_name,
                                           GET_ATTRIBUTE_FUNCTION,
                                           self.path))
        if self.node_name not in [SELF, SOURCE, TARGET]:
            found = [
                x for x in plan.node_templates if self.node_name == x['id']]
            if not found:
                raise KeyError(
                    "{0} function node reference '{1}' does not exist.".format(
                        GET_ATTRIBUTE_FUNCTION, self.node_name))

    def evaluate(self, plan):
        raise RuntimeError(
            '{0} function does not support evaluation.'.format(
                GET_ATTRIBUTE_FUNCTION))


TEMPLATE_FUNCTIONS = {
    GET_PROPERTY_FUNCTION: GetProperty,
    GET_ATTRIBUTE_FUNCTION: GetAttribute,
    GET_INPUT_FUNCTION: GetInput
}


def _get_property_value(node_name,
                        properties,
                        property_path,
                        context_path='',
                        raise_if_not_found=True):
    """Extracts a property's value according to the provided property path

    :param node_name: Node name the property belongs to (for logging).
    :param properties: Properties dict.
    :param property_path: Property path as list.
    :param context_path: Context path (for logging).
    :param raise_if_not_found: Whether to raise an error if property not found.
    :return: Property value.
    """
    str_list = lambda li: [str(item) for item in li]
    value = properties
    for p in property_path:
        if isinstance(value, dict):
            if p not in value:
                if raise_if_not_found:
                    raise KeyError(
                        "Node template property '{0}.properties.{1}' "
                        "referenced from '{2}' doesn't exist.".format(
                            node_name, '.'.join(str_list(property_path)),
                            context_path))
                return None
            value = value[p]
        elif isinstance(value, list):
            try:
                value = value[p]
            except TypeError:
                raise TypeError(
                    "Node template property '{0}.properties.{1}' "
                    "referenced from '{2}' is expected {3} to be an int "
                    "but it is a {4}.".format(
                        node_name, '.'.join(str_list(property_path)),
                        context_path,
                        p, type(p).__name__))
            except IndexError:
                if raise_if_not_found:
                    raise IndexError(
                        "Node template property '{0}.properties.{1}' "
                        "referenced from '{2}' index is out of range. Got {3}"
                        " but list size is {4}.".format(
                            node_name, '.'.join(str_list(property_path)),
                            context_path, p, len(value)))
                return None
        else:
            if raise_if_not_found:
                raise KeyError(
                    "Node template property '{0}.properties.{1}' "
                    "referenced from '{2}' doesn't exist.".format(
                        node_name, '.'.join(str_list(property_path)),
                        context_path))
            return None

    return value


def parse(raw_function, scope=None, context=None, path=None):
    if isinstance(raw_function, dict) and len(raw_function) == 1:
        func_name = raw_function.keys()[0]
        if func_name in TEMPLATE_FUNCTIONS:
            func_args = raw_function.values()[0]
            return TEMPLATE_FUNCTIONS[func_name](func_args,
                                                 scope=scope,
                                                 context=context,
                                                 path=path,
                                                 raw=raw_function)
    return raw_function


def evaluate_functions(payload, context,
                       get_node_instances_method,
                       get_node_instance_method,
                       get_node_method):
    """Evaluate functions in payload.

    :param payload: The payload to evaluate.
    :param context: Context used during evaluation.
    :param get_node_instances_method: A method for getting node instances.
    :param get_node_instance_method: A method for getting a node instance.
    :param get_node_method: A method for getting a node.
    :return: payload.
    """
    ctx = {
        'node_to_node_instances': {},
        'node_instances': {},
        'nodes': {}
    }

    def validate_ref(ref, ref_name, path, func):
        if not ref:
            raise exceptions.FunctionEvaluationError(
                GET_ATTRIBUTE_FUNCTION,
                '{0} is missing in request context in {1} for '
                'attribute {2}'.format(ref_name, path, func.attribute_path))

    def _get_node_instance(node_instance_id):
        if node_instance_id not in ctx['node_instances']:
            node_instance = get_node_instance_method(node_instance_id)
            ctx['node_instances'][node_instance_id] = node_instance
        return ctx['node_instances'][node_instance_id]

    def _get_node(node_id):
        if node_id not in ctx['nodes']:
            node = get_node_method(node_id)
            ctx['nodes'][node_id] = node
        return ctx['nodes'][node_id]

    def handler(v, scope, context, path):
        func = parse(v, scope=scope, context=context, path=path)
        if not isinstance(func, GetAttribute):
            return v

        if func.node_name == SELF:
            node_instance_id = context.get('self')
            validate_ref(node_instance_id, SELF, path, func)
            node_instance = _get_node_instance(node_instance_id)
        elif func.node_name == SOURCE:
            node_instance_id = context.get('source')
            validate_ref(node_instance_id, SOURCE, path, func)
            node_instance = _get_node_instance(node_instance_id)
        elif func.node_name == TARGET:
            node_instance_id = context.get('target')
            validate_ref(node_instance_id, TARGET, path, func)
            node_instance = _get_node_instance(node_instance_id)
        else:
            node_id = func.node_name
            if func.node_name not in ctx['node_to_node_instances']:
                node_instances = get_node_instances_method(node_id)
                ctx['node_to_node_instances'][node_id] = node_instances
            node_instances = ctx['node_to_node_instances'][node_id]
            if len(node_instances) == 0:
                raise exceptions.FunctionEvaluationError(
                    GET_ATTRIBUTE_FUNCTION,
                    'Node specified in function does not exist: {0}.'
                    .format(func.node_name))
            if len(node_instances) > 1:
                raise exceptions.FunctionEvaluationError(
                    GET_ATTRIBUTE_FUNCTION,
                    'Multi instances of node "{0}" are not supported by '
                    'function.'.format(func.node_name))
            node_instance = node_instances[0]

        value = _get_property_value(node_instance.node_id,
                                    node_instance.runtime_properties,
                                    func.attribute_path,
                                    path,
                                    raise_if_not_found=False)
        if value is None:
            node = _get_node(node_instance.node_id)
            value = _get_property_value(node.id,
                                        node.properties,
                                        func.attribute_path,
                                        path,
                                        raise_if_not_found=False)
        return value

    scan.scan_properties(payload,
                         handler,
                         scope=None,
                         context=context,
                         path='payload',
                         replace=True)
    return payload


def evaluate_outputs(outputs_def,
                     get_node_instances_method,
                     get_node_instance_method,
                     get_node_method):
    """Evaluates an outputs definition containing intrinsic functions.

    :param outputs_def: Outputs definition.
    :param get_node_instances_method: A method for getting node instances.
    :param get_node_instance_method: A method for getting a node instance.
    :param get_node_method: A method for getting a node.
    :return: Outputs dict.
    """
    outputs = dict((k, v['value']) for k, v in outputs_def.iteritems())
    return evaluate_functions(
        payload=outputs,
        context={},
        get_node_instances_method=get_node_instances_method,
        get_node_instance_method=get_node_instance_method,
        get_node_method=get_node_method)
