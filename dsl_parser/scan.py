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


NODE_TEMPLATE_SCOPE = 'node_template'
NODE_TEMPLATE_RELATIONSHIP_SCOPE = 'node_template_relationship'
OUTPUTS_SCOPE = 'outputs'


def scan_properties(value, handler, scope=None, context=None, path=''):
    """
    Scans properties dict recursively and applies the provided handler
    method for each property.

    The handler method should have the following signature:
    def handler(dictionary, key, scope, context, value, path):

    * dictionary - the dictionary the property belongs to.
    * key - the name of the property.
    * value - the value of the property.
    * scope - scope of the operation (string).
    * context - scanner context (i.e. actual node template).
    * path - current property path.

    :param value: The properties container (dict/list).
    :param handler: A method for applying for to each property.
    :param path: The properties base path (for debugging purposes).
    """
    assert context
    assert scope
    if isinstance(value, dict):
        for k, v in value.iteritems():
            current_path = '{0}.{1}'.format(path, k)
            handler(value, k, v, scope, context, current_path)
            scan_properties(v, handler,
                            scope=scope,
                            context=context,
                            path=current_path)
    elif isinstance(value, list):
        for item in value:
            scan_properties(item, handler,
                            scope=scope,
                            context=context,
                            path=path)


def _scan_operations(operations, handler, scope=None, context=None, path=''):
    for name, definition in operations.iteritems():
        if isinstance(definition, dict) and 'properties' in definition:
            scan_properties(definition['properties'],
                            handler,
                            scope=scope,
                            context=context,
                            path='{0}.{1}.properties'.format(path, name))


def scan_node_operation_properties(node_template, handler):
    _scan_operations(node_template['operations'],
                     handler,
                     scope=NODE_TEMPLATE_SCOPE,
                     context=node_template,
                     path='{0}.operations'.format(node_template['name']))
    for r in node_template.get('relationships', []):
        context = {'node_template': node_template, 'relationship': r}
        _scan_operations(r.get('source_operations', {}),
                         handler,
                         scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
                         context=context,
                         path='{0}.{1}'.format(node_template['name'],
                                               r['type']))
        _scan_operations(r.get('target_operations', {}),
                         handler,
                         scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
                         context=context,
                         path='{0}.{1}'.format(node_template['name'],
                                               r['type']))
