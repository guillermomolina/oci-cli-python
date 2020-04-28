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
import pathlib
from opencontainers.distribution.v1 import RepositoryList
from solaris_oci import oci
from . import Repository

class Distribution():
    def __init__(self):
        self.repositories = {}
        images_path = pathlib.Path(oci.config['images']['path'])
        self.path = images_path
        self.registry_file_path = self.path.joinpath('distribution.json')
        if self.registry_file_path.is_file():
            self.load()
        else:
            self.create()

    def load(self):
        repository_list = RepositoryList.from_file(self.registry_file_path)
        self.repositories = {}
        for repository_name in repository_list.get('Repositories'):
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository

    def create(self):
        self.repositories = {}
        self.save()

    def save(self):
        if not self.path.is_dir():
            self.path.mkdir(parents=True)
        repository_list_json = {
            'repositories': list(self.repositories.keys())
        }
        repository_list = RepositoryList.from_json(repository_list_json)
        repository_list.save(self.registry_file_path)

    def create_image(self, repository_name, tag_name, rootfs_tar_file, config_json):
        repository = self.repositories.get(repository_name, None)
        if repository is None:
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository
            self.save()
        return repository.create_image(tag_name, rootfs_tar_file, config_json)

    def destroy_image(self, repository_name, tag_name):
        repository = self.repositories.get(repository_name, None)
        if repository is None:
            raise Exception('Repository (%s) does not exist' % repository_name)
        repository = repository.destroy_image(tag_name)
        if repository is None:
            del self.repositories[repository_name]
        else:
            # Not really needed
            self.repositories[repository_name] = repository
        self.save()
