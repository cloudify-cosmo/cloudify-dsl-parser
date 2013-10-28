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

__author__ = 'ran'

import tempfile
import shutil
import unittest
import os
import uuid
import yaml
from dsl_parser.parser import DSLParsingException
from dsl_parser.parser import parse


class AbstractTestParser(unittest.TestCase):
    BASIC_APPLICATION_TEMPLATE_SECTION = """
application_template:
    name: test_app
    topology:
        -   name: test_node
            type: test_type
            properties:
                key: "val"
        """

    BASIC_INTERFACE_AND_PLUGIN = """
interfaces:
    test_interface1:
        operations:
            -   "install"
            -   "terminate"

plugins:
    test_plugin:
        derived_from: "cloudify.plugins.agent_plugin"
        properties:
            interface: "test_interface1"
            url: "http://test_url.zip"
            """

    BASIC_TYPE = """
types:
    test_type:
        interfaces:
            -   test_interface1
        properties:
            install_agent: 'false'
            """

    POLICIES_SECTION = """
policies:
    types:
        test_policy:
            message: "test policy message"
            policy: "test policy code"
    rules:
        test_rule:
            message: "test rule message"
            rule: "test rule code"
            """

    #note that some tests extend the BASIC_APPLICATION_TEMPLATE 'inline', which is why it's appended in the end
    MINIMAL_APPLICATION_TEMPLATE = """
types:
    test_type: {}
    """ + BASIC_APPLICATION_TEMPLATE_SECTION

    APPLICATION_TEMPLATE_WITH_INTERFACES_AND_PLUGINS = BASIC_APPLICATION_TEMPLATE_SECTION + \
                                                       BASIC_INTERFACE_AND_PLUGIN + BASIC_TYPE

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)

    def make_alias_yaml_file(self, alias):
        filename = 'tempfile{0}.yaml'.format(uuid.uuid4())
        filename_path = os.path.join(self._temp_dir, filename)
        with open(filename_path, 'w') as outfile:
            outfile.write(yaml.dump(alias, default_flow_style=True))
        return self._path2url(filename_path)

    def make_file_with_name(self, content, filename):
        filename_path = os.path.join(self._temp_dir, filename)
        with open(filename_path, 'w') as f:
            f.write(content)
        return filename_path

    def make_yaml_file(self, content, as_uri=False):
        filename = 'tempfile{0}.yaml'.format(uuid.uuid4())
        filename_path = self.make_file_with_name(content, filename)
        return (filename_path if not as_uri else self._path2url(filename_path))

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

    def _assert_dsl_parsing_exception_error_code(self, dsl, expected_error_code, exception_type=DSLParsingException,
                                                 parsing_method=parse):
        try:
            parsing_method(dsl)
            self.fail()
        except exception_type, ex:
            self.assertEquals(expected_error_code, ex.err_code)
            return ex