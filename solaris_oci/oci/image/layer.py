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
import logging
from opencontainers.image.v1 import MediaTypeImageLayerNonDistributableGzip, \
    MediaTypeImageLayerNonDistributableZfsXZ, \
    MediaTypeImageLayerNonDistributableZfs, Descriptor
from solaris_oci.oci import oci_config, OCIError
from solaris_oci.util import digest_to_id, id_to_digest
from solaris_oci.util.file import compress, sha256sum, rm
from solaris_oci.oci.graph import Graph, NodeInUseException
from solaris_oci.oci.image import LayerInUseException

log = logging.getLogger(__name__)

class Layer:
    def __init__(self, diff_id=None, id=None, parent=None):
        log.debug('Creating instance of %s(%s)' % (type(self).__name__, id or ''))
        self.diff_id = diff_id
        self.id = id
        self.parent = parent

    @property
    def diff_digest(self):
        return id_to_digest(self.diff_id)

    @property
    def size(self):
        if self.diff_id is not None:
            return Graph.driver().size(self.diff_id)
        return None

    @property
    def path(self):
        if self.diff_id is not None:
            return Graph.driver().path(self.diff_id)
        return None

    @property
    def parent_diff_id(self):
        if self.parent is not None:
            return self.parent.diff_id
        return None

    def create_diff(self):
        if self.diff_id is not None:
            raise('Layer (%s) already created' % self.diff_id)
        self.diff_id = Graph.driver().create(self.parent_diff_id)

    def commit_diff(self, compressed=True):
        log.debug('Start committing diff (%s) of layer (%s)' % 
            (self.diff_id, self.id))
        Graph.driver().commit(self.diff_id)
        layers_path = pathlib.Path(oci_config['global']['path'], 'layers')
        if not layers_path.is_dir():
            layers_path.mkdir(parents=True)
        # TODO: Move to zfs_driver
        layer_file_path = layers_path.joinpath('layer.zfs')
        log.debug('Start saving diff (%s) of layer (%s) to file (%s)' % 
            (self.diff_id, self.id, str(layer_file_path)))
        Graph.driver().save(self.diff_id, layer_file_path)
        log.debug('Finish saving diff (%s) of layer (%s) to file (%s)' % 
            (self.diff_id, self.id, str(layer_file_path)))
        media_type=MediaTypeImageLayerNonDistributableZfs
        if compressed:
            log.debug('Start compressing file (%s)' % str(layer_file_path))
            if compress(layer_file_path, method='xz', parallel=True) != 0:
                raise OCIError('Could not compress layer file (%s)' 
                    % str(layer_file_path))
            log.debug('Finish compressing file (%s)' % str(layer_file_path))
            media_type=MediaTypeImageLayerNonDistributableZfsXZ
            layer_file_path = layers_path.joinpath('layer.zfs.xz')
        # End TODO
        self.id = sha256sum(layer_file_path)
        if self.id is None:
            raise OCIError('Could not get hash of file %s' % str(layer_file_path))
        layer_path = layers_path.joinpath(self.id)
        layer_file_path.rename(layer_path)
        layer_descriptor = Descriptor(
            digest=id_to_digest(self.id),
            size=layer_path.stat().st_size,
            media_type=media_type,
        )
        log.debug('Finish committing diff (%s) of layer (%s)' % 
            (self.diff_id, self.id))
        return layer_descriptor
   
    def add_file_to_diff(self, file_path, destination_path=None):
        if self.diff_id is not None:
            Graph.driver().add_file(self.diff_id, file_path, destination_path)
   
    def add_tar_file_to_diff(self, tar_file, destination_path=None):
        if self.diff_id is not None:
            log.debug('Start adding tar file to diff (%s) of layer (%s)' % 
                (self.diff_id, self.id))
            Graph.driver().add_tar_file(self.diff_id, tar_file, destination_path)
            log.debug('Finish adding tar file to diff (%s) of layer (%s)' % 
                (self.diff_id, self.id))

    def remove_diff(self):
        if self.diff_id is not None:
            try:
                Graph.driver().remove(self.diff_id)
            except NodeInUseException:
                raise LayerInUseException('Layer (%s) is in use, can not remove' % self.id)
            self.diff_id = None

    def remove(self):
        self.remove_diff()
        if self.id is not None:
            layer_file_path = pathlib.Path(oci_config['global']['path'], 
                'layers', self.id)
            rm(layer_file_path)
            self.id = None   

    def is_parent(self):
        return Graph.driver().is_parent(self.diff_id)
