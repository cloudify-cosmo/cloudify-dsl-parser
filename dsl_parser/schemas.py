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


WORKFLOWS_SCHEMA = {
    'type': 'object',
    'patternProperties': {
        '^': {
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
                            #the below 'type' is our own "type" and not the schema's meta language
                            'type': {
                                'type': 'string'
                            },
                            'workflows': WORKFLOWS_SCHEMA,
                            #the below 'properties' is our own "properties" and not the schema's meta language
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
                        #the below 'properties' is our own "properties" and not the schema's meta language
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
                    'required': ['properties'],
                    'additionalProperties': False
                }
            }
        },
        'types': {
            'type': 'object',
            'patternProperties': {
                '^': {
                    'type': 'object',
                    'properties': {
                        'interfaces': {
                            'type': 'array',
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
                                ],
                                'minItems': 1
                            }
                        },
                        'workflows': WORKFLOWS_SCHEMA,
                        #the below 'properties' is our own "properties" and not the schema's meta language
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