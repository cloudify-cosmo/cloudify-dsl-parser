
from dsl_parser.framework import parser
from dsl_parser.framework.elements import Element
from dsl_parser.elements import data_types, version


def validate(obj, element_cls):
    class TestElement(Element):
        schema = {
            'tosca_definitions_version': version.ToscaDefinitionsVersion,
            'test': element_cls,
            'data_types': data_types.DataTypes
        }
    obj = {
        'tosca_definitions_version': 'cloudify_dsl_1_1',
        'test': obj
    }
    parser.parse(obj,
                 element_cls=TestElement,
                 inputs={
                     'validate_version': True
                 },
                 strict=True)
