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


class Holder(object):
    def __init__(self,
                 value,
                 start_line=None,
                 start_column=None,
                 end_line=None,
                 end_column=None,
                 filename=None):
        self.value = value
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column
        self.filename = filename

    def __str__(self):
        return '{0}<{1}.{2}-{3}.{4} [{5}]>'.format(
            self.value,
            self.start_line,
            self.start_column,
            self.end_line,
            self.end_column,
            self.filename)

    def __repr__(self):
        return (
            '{name}(start_line={self.start_line}, '
            'start_column={self.start_column},'
            'end_line={self.end_line},'
            'end_column={self.end_column})'
        )

    def __contains__(self, key):
        key_holder, value_holder = self.get_item(key)
        return value_holder is not None

    def get_item(self, key):
        if not isinstance(self.value, dict):
            raise ValueError('Value is expected to be of type dict while it'
                             'is in fact of type {0}'
                             .format(type(self.value).__name__))
        for key_holder, value_holder in self.value.iteritems():
            if key_holder.value == key:
                return key_holder, value_holder
        return None, None

    def restore(self):
        if isinstance(self.value, dict):
            return dict((key_holder.restore(), value_holder.restore())
                        for key_holder, value_holder in self.value.iteritems())
        elif isinstance(self.value, list):
            return [value_holder.restore() for value_holder in self.value]
        elif isinstance(self.value, set):
            return set((value_holder.restore() for value_holder in self.value))
        else:
            return self.value

    @classmethod
    def of(cls, obj, filename=None):
        if isinstance(obj, Holder):
            return obj
        if isinstance(obj, dict):
            result = dict((cls.of(key, filename=filename),
                           cls.of(value, filename=filename))
                          for key, value in obj.iteritems())
        elif isinstance(obj, list):
            result = [cls.of(item, filename=filename) for item in obj]
        elif isinstance(obj, set):
            result = set((cls.of(item, filename=filename) for item in obj))
        else:
            result = obj
        return cls(result, filename=filename)

    def copy(self):
        return self.__class__(
            value=self.value,
            start_line=self.start_line,
            start_column=self.start_column,
            end_line=self.end_line,
            end_column=self.end_column,
            filename=self.filename)
