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
from solaris_oci.oci import oci_config, OCIError
from solaris_oci.util import generate_random_name
from .container import Container

class Runtime():
    def __init__(self):
        self.containers = None
        runtime_path = pathlib.Path(oci_config['global']['path'])
        runtime_file_path = runtime_path.joinpath('runtime.json')
        if runtime_file_path.is_file():
            self.load()
        else:
            self.create()

    def load(self):
        runtime_path = pathlib.Path(oci_config['global']['path'])
        runtime_file_path = runtime_path.joinpath('runtime.json')
        with runtime_file_path.open() as runtime_file:
            runtime = json.load(runtime_file)
            self.containers = {}
            for container_id in runtime.get('containers', []):
                container = Container(container_id)
                self.containers[container_id] = container

    def create(self):
        runtime_path = pathlib.Path(oci_config['global']['path'])
        runtime_file_path = runtime_path.joinpath('runtime.json')
        if runtime_file_path.is_file():
            raise OCIError('Runtime file (%s) already exists' % runtime_file_path)
        self.containers = {}
        self.save()

    def save(self):
        runtime_path = pathlib.Path(oci_config['global']['path'])
        if not runtime_path.is_dir():
            runtime_path.mkdir(parents=True)
        runtime = {
            'containers': list(self.containers.keys())
        }
        runtime_file_path = runtime_path.joinpath('runtime.json')
        with runtime_file_path.open('w') as runtime_file:
            json.dump(runtime, runtime_file, separators=(',', ':'))

    def generate_container_name(self):
        container_names = [container.name for container in self.containers.values()]
        return generate_random_name(exclude_list=container_names)

    def create_container(self, image_name, name=None):
        container = Container()
        container.create(image_name, name or self.generate_container_name())
        self.containers[container.id] = container
        self.save()
        return container

    def remove_container(self, container_ref):
        container = self.get_container(container_ref)
        container_id = container.id
        container.remove()
        del self.containers[container_id]
        self.save()

    def get_container(self, container_ref):        
        # container_ref, can either be:
        # small id (6 bytes, 12 octets, 96 bits), the first 12 octets from id
        # id (16 bytes, 32 octets, 256 bits), the sha256 hash
        # name of the container
        if container_ref in self.containers:
            return self.containers[container_ref]
        for container_id, container in self.containers.items():
            if container_id[:12] == container_ref:
                return container
            if container.name == container_ref:
                return container
        raise OCIError('Container (%s) is unknown' % container_ref)
