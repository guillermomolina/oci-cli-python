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
from solaris_oci.util.file import untar, sha256sum

class Layer:
    def __init__(self, image_digest, digest=None, parent=None):
        self.image_id = image_digest.split(':')[1]
        self.parent_id = None
        if parent is not None:
            self.parent_id = parent.id
        self.id = None
        if digest is not None:
            self.id = digest.split(':')[1]
        self.path = None

    @property
    def digest(self):
        return 'sha256:' + self.id

    @property
    def size(self):
        return oci.graph_driver.get_layer_size(self.image_id, self.id)

    def create(self):
        self.id = oci.graph_driver.create_layer(self.image_id, self.parent_id)
        layers_path = pathlib.Path(oci.config['layers']['path'])
        self.path = layers_path.joinpath('sha256', self.id)

    def destroy(self):
        oci.graph_driver.destroy_layer(self.image_id, self.id, self.parent_id)
        self.path = None

    def create_archive(self, file_path):
        oci.graph_driver.save_layer(self.image_id, self.id, file_path)

    def commit(self):
        oci.graph_driver.commit_layer(self.image_id, self.id)
   
    def add(self, file_path, destination_path=None):
        local_destination_path = self.path
        if destination_path is not None:
            local_destination_path.joinpath(destination_path)
        if file_path.suffix == '.tar':
            untar(file_path, local_destination_path)
            return
        raise NotImplementedError()

