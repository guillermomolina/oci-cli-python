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
from solaris_oci import oci
from .container import Container

class Runtime():
    def __init__(self):
        self.containers = None
        containers_path = pathlib.Path(oci.config['containers']['path'])
        self.path = containers_path
        self.registry_file_path = self.path.joinpath('runtime.json')
        if self.registry_file_path.is_file():
            self.load()
        else:
            self.create()

    def load(self):
        with self.registry_file_path.open() as registry_file:
            registry = json.load(registry_file)
            self.containers = {}
            for container_id in registry.get('containers', []):
                container = Container(container_id)
                self.containers[container_id] = container

    def create(self):
        self.containers = {}
        self.save()

    def save(self):
        if not self.path.is_dir():
            self.path.mkdir(parents=True)
        registry = {
            'containers': list(self.containers.keys())
        }
        with self.registry_file_path.open('w') as registry_file:
            json.dump(registry, registry_file, separators=(',', ':'))

    def create_container(self, image):
        container = Container()
        container.create(image)
        self.containers[container.id] = container
        self.save()
        return container

    def remove_container(self, container_id):
        container = self.containers.get(container_id, None)
        if container is None:
            raise Exception('Container (%s) does not exist' % container_id)
        container.remove()
        del self.containers[container_id]
        self.save()

    def get_container(self, container_id):
        return self.containers.get(container_id, None)
