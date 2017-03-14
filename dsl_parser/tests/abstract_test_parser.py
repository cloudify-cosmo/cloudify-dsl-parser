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


import tempfile
import shutil
import os
import uuid
from functools import wraps
from multiprocessing import Process

import testtools
from mock import MagicMock

from dsl_parser.exceptions import DSLParsingException
from dsl_parser.parser import parse as dsl_parse
from dsl_parser.parser import parse_from_path as dsl_parse_from_path
from dsl_parser.import_resolver.default_import_resolver import \
    DefaultImportResolver
from dsl_parser.version import DSL_VERSION_PREFIX
from dsl_parser.multi_instance import (create_deployment_plan,
                                       modify_deployment)


def timeout(seconds=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            process = Process(None, func, None, args, kwargs)
            process.start()
            process.join(seconds)
            if process.is_alive():
                process.terminate()
                raise RuntimeError(
                    'test timeout exceeded [timeout={0}]'.format(seconds))
            if process.exitcode != 0:
                raise RuntimeError()
        return wraps(func)(wrapper)
    return decorator


class AbstractTestParser(testtools.TestCase):
    BASIC_VERSION_SECTION_DSL_1_0 = """
tosca_definitions_version: cloudify_dsl_1_0
    """

    BASIC_VERSION_SECTION_DSL_1_1 = """
tosca_definitions_version: cloudify_dsl_1_1
    """

    BASIC_VERSION_SECTION_DSL_1_2 = """
tosca_definitions_version: cloudify_dsl_1_2
    """

    BASIC_VERSION_SECTION_DSL_1_3 = """
tosca_definitions_version: cloudify_dsl_1_3
    """

    BASIC_NODE_TEMPLATES_SECTION = """
node_templates:
    test_node:
        type: test_type
        properties:
            key: "val"
        """

    BASIC_PLUGIN = """
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
"""

    PLUGIN_WITH_INSTALL_ARGS = """
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
        install_arguments: -r requirements.txt
"""

    BASIC_TYPE = """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                    implementation: test_plugin.install
                    inputs: {}
                terminate:
                    implementation: test_plugin.terminate
                    inputs: {}
        properties:
            install_agent:
                default: 'false'
            key: {}
            """

    BASIC_INPUTS = """
inputs:
    test_input:
        type: string
        default: test_input_default_value
"""

    BASIC_OUTPUTS = """
outputs:
    test_output:
        value: test_output_value
"""

    # note that some tests extend the BASIC_NODE_TEMPLATES 'inline',
    # which is why it's appended in the end
    MINIMAL_BLUEPRINT = """
node_types:
    test_type:
        properties:
            key:
                default: 'default'
    """ + BASIC_NODE_TEMPLATES_SECTION

    BLUEPRINT_WITH_INTERFACES_AND_PLUGINS = BASIC_NODE_TEMPLATES_SECTION + \
        BASIC_PLUGIN + BASIC_TYPE

    PLUGIN_WITH_INTERFACES_AND_PLUGINS_WITH_INSTALL_ARGS = \
        BASIC_NODE_TEMPLATES_SECTION + PLUGIN_WITH_INSTALL_ARGS + BASIC_TYPE

    def setUp(self):
        super(AbstractTestParser, self).setUp()
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)
        super(AbstractTestParser, self).tearDown()

    def make_file_with_name(self, content, filename, base_dir=None):
        base_dir = os.path.join(self._temp_dir, base_dir) \
            if base_dir else self._temp_dir
        filename_path = os.path.join(base_dir, filename)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        with open(filename_path, 'w') as f:
            f.write(content)
        return filename_path

    def make_yaml_file(self, content, as_uri=False):
        filename = 'tempfile{0}.yaml'.format(uuid.uuid4())
        filename_path = self.make_file_with_name(content, filename)
        return filename_path if not as_uri else self._path2url(filename_path)

    def _path2url(self, path):
        from urllib import pathname2url
        from urlparse import urljoin
        return urljoin('file:', pathname2url(path))

    def create_yaml_with_imports(self, contents, as_uri=False):
        yaml = """
imports:"""
        for content in contents:
            filename = self.make_yaml_file(content)
            yaml += """
    -   {0}""".format(filename if not as_uri else self._path2url(filename))
        return yaml

    def parse(self, dsl_string,
              resources_base_path=None,
              dsl_version=BASIC_VERSION_SECTION_DSL_1_0,
              resolver=None,
              validate_version=True):
        # add dsl version if missing
        if DSL_VERSION_PREFIX not in dsl_string:
            dsl_string = dsl_version + dsl_string
            if not resolver:
                resolver = DefaultImportResolver()
        return dsl_parse(dsl_string,
                         resources_base_path=resources_base_path,
                         resolver=resolver,
                         validate_version=validate_version)

    def parse_1_0(self, dsl_string, resources_base_path=None):
        return self.parse(dsl_string, resources_base_path,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_0)

    def parse_1_1(self, dsl_string, resources_base_path=None):
        return self.parse(dsl_string, resources_base_path,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_1)

    def parse_1_2(self, dsl_string, resources_base_path=None):
        return self.parse(dsl_string, resources_base_path,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_2)

    def parse_1_3(self, dsl_string, resources_base_path=None):
        return self.parse(dsl_string, resources_base_path,
                          dsl_version=self.BASIC_VERSION_SECTION_DSL_1_3)

    def parse_from_path(self, dsl_path, resources_base_path=None):
        return dsl_parse_from_path(dsl_path, resources_base_path)

    def parse_multi(self, yaml):
        return create_deployment_plan(self.parse_1_3(yaml))

    @staticmethod
    def modify_multi(plan, modified_nodes):
        return modify_deployment(
            nodes=plan['nodes'],
            previous_nodes=plan['nodes'],
            previous_node_instances=plan['node_instances'],
            modified_nodes=modified_nodes,
            scaling_groups=plan['scaling_groups'])

    def _assert_dsl_parsing_exception_error_code(
            self, dsl,
            expected_error_code, exception_type=DSLParsingException,
            parsing_method=None):
        if not parsing_method:
            parsing_method = self.parse
        try:
            parsing_method(dsl)
            self.fail()
        except exception_type as ex:
            self.assertEquals(expected_error_code, ex.err_code)
            return ex

    def get_node_by_name(self, plan, name):
        return [x for x in plan.node_templates if x['name'] == name][0]

    @staticmethod
    def _sort_result_nodes(result_nodes, ordered_nodes_ids):
        ordered_nodes = []

        for node_id in ordered_nodes_ids:
            for result_node in result_nodes:
                if result_node['id'] == node_id:
                    ordered_nodes.append(result_node)
                    break

        return ordered_nodes

    @staticmethod
    def _get_secret_mock(secret_id):
        secret_mock = MagicMock()
        secret_mock.value = secret_id + '_value'
        return secret_mock
