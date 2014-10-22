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


class MissingRequiredInputError(Exception):
    """
    An error raised when a deployment is created and a required input
    was not specified on its creation.
    """
    def __init__(self, *args, **kwargs):
        super(MissingRequiredInputError, self).__init__(*args, **kwargs)


class UnknownInputError(Exception):
    """
    An error raised when an unknown input is specified on deployment creation.
    """
    def __init__(self, *args, **kwargs):
        super(UnknownInputError, self).__init__(*args, **kwargs)


class FunctionEvaluationError(Exception):
    """
    An error raised when an intrinsic function was unable to get evaluated.
    """
    def __init__(self, func_name, message=None):
        msg = 'Unable to evaluate {0} function'.format(func_name)
        if message:
            msg = '{0}: {1}'.format(msg, message)
        super(FunctionEvaluationError, self).__init__(msg)


class DSLParsingException(Exception):
    def __init__(self, err_code, *args):
        super(DSLParsingException, self).__init__(*args)
        self.err_code = err_code


class DSLParsingLogicException(DSLParsingException):
    pass


class DSLParsingFormatException(DSLParsingException):
    pass
