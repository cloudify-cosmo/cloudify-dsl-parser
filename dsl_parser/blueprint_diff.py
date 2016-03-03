########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


def blueprint_diff(old_blueprint, new_blueprint):

    path_of_keys = []
    output = {}

    diff(old_blueprint, new_blueprint, path_of_keys, output)
    diff(new_blueprint, old_blueprint, path_of_keys, output,
         look_backwards=True)

    return output


def diff(old, new, path_of_keys, output, look_backwards=False):
    """
    Get two dicts and return a dict representing the difference between them

    :param old: The dict before the change
    :param new: The dict after the change
    :param path_of_keys: A list of dictionary keys that helps us track
                         our position in nested dictionaries during recursive
                         calls
    :param output: A dictionary representing the changes between the
                   dictionaries
    :param look_backwards: If false, it detects items that are in the new dict,
                           but were not in the old dict ('added items'),
                           and items that have the same key but not the same
                           value ('modified items').
                           If true, it detects items that were in the old dict,
                           but are not in the new dict ('removed items')
    :rtype: dict
    :return:
    A dict representing the differences between the two dicts, with respect to
    the value of `look_backwards`
    """
    for key in new:

        value = new[key]
        path_of_keys.append(key)

        if not path_exists(old, path_of_keys):
            status = 'removed' if look_backwards else 'added'
            add_entry(output, path_of_keys, status)

        elif type(value) is not dict:
            old_value = get_value(old, path_of_keys)
            if value != old_value and not look_backwards:
                if type(value) is list:
                    modified = list_diff(old_value, value)
                else:
                    modified = 'modified'
                add_entry(output, path_of_keys, modified)

        else:
            diff(old, value, path_of_keys, output, look_backwards)

        del path_of_keys[-1]


def list_diff(old, new):
    """
    create a diff between two lists

    the diff reflects the following changes:
    1. 'removed items': items in the old list that are not in the new list.
    2. 'added items': items in the new list that were not in the old list.
    3. 'moved items': items that are both in the new and the old lists, but
                      their indexes differ between the lists.

              ### old blueprint ###           ### new blueprint ###

            - type: "type1"                 # added type4
              target: "target1"             - type: "type4"
              properties:                     target: "target4"
                  connection_type: ""         properties:
              source_interfaces: {}             connection_type: ""
              target_interfaces: {}           source_interfaces: {}
                                              target_interfaces: {}
            - type: "type2"
              target: "target2"             # type2 stayed the same
              properties:                   - type: "type2"
                  connection_type: ""         target: "target2"
              source_interfaces: {}           properties:
              target_interfaces: {}               connection_type: ""
                                              source_interfaces: {}
            - type: "type3"                   target_interfaces: {}
              target: "target3"
              properties:                   # type1 moved here
                  connection_type: ""       - type: "type1"
              source_interfaces: {}           target: "target1"
              target_interfaces: {}           properties:
                                                  connection_type: ""
                                              source_interfaces: {}
                                              target_interfaces: {}

                                            # removed type3

                               ### output diff ###

                                    o0: 2
                                    o2: removed
                                    n0: added

    :param old: the base list
    :param new: the list to compare to
    :rtype: dict
    :return: a dict representing the difference between the lists
    """
    added_items = set(range(len(new)))
    output = {}
    for idx, item in enumerate(old):

        # item was removed
        if item not in new:
            output['o' + str(idx)] = 'removed'
        else:
            new_idx = new.index(item)

            # item moved to a new position
            if idx != new_idx:
                output['o' + str(idx)] = new_idx

            added_items.remove(new_idx)

    for idx in added_items:
        output['n' + str(idx)] = 'added'

    return output


def get_value(d, path_of_keys):

    for key in path_of_keys:
        if type(d[key]) is dict:
            d = d[key]
        else:
            return d[key]


def path_exists(d, path_of_keys):

    try:
        for key in path_of_keys:
            d = d[key]

    except KeyError:
        return False

    return True


def add_entry(output, path_of_keys, status):

    for idx, key in enumerate(path_of_keys):
        if key in output:
            output = output[key]
        else:
            break

    dict_to_insert = convert_path_of_keys_to_dict(path_of_keys[idx:], status)
    output.update(dict_to_insert)


def convert_path_of_keys_to_dict(path_of_keys, value):

    if not path_of_keys:
        return {}

    key = path_of_keys[0]

    if len(path_of_keys) == 1:
        return {key: value}
    else:
        return {key: convert_path_of_keys_to_dict(path_of_keys[1:], value)}
