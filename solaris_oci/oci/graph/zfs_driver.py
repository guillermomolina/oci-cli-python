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

'''
    Driver:
        root_zfs = rpool/oci
        layers_path = /var/lib/oci/layers
    Layer:
        _id -> sha256 hash
        image_zfs = $root_zfs/$image_id (not mounted)
        layer_zfs = $image_zfs/$layer_id (if parent, clone of 
            $parent_layer_zfs@parent_layer_id)
        layer_path = $layers_path/$layer_id
        layer_snapshot = $root_zfs@$layer_id (recursive)

    Create driver root zfs:
        zfs create -o mountpoint=none -o compression=lz4 $root_zfs

    Create image zfs:
        zfs create -o mountpoint=none $image_zfs

    Create base layer:
        zfs create -o mountpoint=$layer_path $layer_zfs

    Create child layer:
        zfs clone -o mountpoint=$layer_path $parent_layer_zfs@parent_layer_id \
            $layer_zfs
    
    Create layer from snapshot (in order, parent layer before child layer):
        zfs receive -v $image_zfs < $layer_zfs_file

    Commit layer:
        zfs set readonly=on $layer_zfs
        zfs snapshot -r $layer_snapshot
    
    Save base layer:
        zfs send -R $layer_snapshot > $zfs_file
    
    Save child layer:
        zfs send -R -I $parent_layer_zfs@parent_layer_id \
            $layer_snapshot > $layer_zfs_file

    Remove layer (in order, child layer before parent layer):
        zfs destroy -r $layer_snapshot
        zfs destroy $layer_zfs
        rmdir $layer_path

    Remove image zfs (should be empty):
        zfs destroy $image_zfs

'''

import pathlib
from solaris_oci import oci
from solaris_oci.util import generate_random_sha256
from solaris_oci.util.zfs import zfs_create, zfs_get, zfs_set, zfs_snapshot, \
    zfs_send, zfs_destroy
from solaris_oci.util.file import tar, du, rm
from .driver import Driver

class ZfsDriver(Driver):
    def __init__(self):
        super().__init__()
        self.root_zfs = oci.config['graph']['zfs']['filesystem']
        layers_path = pathlib.Path(oci.config['layers']['path'])
        self.layers_sha256_path = layers_path.joinpath('sha256')

    def create_layer(self, image_id, parent_layer_id=None):
        if parent_layer_id is None:
            # This is the first layer, create the base zfs first:
            image_zfs = zfs_create(image_id, parent=self.root_zfs, mountpoint='none')
            if image_zfs is None:
                raise Exception('Could not create base zfs (%s/%s)' % (self.root_zfs, image_id) )
        else:
            image_zfs = self.root_zfs + '/' + image_id
            if zfs_get(image_zfs, 'type') != 'filesystem':
                raise Exception('Base zfs (%s/%s) does not exist' % (self.root_zfs, image_id) )
        layer_id = generate_random_sha256()
        layer_path = self.layers_sha256_path.joinpath(layer_id)
        layer_zfs = zfs_create(layer_id, parent=image_zfs, mountpoint=layer_path)
        if layer_zfs is None:
            raise Exception('Could not create layer zfs (%s/%s)' % (image_zfs, layer_id) )
        return layer_id

    def commit_layer(self, image_id, layer_id):
        image_zfs = self.root_zfs + '/' + image_id
        layer_zfs = image_zfs + '/' + layer_id
        if zfs_get(layer_zfs, 'type') != 'filesystem':
            raise Exception('Layer zfs (%s) does not exist' % layer_zfs)
        zfs_set(layer_zfs, readonly=True)
        layer_snapshot = zfs_snapshot(layer_id, image_zfs, recursive=True)
        return layer_snapshot

    def get_parent_layer_id(self, image_id, layer_id):
        image_zfs = self.root_zfs + '/' + image_id
        layer_zfs = image_zfs + '/' + layer_id
        parent_zfs = zfs_get(layer_zfs, 'origin')
        if parent_zfs is None:
            return None
        if parent_zfs.startswith(image_zfs):
            # TODO: more checks
            return parent_zfs.split('/')[-1]
        raise Exception('Layer zfs (%s) has incorrect parent (%s)' % 
            (layer_zfs, parent_zfs))

    def save_layer(self, image_id, layer_id, file_path):
        image_zfs = self.root_zfs + '/' + image_id
        layer_snapshot = image_zfs + '@' + layer_id
        if zfs_get(layer_snapshot, 'type') != 'snapshot':
            raise Exception('Layer snapshot (%s) does not exist' % layer_snapshot)
        layer_path = self.layers_sha256_path.joinpath(layer_id)
        parent_layer_id = self.get_parent_layer_id(image_id, layer_id)
        if file_path.suffix == '.tar':
            if parent_layer_id is None:
                if tar(layer_path, file_path) != 0:
                    raise Exception('could not create tar file (%s) from (%s)'
                        % (str(file_path), str(layer_path)))
            else:
                raise NotImplementedError()
        elif file_path.suffix == '.zfs':
            if parent_layer_id is None:
                zfs_send(layer_snapshot, file_path, recursive=True)
            else:
                parent_layer_zfs = self.root_zfs + '/' + parent_layer_id
                parent_layer_snapshot = parent_layer_zfs + '@' + parent_layer_id
                zfs_send(layer_snapshot, file_path, 
                    first_snapshot=parent_layer_snapshot, recursive=True)
        else:
            raise NotImplementedError()

    def destroy_layer(self, image_id, layer_id, parent_layer_id=None):
        image_zfs = self.root_zfs + '/' + image_id
        layer_snapshot = image_zfs + '@' + layer_id
        if zfs_destroy(layer_snapshot, recursive=True) != 0:
            print('WARNING: Could not destroy snapshot (%s)' % layer_snapshot)
        layer_zfs = image_zfs + '/' + layer_id
        if zfs_destroy(layer_zfs) != 0:
            print('WARNING: Could not destroy layer zfs (%s)' % layer_zfs)
        layer_path = self.layers_sha256_path.joinpath(layer_id)
        rm(layer_path)
        if parent_layer_id is None:
            if zfs_destroy(image_zfs) != 0:
                print('WARNING: Could not destroy image zfs (%s)' % image_zfs)

    def get_layer_size(self, image_id, layer_id):
        image_zfs = self.root_zfs + '/' + image_id
        layer_zfs = image_zfs + '/' + layer_id
        layer_path = self.layers_sha256_path.joinpath(layer_id)
        return du(layer_path)

    def get_layer_zfs_size(self, image_id, layer_id):
        # compressed and/or deduplicated size is smaller than actuall size
        image_zfs = self.root_zfs + '/' + image_id
        layer_zfs = image_zfs + '/' + layer_id
        return zfs_get(layer_zfs, 'used')
