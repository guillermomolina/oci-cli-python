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
from solaris_oci.oci import oci_config, OCIError
from . import Repository, ImageInUseException

def split_image_name(image_name):
    splitted_image_name = image_name.split(':')            
    if len(splitted_image_name) == 1:
        splitted_image_name.append('latest')
    elif len(splitted_image_name) != 2:
        raise OCIError('Invalid image name (%s)' % image_name)
    return tuple(splitted_image_name)

class Distribution():
    def __init__(self):
        self.repositories = None
        distribution_file_path = pathlib.Path(oci_config['global']['path'], 
            'distribution.json')
        if distribution_file_path.is_file():
            self.load()
        else:
            self.create()

    def load(self):
        distribution_path = pathlib.Path(oci_config['global']['path'])
        distribution_file_path = distribution_path.joinpath('distribution.json')
        repository_list = RepositoryList.from_file(distribution_file_path)
        self.repositories = {}
        for repository_name in repository_list.get('Repositories'):
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository

    def create(self):
        distribution_file_path = pathlib.Path(oci_config['global']['path'], 
            'distribution.json')
        if distribution_file_path.is_file():
            raise OCIError('Distribution file (%s) already exists' % distribution_file_path)
        self.repositories = {}
        self.save()

    def save(self):
        distribution_path = pathlib.Path(oci_config['global']['path'])
        if not distribution_path.is_dir():
            distribution_path.mkdir(parents=True)
        repository_list_json = {
            'repositories': list(self.repositories.keys())
        }
        repository_list = RepositoryList.from_json(repository_list_json)
        distribution_file_path = distribution_path.joinpath('distribution.json')
        repository_list.save(distribution_file_path)

    def get_repository(self, repository_name):
        try:
            return self.repositories[repository_name]
        except:
            raise OCIError('Repository (%s) does not exist' % repository_name)

    def create_image(self, image_name, rootfs_tar_file, config_json):
        repository_name, tag = split_image_name(image_name)
        repository = self.repositories.get(repository_name, None)
        if repository is None:
            repository = Repository(repository_name)
            self.repositories[repository_name] = repository
            self.save()
        return repository.create_image(tag, rootfs_tar_file, config_json)

    def get_image(self, image_ref):        
        # image_ref, can either be:
        # small id (6 bytes, 12 octets, 96 bits), the first 12 octets from id
        # id (16 bytes, 32 octets, 256 bits), the sha256 hash
        # name of the repository (tag implied as latest)
        # repository_name:tag
        repository_name, tag = split_image_name(image_ref)
        for repository in self.repositories.values():
            for image in repository.images.values():                
                if image.id == image_ref:
                    return image
                if image.id[:12] == image_ref:
                    return image
                if image.repository == repository_name and image.tag == tag:
                    return image
        raise OCIError('Image (%s) is unknown' % image_ref)

    def remove_image(self, image_name):
        image = self.get_image(image_name)
        repository_name = image.repository
        tag = image.tag
        repository = self.get_repository(repository_name)
        repository.remove_image(tag)
        if repository.index is None:
            del self.repositories[repository_name]
            self.save()
