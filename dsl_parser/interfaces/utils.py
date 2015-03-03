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


from dsl_parser import functions
from dsl_parser.exceptions import DSLParsingLogicException
from dsl_parser.utils import flatten_schema


def validate_missing_inputs(inputs):
    for key, value in inputs.iteritems():
        if value is None:
            raise DSLParsingLogicException(
                107,
                'Input {0} is missing a value'.format(key))


def validate_inputs_types(inputs, inputs_schema):
    for input_key, _input in inputs_schema.iteritems():
        input_type = _input.get('type')
        if input_type is None:
            # no type defined - no validation
            continue
        input_val = inputs[input_key]

        if functions.parse(input_val) != input_val:
            # intrinsic function - not validated at the moment
            continue

        if input_type == 'integer':
            if isinstance(input_val, (int, long)) and not \
                    isinstance(input_val, bool):
                continue
        elif input_type == 'float':
            if isinstance(input_val, (int, float, long)) and not \
                    isinstance(input_val, bool):
                continue
        elif input_type == 'boolean':
            if isinstance(input_val, bool):
                continue
        elif input_type == 'string':
            continue
        else:
            raise DSLParsingLogicException(
                80, 'Unexpected type defined in inputs schema '
                    'for input {0} - unknown type is {1}'
                    .format(input_key, input_type))

        raise DSLParsingLogicException(
            50, 'Input type validation failed: Input {0} type '
                'is {1}, yet it was assigned with the value {2}'
                .format(input_key, input_type, input_val))


def merge_schema_and_instance_inputs(schema_inputs,
                                     instance_inputs):

    flattened_schema_inputs = flatten_schema(schema_inputs)
    merged_inputs = dict(
        flattened_schema_inputs.items() +
        instance_inputs.items())

    validate_missing_inputs(merged_inputs)
    validate_inputs_types(merged_inputs, schema_inputs)
    return merged_inputs


def operation_mapping(implementation, inputs, executor):
    return {
        'implementation': implementation,
        'inputs': inputs,
        'executor': executor
    }


def no_op():
    return operation_mapping(
        implementation='',
        inputs={},
        executor=None
    )
