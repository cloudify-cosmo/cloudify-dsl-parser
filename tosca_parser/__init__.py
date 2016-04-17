# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Aria's parser Package
Path: aria.parser

Methods:
    * default_parser - Parser class instance with default values
    * default_expander - ParserExpander class instance with default values
    * parse - default_parser.parse method
    * expand - default parser language expansion method

"""

from .parser import Parser
from .extension_tools import ParserExtender

__version__ = '0.1.0.0'


default_parser = Parser()
default_expander = ParserExtender()

parse = default_parser.parse
extend = default_expander.extend
