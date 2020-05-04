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
from opencontainers.image.v1 import MediaTypeImageLayerNonDistributableGzip, \
    MediaTypeImageLayerNonDistributableZfsXZ, \
    MediaTypeImageLayerNonDistributableZfs, Descriptor
from solaris_oci import oci
from solaris_oci.util import digest_to_id, id_to_digest
from solaris_oci.util.file import compress, sha256sum, rm

class Layer:
    def __init__(self, diff_id=None, id=None, parent=None):
        self.diff_id = diff_id
        self.id = id
        self.parent = parent

    @property
    def diff_digest(self):
        return id_to_digest(self.diff_id)

    @property
    def size(self):
        if self.diff_id is not None:
            return oci.graph_driver.size(self.diff_id)
        return None

    @property
    def path(self):
        if self.diff_id is not None:
            return oci.graph_driver.path(self.diff_id)
        return None

    @property
    def parent_diff_id(self):
        if self.parent is not None:
            return parent.diff_id
        return None

    def create_diff(self):
        if self.diff_id is not None:
            raise('Layer (%s) already created' % self.diff_id)
        self.diff_id = oci.graph_driver.create(self.parent_diff_id)

    def commit_diff(self, compressed=True):
        oci.graph_driver.commit(self.diff_id)
        layers_path = pathlib.Path(oci.config['global']['path'], 'layers')
        if not layers_path.is_dir():
            layers_path.mkdir(parents=True)
        # TODO: Move to zfs_driver
        layer_file_path = layers_path.joinpath('layer.zfs')
        oci.graph_driver.save(self.diff_id, layer_file_path)
        media_type=MediaTypeImageLayerNonDistributableZfs
        if compressed:
            if compress(layer_file_path, method='xz', parallel=True) != 0:
                raise Exception('Could not compress layer file (%s)' 
                    % str(layer_file_path))
            media_type=MediaTypeImageLayerNonDistributableZfsXZ
            layer_file_path = layers_path.joinpath('layer.zfs.xz')
        # End TODO
        self.id = sha256sum(layer_file_path)
        if self.id is None:
            raise Exception('Could not get hash of file %s' % str(layer_file_path))
        layer_path = layers_path.joinpath(self.id)
        layer_file_path.rename(layer_path)
        layer_descriptor = Descriptor(
            digest=id_to_digest(self.id),
            size=layer_path.stat().st_size,
            media_type=media_type,
        )
        return layer_descriptor
   
    def add_file_to_diff(self, file_path, destination_path=None):
        if self.diff_id is not None:
            oci.graph_driver.add_file(self.diff_id, file_path, destination_path)

    def remove_diff(self):
        if self.diff_id is not None:
            oci.graph_driver.remove(self.diff_id)
            self.diff_id = None

    def remove(self):
        self.remove_diff()
        if self.id is not None:
            layer_file_path = pathlib.Path(oci.config['global']['path'], 
                'layers', self.id)
            rm(layer_file_path)
            self.id = None
       
