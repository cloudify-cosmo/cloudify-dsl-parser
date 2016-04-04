
from yaml import safe_dump as yaml_dump
from yaml import safe_load as yaml_load

from dsl_parser import constants
from dsl_parser.exceptions import DSLParsingLogicException

from . import AbstractTestParser


class PluginsTest(AbstractTestParser):

    def test_plugin_with_install_true_existing_source(self):
        self._test(install=True,
                   source='dummy')

    def test_plugin_with_install_true_existing_package_name(self):
        self._test(install=True,
                   package_name='package')

    def test_plugin_with_install_false_existing_source(self):
        self._test(install=False,
                   source='dummy')

    def test_plugin_with_install_false_existing_package_name(self):
        self._test(install=False,
                   package_name='package')

    def test_plugin_with_install_false_missing_source_and_package(self):
        self._test(install=False)

    def test_plugin_with_missing_install_existing_source(self):
        self._test(source='dummy')

    def test_plugin_with_missing_install_existing_package(self):
        self._test(package_name='package')

    def test_plugin_with_missing_install_missing_source_and_package(self):
        self._test(expected_error_code=50)

    def test_plugin_with_install_true_missing_source_and_package(self):
        self._test(install=True, expected_error_code=50)

    def _test(self, install=None, source=None, package_name=None,
              expected_error_code=None):
        yaml = """
plugins:
  test_plugin: {}

node_templates:
  test_node:
    type: type
    interfaces:
      test_interface1:
        install: test_plugin.install

node_types:
  type: {}
"""
        raw_parsed_yaml = yaml_load(yaml)
        plugin = {
            'executor': 'central_deployment_agent'
        }

        if install is not None:
            plugin['install'] = install
        if source is not None:
            plugin['source'] = source
        if package_name is not None:
            plugin['package_name'] = package_name
        raw_parsed_yaml['plugins']['test_plugin'] = plugin
        result = yaml_dump(raw_parsed_yaml)
        yaml = '\n{0}'.format(result)
        if expected_error_code:
            self._assert_dsl_parsing_exception_error_code(
                yaml, expected_error_code, DSLParsingLogicException)
        else:
            result = self.parse_1_2(yaml)
            plugin = result['nodes'][0][
                constants.DEPLOYMENT_PLUGINS_TO_INSTALL][0]
            if install is not None:
                self.assertEqual(install, plugin['install'])
            if source is not None:
                self.assertEqual(source, plugin['source'])
            if package_name is not None:
                self.assertEqual(package_name, plugin['package_name'])
