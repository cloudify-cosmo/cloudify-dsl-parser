
from dsl_parser.import_resolver.abstract_import_resolver import (
    AbstractImportResolver)

from . import AbstractTestParser

BLUEPRINT_1 = """
node_types:
    resolver_type_1:
        properties:
            key:
                default: 'default'
node_templates:
    resolver_1:
        type: resolver_type_1
        properties:
            key: value_1
"""
BLUEPRINT_2 = """
node_types:
    resolver_type_2:
        properties:
            key:
                default: 'default'
"""


class TestParseWithResolver(AbstractTestParser):

    def test_parse_using_resolver(self):

        yaml_to_parse = """
imports:
    -   http://url1
    -   http://url2"""

        urls = []

        class CustomResolver(AbstractImportResolver):
            def resolve(self, url):
                urls.append(url)
                if len(urls) == 2:
                    return BLUEPRINT_2
                return BLUEPRINT_1
        custom_resolver = CustomResolver()
        self.parse(yaml_to_parse, resolver=custom_resolver)

        self.assertEqual(len(urls), 2)
        self.assertIn('http://url1', urls)
        self.assertIn('http://url2', urls)
