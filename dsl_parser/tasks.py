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


__author__ = 'idanmo'

import json

import parser
import multi_instance


def parse_dsl(dsl_location, alias_mapping_url,
              resources_base_url, **kwargs):
    result = parser.parse_from_url(dsl_url=dsl_location,
                                   alias_mapping_url=alias_mapping_url,
                                   resources_base_url=resources_base_url)
    return json.dumps(result)


def prepare_deployment_plan(plan, **kwargs):
    """
    Prepare a plan for deployment
    """
    plan = multi_instance.create_multi_instance_plan(plan)
    return json.dumps(plan)
