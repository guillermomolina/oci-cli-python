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
        self.repositories = None
        try:
            self.load()
        except:
            self.create()

    def load(self):
        distribution_path = pathlib.Path(oci.config['global']['path'])
        distribution_file_path = distribution_path.joinpath('distribution.json')
        repository_list = RepositoryList.from_file(distribution_file_path)
        self.repositories = {}
        for repository_name in repository_list.get('Repositories'):
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository

    def create(self):
        distribution_file_path = pathlib.Path(oci.config['global']['path'], 
            'distribution.json')
        if distribution_file_path.exists():
            raise Exception('Distribution file (%s) already exists' % distribution_file_path)
        self.repositories = {}
        self.save()

    def save(self):
        distribution_path = pathlib.Path(oci.config['global']['path'])
        if not distribution_path.is_dir():
            distribution_path.mkdir(parents=True)
        repository_list_json = {
            'repositories': list(self.repositories.keys())
        }
        repository_list = RepositoryList.from_json(repository_list_json)
        distribution_file_path = distribution_path.joinpath('distribution.json')
        repository_list.save(distribution_file_path)

    def create_image(self, repository_name, tag_name, rootfs_tar_file, config_json):
        repository = self.repositories.get(repository_name, None)
        if repository is None:
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository
            self.save()
        return repository.create_image(tag_name, rootfs_tar_file, config_json)

    def get_repository(self, repository_name):
        repository = self.repositories.get(repository_name, None)
        if repository is None:
            raise Exception('Repository (%s) does not exist' % repository_name)
        return repository

    def get_image(self, repository_name, tag_name):
        repository = self.get_repository(repository_name)
        return repository.get_image(tag_name)

    def remove_image(self, repository_name, tag_name):
        repository = self.get_repository(repository_name)
        repository.remove_image(tag_name)
        if repository.index is None:
            del self.repositories[repository_name]
            self.save()
