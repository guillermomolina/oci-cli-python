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
from opencontainers.distribution.v1 import RepositoryList
from .. import config as osi_config
from . import Repository

class Distribution():
    def __init__(self):
        self.repository_list = None
        self.repositories = None

    def load(self):
        distribution_path = osi_config.distribution_path
        distribution_json_path = osi_config.distribution_json_path
        with distribution_json_path.open() as distribution_json_file:
            distribution_json = json.load(distribution_json_file)
            self.repository_list = RepositoryList()
            self.repository_list.load(distribution_json)
            self.repositories = []
            for repository_name in self.repository_list.get('Repositories'):
                repository = Repository(repository_name)
                repository.load(distribution_path)
                self.repositories.append(repository)
