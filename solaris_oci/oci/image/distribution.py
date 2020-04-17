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

from .. import config as osi_config
from .repository import Repository
from .descriptor import Descriptor
import json

class Distribution():
    def __init__(self, descriptor_json=None):
        self.repositories = None
    
    def load(self):
        with osi_config.distribution_json_path.open() as distribution_file:
            # load distribution.json
            distribution_json = json.load(distribution_file)
            self.schemaVersion = distribution_json['schemaVersion']
            self.repositories = []
            for repository_descriptor_json in distribution_json['repositories']:
                self.repositories.append(Repository(repository_descriptor_json))

    def images(self, filter=None):
        images = []
        for repository in self.repositories:
            for index in repository.indexes:
                for manifest in index.manifests:
                    image = manifest.image.data.copy()
                    image['registry'] = repository.registry
                    image['repository'] = repository.name
                    image['id'] = repository.descriptor.digest
                    image['digest'] = index.descriptor.digest
                    image['tag'] = index.name
                    image['size'] = manifest.size
                    images.append(image)
        
        if filter is not None:
            names = []
            for reference in filter:
                records = reference.split(':')
                name = records[0]
                if len(records) == 2:
                    raise Exception('NYI')
                names.append(name)
            images = [i for i in images if i['repository'] in names]

        return images
