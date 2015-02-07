# flake8: NOQA
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


PROPERTY_TYPES_SCHEMA = {
    'enum': [
        'string',
        'integer',
        'float',
        'boolean'
    ]
}

PROPERTIES_SCHEMA_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': {
            # can't seem to be able to do the 'oneOf' inside the
            # 'properties' object, so some duplication is required here in
            # order to allow any type for the 'default' value.
            'anyOf': [
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'null'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'object'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'string'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'number'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'boolean'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'default': {
                            'type': 'array'
                        },
                        'description': {
                            'type': 'string'
                        },
                        'type': PROPERTY_TYPES_SCHEMA
                    },
                    'additionalProperties': False
                }
            ]
        }
    }
}


NODE_TEMPLATE_OPERATION_SCHEMA = {

    'oneOf': [
        {
            'type': 'string'
        },
        {
            'type': 'object',
            'minProperties': 0,
            'maxProperties': 0
        },
        {
            'type': 'object',
            'properties': {
                'implementation': {
                    'type': 'string'
                },
                'inputs': {
                    'type': 'object'
                },
                'executor': {
                    'type': 'string'
                }
            },
            'minProperties': 1,
            'additionalProperties': False
        }
    ]
}


NODE_TYPE_OPERATION_SCHEMA = {

    'oneOf': [
        {
            'type': 'string'
        },
        {
            'type': 'object',
            'minProperties': 0,
            'maxProperties': 0
        },
        {
            'type': 'object',
            'properties': {
                'implementation': {
                    'type': 'string'
                },
                'inputs': PROPERTIES_SCHEMA_SCHEMA,
                'executor': {
                    'type': 'string'
                }
            },
            'required': ['implementation'],
            'additionalProperties': False
        }
    ]
}

RELATIONSHIP_TYPE_OPERATION_SCHEMA = NODE_TYPE_OPERATION_SCHEMA
RELATIONSHIP_INSTANCE_OPERATION_SCHEMA = NODE_TEMPLATE_OPERATION_SCHEMA

NODE_TEMPLATE_INTERFACE_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': NODE_TEMPLATE_OPERATION_SCHEMA
    },
    'minProperties': 1
}

NODE_TYPE_INTERFACE_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': NODE_TYPE_OPERATION_SCHEMA
    },
    'minProperties': 1
}

NODE_TEMPLATE_INTERFACES_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': NODE_TEMPLATE_INTERFACE_SCHEMA
    },
    'minProperties': 1
}

NODE_TYPE_INTERFACES_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': NODE_TYPE_INTERFACE_SCHEMA
    },
    'minProperties': 1
}

RELATIONSHIP_TYPE_INTERFACE_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': RELATIONSHIP_TYPE_OPERATION_SCHEMA
    },
    'minProperties': 1
}

RELATIONSHIP_INSTANCE_INTERFACE_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': RELATIONSHIP_INSTANCE_OPERATION_SCHEMA
    },
    'minProperties': 1
}

RELATIONSHIP_TYPE_INTERFACES_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': RELATIONSHIP_TYPE_INTERFACE_SCHEMA
    },
    'minProperties': 1
}


RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': RELATIONSHIP_INSTANCE_INTERFACE_SCHEMA
    },
    'minProperties': 1
}


WORKFLOW_MAPPING_SCHEMA = {
    'type': 'object',
    'properties': {
        'mapping': {
            'type': 'string'
        },
        'parameters': PROPERTIES_SCHEMA_SCHEMA,
    },
    'required': ['mapping', 'parameters'],
    'additionalProperties': False
}

WORKFLOWS_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': {
            'oneOf': [
                {'type': 'string'},
                WORKFLOW_MAPPING_SCHEMA,
            ]
        },
    }
}

OUTPUTS_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': {
            'anyOf': [
                {
                    'type': 'object',
                    'properties': {
                        'description': {
                            'type': 'string'
                        },
                        'value': {
                            'type': 'number'
                        }
                    },
                    'required': ['value'],
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'description': {
                            'type': 'string'
                        },
                        'value': {
                            'type': 'string'
                        }
                    },
                    'required': ['value'],
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'description': {
                            'type': 'string'
                        },
                        'value': {
                            'type': 'object'
                        }
                    },
                    'required': ['value'],
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'description': {
                            'type': 'string'
                        },
                        'value': {
                            'type': 'array'
                        }
                    },
                    'required': ['value'],
                    'additionalProperties': False
                },
                {
                    'type': 'object',
                    'properties': {
                        'description': {
                            'type': 'string'
                        },
                        'value': {
                            'type': 'boolean'
                        }
                    },
                    'required': ['value'],
                    'additionalProperties': False
                },
            ]
        },
    }
}

UNIQUE_STRING_ARRAY_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'string'
    },
    'uniqueItems': True
}

IMPORTS_SCHEMA = UNIQUE_STRING_ARRAY_SCHEMA

MEMBERS_SCHEMA = UNIQUE_STRING_ARRAY_SCHEMA.copy()
MEMBERS_SCHEMA['minItems'] = 1


