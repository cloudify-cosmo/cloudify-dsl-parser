# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .constants import (
    NODE_TEMPLATE_SCOPE,
    NODE_TEMPLATE_RELATIONSHIP_SCOPE,
    OUTPUTS_SCOPE,
)


def scan_properties(
        value,
        handler,
        scope=None,
        context=None,
        path='',
        replace=False):
    """
    Scans properties dict recursively and applies the provided handler
    method for each property.

    The handler method should have the following signature:
    def handler(value, scope, context, path):

    * value - the value of the property.
    * scope - scope of the operation (string).
    * context - scanner context (i.e. actual node template).
    * path - current property path.
    * replace - replace current dict/list values of scanned properties.

    :param value: The properties container (dict/list).
    :param handler: A method for applying for to each property.
    :param scope:
    :param context:
    :param path: The properties base path (for debugging purposes).
    :param replace:
    """
    scan_property_handler = _SCAN_PROPERTIES_HANDLERS.get(type(value))
    if scan_property_handler:
        scan_property_handler(value, handler, scope, context, path, replace)


def scan_dict_properties(
        value,
        handler,
        scope=None,
        context=None,
        path='',
        replace=False):
    for k, v in value.iteritems():
        current_path = '{0}.{1}'.format(path, k)
        result = handler(v, scope, context, current_path)
        if replace and result != v:
            value[k] = result
        scan_properties(v, handler,
                        scope=scope,
                        context=context,
                        path=current_path,
                        replace=replace)


def scan_list_properties(
        value,
        handler,
        scope=None,
        context=None,
        path='',
        replace=False):
    for index, item in enumerate(value):
        current_path = '{0}[{1}]'.format(path, index)
        result = handler(item, scope, context, current_path)
        if replace and result != item:
            value[index] = result
        scan_properties(item,
                        handler,
                        scope=scope,
                        context=context,
                        path=path,
                        replace=replace)


def scan_node_operation_properties(node_template, handler, replace=False):
    _scan_operations(node_template['operations'],
                     handler,
                     scope=NODE_TEMPLATE_SCOPE,
                     context=node_template,
                     path='{0}.operations'.format(node_template['name']),
                     replace=replace)
    for relationship in node_template.get('relationships', ()):
        context = {
            'node_template': node_template,
            'relationship': relationship,
        }
        _scan_operations(
            relationship.get('source_operations', {}),
            handler,
            scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
            context=context,
            path='{0}.{1}'.format(node_template['name'], relationship['type']),
            replace=replace)
        _scan_operations(
            relationship.get('target_operations', {}),
            handler,
            scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
            context=context,
            path='{0}.{1}'.format(node_template['name'], relationship['type']),
            replace=replace)


def scan_service_template(plan, handler, replace=False):
    for node_template in plan.node_templates:
        scan_properties(
            node_template['properties'],
            handler,
            scope=NODE_TEMPLATE_SCOPE,
            context=node_template,
            path='{0}.properties'.format(node_template['name']),
            replace=replace)
        scan_node_operation_properties(node_template, handler, replace=replace)

    for output_name, output in plan.outputs.iteritems():
        scan_properties(
            output,
            handler,
            scope=OUTPUTS_SCOPE,
            context=plan.outputs,
            path='outputs.{0}'.format(output_name),
            replace=replace)


_SCAN_PROPERTIES_HANDLERS = {
    dict: scan_dict_properties,
    list: scan_list_properties,
}


def _scan_operations(operations,
                     handler,
                     scope=None,
                     context=None,
                     path='',
                     replace=False):
    for name, definition in operations.iteritems():
        if isinstance(definition, dict) and 'inputs' in definition:
            context['operation'] = definition
            scan_properties(
                definition['inputs'],
                handler,
                scope=scope,
                context=context.copy() if context else {},
                path='{0}.{1}.inputs'.format(path, name),
                replace=replace)
