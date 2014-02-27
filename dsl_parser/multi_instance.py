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
__author__ = 'dan'

import rel_graph


def create_multi_instance_plan(plan):
    """
    Expand node instances based on number of instances to deploy and
    defined relationships
    """
    graph = rel_graph.build_initial_node_graph(plan)
    m_graph = rel_graph.build_multi_instance_node_graph(graph)
    m_plan = rel_graph.create_multi_instance_plan_from_multi_instance_graph(
        plan, m_graph)
    return m_plan