# Schema validation is currently done using a json schema validator
# ( see http://json-schema.org/ ), since no good YAML schema validator could
# be found (both for Python and at all).
#
# Python implementation documentation:
# http://python-jsonschema.readthedocs.org/en/latest/
# A one-stop-shop for easy API explanation:
# http://jsonary.com/documentation/json-schema/?
# A website which can create a schema from a given JSON automatically:
# http://www.jsonschema.net/#
# (Note: the website was not used for creating the schema below, as among
# other things, its syntax seems a bit different than the one used here,
# and should only be used as a reference)
DSL_SCHEMA = {
    'type': 'object',
    'properties': {
        'tosca_definitions_version': {
            'type': 'string'
        },
        'node_templates': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        #non-meta 'type'
                        'type': {
                            'type': 'string'
                        },
                        'instances': {
                            'type': 'object',
                            'properties': {
                                'deploy': {
                                    'type': 'number'
                                }
                            },
                            'required': ['deploy'],
                            'additionalProperties': False
                        },
                        'interfaces': NODE_TEMPLATE_INTERFACES_SCHEMA,
                        'relationships': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    #non-meta 'type'
                                    'type': {
                                        'type': 'string'
                                    },
                                    'target': {
                                        'type': 'string'
                                    },
                                    #non-meta 'properties'
                                    'properties': {
                                        'type': 'object'
                                    },
                                    'source_interfaces': RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA,
                                    'target_interfaces': RELATIONSHIP_INSTANCE_INTERFACES_SCHEMA,
                                },
                                'required': ['type', 'target'],
                                'additionalProperties': False
                            }
                        },
                        #non-meta 'properties'
                        'properties': {
                            'type': 'object'
                        }
                    },
                    'required': ['type'],
                    'additionalProperties': False
                }
            }
        },
        'plugins': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'source': {
                            'type': 'string'
                        },
                        'executor': {
                            'type': 'string'
                        },
                        'install': {
                            'type': 'boolean'
                        },
                        'install_arguments': {
                            'type': 'string'
                        }
                    },
                    'required': ['executor'],
                    'additionalProperties': False
                }
            },
            'additionalProperties': False
        },
        'policy_types': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'properties': PROPERTIES_SCHEMA_SCHEMA,
                        'source': {
                            'type': 'string'
                        }
                    },
                    'required': ['source'],
                    'additionalProperties': False
                },
            },
            'additionalProperties': False
        },
        'policy_triggers': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'parameters': PROPERTIES_SCHEMA_SCHEMA,
                        'source': {
                            'type': 'string'
                        }
                    },
                    'required': ['source'],
                    'additionalProperties': False
                },
                },
            'additionalProperties': False
        },
        'groups': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'members': MEMBERS_SCHEMA,
                        'policies': {
                            'type': 'object',
                            'patternProperties': {
                                '^': {
                                    'type': 'object',
                                    'properties': {
                                        #non-meta 'properties'
                                        'type': {
                                            'type': 'string'
                                        },
                                        'properties': {
                                            'type': 'object'
                                        },
                                        'triggers': {
                                            'type': 'object',
                                            'patternProperties': {
                                                '^': {
                                                    'type': 'object',
                                                    'properties': {
                                                        #non-meta 'properties'
                                                        'type': {
                                                            'type': 'string'
                                                        },
                                                        'parameters': {
                                                            'type': 'object'
                                                        },
                                                    },
                                                    'required': ['type'],
                                                    'additionalProperties': False
                                                },
                                            },
                                            'additionalProperties': False
                                        }
                                    },
                                    'required': ['type'],
                                    'additionalProperties': False
                                },
                            },
                            'additionalProperties': False
                        }
                    },
                    'required': ['policies', 'members'],
                    'additionalProperties': False
                },
            },
            'additionalProperties': False
        },
        'node_types': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'interfaces': NODE_TYPE_INTERFACES_SCHEMA,
                        #non-meta 'properties'
                        'properties': PROPERTIES_SCHEMA_SCHEMA,
                        'derived_from': {
                            'type': 'string'
                        },
                    },
                    'additionalProperties': False
                }
            }
        },
        'type_implementations': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        #non-meta 'properties'
                        'properties': {
                            'type': 'object'
                        },
                        'type': {
                            'type': 'string'
                        },
                        'node_ref': {
                            'type': 'string'
                        },
                    },
                    'required': ['node_ref', 'type'],
                    'additionalProperties': False
                }
            }
        },
        'workflows': WORKFLOWS_SCHEMA,
        'relationships': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'derived_from': {
                            'type': 'string'
                        },
                        'source_interfaces': RELATIONSHIP_TYPE_INTERFACES_SCHEMA,
                        'target_interfaces': RELATIONSHIP_TYPE_INTERFACES_SCHEMA,
                        #non-meta 'properties'
                        'properties': PROPERTIES_SCHEMA_SCHEMA
                    },
                    'additionalProperties': False
                }
            }
        },
        'relationship_implementations': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string'
                        },
                        'source_node_ref': {
                            'type': 'string'
                        },
                        'target_node_ref': {
                            'type': 'string'
                        },
                        #non-meta 'properties'
                        'properties': {
                            'type': 'object'
                        },
                    },
                    'required': ['source_node_ref', 'target_node_ref',
                                 'type'],
                    'additionalProperties': False
                }
            }
        },
        'inputs': PROPERTIES_SCHEMA_SCHEMA,
        'outputs': OUTPUTS_SCHEMA
    },
    'required': ['tosca_definitions_version', 'node_templates'],
    'additionalProperties': False
}