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
POLICIES_SCOPE = 'policies'
SCALING_GROUPS_SCOPE = 'scaling_groups'

# Searching for secrets in the blueprint only one time of the few times
# that scan_service_template is called
collect_secrets = False
secrets = set()


def scan_properties(value,
                    handler,
                    scope=None,
                    context=None,
                    path='',
                    replace=False,
                    recursive=True):
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
    :param path: The properties base path (for debugging purposes).
    """
    if isinstance(value, dict):
        for k, v in value.iteritems():
            current_path = '{0}.{1}'.format(path, k)
            result = handler(v, scope, context, current_path)
            _collect_secret(result)
            if replace and result != v:
                value[k] = result
            if recursive:
                scan_properties(v, handler,
                                scope=scope,
                                context=context,
                                path=current_path,
                                replace=replace)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current_path = '{0}[{1}]'.format(path, index)
            result = handler(item, scope, context, current_path)
            _collect_secret(result)
            if replace and result != item:
                value[index] = result
            if recursive:
                scan_properties(item,
                                handler,
                                scope=scope,
                                context=context,
                                path=path,
                                replace=replace)


def _collect_secret(value):
    if collect_secrets and isinstance(value, dict) and 'get_secret' in value:
        secrets.add(value['get_secret'])


def _scan_operations(operations,
                     handler,
                     scope=None,
                     context=None,
                     path='',
                     replace=False):
    for name, definition in operations.iteritems():
        if isinstance(definition, dict) and 'inputs' in definition:
            context = context.copy() if context else {}
            context['operation'] = definition
            scan_properties(definition['inputs'],
                            handler,
                            scope=scope,
                            context=context,
                            path='{0}.{1}.inputs'.format(path, name),
                            replace=replace)


def scan_node_operation_properties(node_template, handler, replace=False):
    _scan_operations(node_template['operations'],
                     handler,
                     scope=NODE_TEMPLATE_SCOPE,
                     context=node_template,
                     path='{0}.operations'.format(node_template['name']),
                     replace=replace)
    for r in node_template.get('relationships', []):
        context = {'node_template': node_template, 'relationship': r}
        _scan_operations(r.get('source_operations', {}),
                         handler,
                         scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
                         context=context,
                         path='{0}.{1}'.format(node_template['name'],
                                               r['type']),
                         replace=replace)
        _scan_operations(r.get('target_operations', {}),
                         handler,
                         scope=NODE_TEMPLATE_RELATIONSHIP_SCOPE,
                         context=context,
                         path='{0}.{1}'.format(node_template['name'],
                                               r['type']),
                         replace=replace)


def scan_service_template(plan, handler, replace=False, search_secrets=False):
    global collect_secrets
    collect_secrets = search_secrets

    for node_template in plan.node_templates:
        scan_properties(node_template['properties'],
                        handler,
                        scope=NODE_TEMPLATE_SCOPE,
                        context=node_template,
                        path='{0}.properties'.format(
                            node_template['name']),
                        replace=replace)
        for name, capability in node_template.get('capabilities', {}).items():
            scan_properties(capability.get('properties', {}),
                            handler,
                            scope=NODE_TEMPLATE_SCOPE,
                            context=node_template,
                            path='{0}.capabilities.{1}'.format(
                                node_template['name'],
                                name),
                            replace=replace)
        scan_node_operation_properties(node_template, handler, replace=replace)
    for output_name, output in plan.outputs.iteritems():
        scan_properties(output,
                        handler,
                        scope=OUTPUTS_SCOPE,
                        context=plan.outputs,
                        path='outputs.{0}'.format(output_name),
                        replace=replace)
    for policy_name, policy in plan.get('policies', {}).items():
        scan_properties(policy.get('properties', {}),
                        handler,
                        scope=POLICIES_SCOPE,
                        context=policy,
                        path='policies.{0}.properties'.format(policy_name),
                        replace=replace)
    for group_name, scaling_group in plan.get('scaling_groups', {}).items():
        scan_properties(scaling_group.get('properties', {}),
                        handler,
                        scope=SCALING_GROUPS_SCOPE,
                        context=scaling_group,
                        path='scaling_groups.{0}.properties'.format(
                            group_name),
                        replace=replace)

    if collect_secrets and len(secrets) > 0:
        plan['secrets'] = list(secrets)
        secrets.clear()
