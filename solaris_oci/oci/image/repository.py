# Copyright 2020, Guillermo Adrián Molina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .descriptor import Descriptor
from .index import Index

class Repository():
    def __init__(self, descriptor_json=None):
        self.descriptor = None
        self.name = None
        self.indexes = None
        if descriptor_json is not None:
            self.descriptor = Descriptor(descriptor_json)
            self.load()

    def load(self):
        self.registry = self.descriptor.annotations.get('org.opencontainers.registry.ref.name')
        self.name = self.descriptor.annotations.get('org.opencontainers.repository.ref.name')
        repository_json = self.descriptor.read()
        self.indexes = []
        for index_descriptor_json in repository_json['indexes']:
            self.indexes.append(Index(index_descriptor_json))
