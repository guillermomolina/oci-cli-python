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

import json 
from opencontainers.distribution.v1 import TagList
from . import Image

class Repository():
    def __init__(self, name):
        self.name = name
        self.tag_list = None
        self.images = None

    def load(self, distribution_path):
        repository_path = distribution_path.joinpath(self.name)
        repository_json_path = repository_path.joinpath('repository.json')
        with repository_json_path.open() as repository_json_file:
            repository_json = json.load(repository_json_file)
            self.tag_list = TagList(self.name)
            self.tag_list.load(repository_json)
            self.images = []
            for tag_name in self.tag_list.get('Tags'):
                image = Image(self.name, tag_name)
                image.load(distribution_path)
                self.images.append(image)
