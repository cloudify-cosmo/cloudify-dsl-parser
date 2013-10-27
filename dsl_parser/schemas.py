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


SINGLE_WORKFLOW_SCHEMA = {
    'type': 'object',
    'oneOf': [
        {
            'type': 'object',
            'properties': {
                'radial': {
                    'type': 'string'
                }
            },
            'required': ['radial'],
            'additionalProperties': False
        },
        {
            'type': 'object',
            'properties': {
                'ref': {
                    'type': 'string'
                }
            },
            'required': ['ref'],
            'additionalProperties': False
        }
    ]
}

WORKFLOWS_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': SINGLE_WORKFLOW_SCHEMA
    }
}

INSTANCE_OR_TYPE_POLICIES_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': {
            'type': 'object',
            'properties': {
                'rules': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            #non-meta 'type'
                            'type': {
                                'type': 'string'
                            },
                            #non-meta 'properties'
                            'properties': {
                                'type': 'object',
                                'properties': {
                                    'state': {
                                        'type': 'string'
                                    },
                                    'value': {
                                        'type': 'string'
                                    }
                                },
                                'required': ['state', 'value'],
                                'additionalProperties': False
                            }
                        },
                        'required': ['type', 'properties'],
                        'additionalProperties': False
                    },
                    'minItems': 1
                }
            },
            'required': ['rules'],
            'additionalProperties': False
        }
    }
}

# Schema validation is currently done using a json schema validator ( see http://json-schema.org/ ),
# since no good YAML schema validator could be found (both for Python and at all).
#
# Python implementation documentation: http://python-jsonschema.readthedocs.org/en/latest/
# A one-stop-shop for easy API explanation: http://jsonary.com/documentation/json-schema/?
# A website which can create a schema from a given JSON automatically: http://www.jsonschema.net/#
#   (Note: the website was not used for creating the schema below, as among other things, its syntax seems a bit
#   different than the one used here, and should only be used as a reference)
DSL_SCHEMA = {
    'type': 'object',
    'properties': {
        'application_template': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string'
                },
                'topology': {
                    'type': 'array',
                    'minItems': 1,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string'
                            },
                            #non-meta 'type'
                            'type': {
                                'type': 'string'
                            },
                            'workflows': WORKFLOWS_SCHEMA,
                            'policies': INSTANCE_OR_TYPE_POLICIES_SCHEMA,
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
                                        'plugin': {
                                            'type': 'string'
                                        },
                                        'bind_at': {
                                            'type': 'string'
                                        },
                                        'run_on_node': {
                                            'type': 'string'
                                        },
                                        'workflow': SINGLE_WORKFLOW_SCHEMA,
                                        'interface': {
                                            'type': 'object',
                                            'properties': {
                                                'name': {
                                                    'type': 'string'
                                                },
                                                'operations': {
                                                    'type': 'array',
                                                    'items': {
                                                        'type': 'string'
                                                    },
                                                    'uniqueItems': True,
                                                    'minItems': 1
                                                }
                                            },
                                            'required': ['name', 'operations'],
                                            'additionalProperties': False
                                        }
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
                        'required': ['name', 'type'],
                        'additionalProperties': False
                    }
                }
            },
            'required': ['name', 'topology'],
            'additionalProperties': False
        },
        'interfaces': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'operations': {
                            'type': 'array',
                            'items': {
                                'type': 'string'
                            },
                            'uniqueItems': True,
                            'minItems': 1
                        }
                    },
                    'required': ['operations'],
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
                        'derived_from': {
                            'type': 'string'
                        },
                        #non-meta 'properties'
                        'properties': {
                            'type': 'object',
                            'properties': {
                                'interface': {
                                    'type': 'string'
                                },
                                'url': {
                                    'type': 'string'
                                }
                            },
                            'required': ['interface', 'url'],
                            'additionalProperties': False
                        }
                    },
                    'required': ['derived_from', 'properties'],
                    'additionalProperties': False
                }
            }
        },
        'policies': {
            'type': 'object',
            'properties': {
                'types': {
                    'type': 'object',
                    'patternProperties': {
                        '^': {
                            'type': 'object',
                            'oneOf': [
                                {
                                    'type': 'object',
                                    'properties': {
                                        'message': {
                                            'type': 'string'
                                        },
                                        'policy': {
                                            'type': 'string'
                                        }
                                    },
                                    'required': ['message', 'policy'],
                                    'additionalProperties': False
                                },
                                {
                                    'type': 'object',
                                    'properties': {
                                        'message': {
                                            'type': 'string'
                                        },
                                        'ref': {
                                            'type': 'string'
                                        }
                                    },
                                    'required': ['message', 'ref'],
                                    'additionalProperties': False
                                }
                            ]
                        }
                    }
                },
                'rules': {
                    'type': 'object',
                    'patternProperties': {
                        '^': {
                            'type': 'object',
                            'properties': {
                                'message': {
                                    'type': 'string'
                                },
                                'rule': {
                                    'type': 'string'
                                }
                            },
                            'required': ['message', 'rule'],
                            'additionalProperties': False
                        }
                    }
                }
            },
            'additionalProperties': False
        },
        'types': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'interfaces': {
                            'type': 'array',
                            'minItems': 1,
                            'items': {
                                'oneOf': [
                                    {
                                        'type': 'object',
                                        'patternProperties': {
                                            '^': {
                                                'type': 'string'
                                            }
                                        },
                                        'maxProperties': 1,
                                        'minProperties': 1
                                    },
                                    {
                                        'type': 'string'
                                    }
                                ]
                            }
                        },
                        'workflows': WORKFLOWS_SCHEMA,
                        'policies': INSTANCE_OR_TYPE_POLICIES_SCHEMA,
                        #non-meta 'properties'
                        'properties': {
                            'type': 'object'
                        },
                        'derived_from': {
                            'type': 'string'
                        }
                    },
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
                        'plugin': {
                            'type': 'string'
                        },
                        'bind_at': {
                            'type': 'string'
                        },
                        'run_on_node': {
                            'type': 'string'
                        },
                        'derived_from': {
                            'type': 'string'
                        },
                        'workflow': SINGLE_WORKFLOW_SCHEMA,
                        'interface': {
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'type': 'string'
                                },
                                'operations': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string'
                                    },
                                    'uniqueItems': True,
                                    'minItems': 1
                                }
                            },
                            'required': ['name', 'operations'],
                            'additionalProperties': False
                        }
                    },
                    'additionalProperties': False
                }
            }
        }
    },
    'required': ['application_template'],
    'additionalProperties': False
}


IMPORTS_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'string'
    },
    'uniqueItems': True
}