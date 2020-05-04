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
        driver_path = /var/lib/oci/diffs
    Layer:
        _id -> sha256 hash
        base_zfs = $root_zfs/$base_id (not mounted)
        node_zfs = $base_zfs/$node_id (if parent, clone of 
            $parent_zfs@parent_id)
        node_path = $driver_path/$node_id
        node_snapshot = $root_zfs@$node_id (recursive)

    Create driver root zfs:
        zfs create -o mountpoint=none -o compression=lz4 $root_zfs

    Create image zfs:
        zfs create -o mountpoint=none $base_zfs

    Create base diff:
        zfs create -o mountpoint=$node_path $node_zfs

    Create child diff:
        zfs clone -o mountpoint=$node_path $parent_zfs@parent_id \
            $node_zfs
    
    Create diff from snapshot (in order, parent diff before child diff):
        zfs receive -v $base_zfs < $node_zfs_file

    Commit diff:
        zfs set readonly=on $node_zfs
        zfs snapshot -r $node_snapshot
    
    Save base diff:
        zfs send -R $node_snapshot > $zfs_file
    
    Save child diff:
        zfs send -R -I $parent_zfs@parent_id \
            $node_snapshot > $node_zfs_file

    Remove diff (in order, child diff before parent diff):
        zfs destroy -r $node_snapshot
        zfs destroy $node_zfs
        rmdir $node_path

    Remove image zfs (should be empty):
        zfs destroy $base_zfs

'''

import pathlib
from solaris_oci import oci
from solaris_oci.util import generate_random_sha256
from solaris_oci.util.zfs import zfs_create, zfs_get, zfs_set, zfs_snapshot, \
    zfs_send, zfs_destroy, zfs_is_snapshot, zfs_is_filesystem, zfs_list
from solaris_oci.util.file import tar, du, rm, untar
from .driver import Driver

def id_from_zfs(filesystem):
    if filesystem is not None:
        splitted = filesystem.split('/')[-1]
        if len(splitted) >= 2:
            return splitted[-1]
    return None

class ZfsDriver(Driver):
    def __init__(self):
        super().__init__()
        self.filesystems = {}
        self.driver_path = pathlib.Path(oci.config['global']['path'], 'zfs')
        if not self.driver_path.is_dir():
            self.driver_path.mkdir(parents=True)
        self.root_zfs = oci.config['graph']['zfs']['filesystem']
        if not zfs_is_filesystem(self.root_zfs):         
            self.root_zfs = zfs_create(self.root_zfs, mountpoint=self.driver_path)
            if self.root_zfs is None:
                raise Exception('Could not create root zfs (%s)' % root_zfs)   
        self.load()
    
    def load(self):
        zfs_filesystems = zfs_list(self.root_zfs, recursive=True,
            properties=['name', 'origin', 'mountpoint'])
        self.filesystems = {}
        root_zfs_sections = self.root_zfs.split('/')
        base_zfs_section_number = len(root_zfs_sections)
        node_zfs_section_number = base_zfs_section_number + 1
        base_filesystems = set()
        for zfs in zfs_filesystems:
            if zfs['name'] == self.root_zfs:
                # Discard root zfs
                continue
            node_zfs = zfs['name']
            zfs_sections = node_zfs.split('/')
            if len(zfs_sections) == node_zfs_section_number:
                # base zfs, go on
                continue
            base_zfs = '/'.join(zfs_sections[:-1])
            base_filesystems.add(base_zfs)
            node_id = zfs_sections[node_zfs_section_number]
            parent_zfs = zfs['origin']
            parent = None
            if parent_zfs is not None:
                parent_id = id_from_zfs(parent_zfs)
                parent = self.filesystems(parent_id)
            node_path = zfs['mountpoint']
            node_size = None
            if node_path is not None:
                node_size = du(node_path)
            zfs_node = self.filesystems.setdefault(node_id, {
                'zfs': node_zfs,
                'id': node_id,
                'path': node_path,
                'size': node_size,
                'snapshot': None,
                'base_zfs': base_zfs,
                'parent_zfs': parent_zfs,
                'parent': parent
            })
        for base_zfs in base_filesystems:
            zfs_snapshots = zfs_list(base_zfs, recursive=True, 
                zfs_type='snapshot', properties=['name'])
            for zfs_snapshot in zfs_snapshots:
                zfs_snapshot_name = zfs_snapshot['name']
                zfs_sections = zfs_snapshot_name.split('@')
                if zfs_sections[0] == base_zfs:
                    node_id = zfs_sections[1]
                    zfs_node = self.filesystems[node_id]
                    zfs_node['snapshot'] = zfs_snapshot_name

    def path(self, node_id):
        return self.filesystems[node_id]['path']

    def size(self, node_id):
        return self.filesystems[node_id]['size']

    def zfs_size(self, node_id):
        # compressed and/or deduplicated size is smaller than actuall size
        node = self.filesystems[node_id]
        return zfs_get(node['zfs'], 'used')

    def create(self, parent_id=None):
        node_id = generate_random_sha256()
        if parent_id is None:
            parent = None
            parent_zfs = None
            base_id = node_id
            # This is the first diff, create the base zfs first:
            base_zfs = zfs_create(base_id, parent=self.root_zfs, mountpoint='none')
            if base_zfs is None:
                raise Exception('Could not create base zfs (%s/%s)' % (self.root_zfs, base_id))
            node_path = self.driver_path.joinpath(node_id)
            node_zize = 0
            node_zfs = zfs_create(node_id, parent=base_zfs, mountpoint=node_path)
        else:
            # clone parent
            NotImplementedError()
        if node_zfs is None:
            raise Exception('Could not create diff zfs (%s/%s)' % (base_zfs, node_id) )
        self.filesystems[node_id] = {
            'zfs': node_zfs,
            'id': node_id,
            'path': node_path,
            'size': node_zize,
            'snapshot': None,
            'base_zfs': base_zfs,
            'parent': parent
        }
        return node_id

    def commit(self, node_id):
        node = self.filesystems[node_id]
        base_zfs = node['base_zfs']
        node_zfs = node['zfs']
        if not zfs_is_filesystem(node_zfs):
            raise Exception('Layer zfs (%s) does not exist' % node_zfs)
        zfs_set(node_zfs, readonly=True)
        node_snapshot = zfs_snapshot(node_id, base_zfs, recursive=True)
        node['snapshot'] = node_snapshot
        return node_snapshot

    def children(self, node_id):
        return [
            node for node in self.filesystems.values() 
                if node['parent'] is not None and \
                    self.filesystems(node['parent']) == node
        ]

    def save(self, node_id, file_path):
        node = self.filesystems[node_id]
        node_snapshot = node['snapshot']
        if not zfs_is_snapshot(node_snapshot):
            raise Exception('Layer snapshot (%s) does not exist' % node_snapshot)
        node_path = node['path']
        if file_path.suffix == '.tar':
            parent = node['parent']
            if parent is None:
                if tar(node_path, file_path) != 0:
                    raise Exception('could not create tar file (%s) from (%s)'
                        % (str(file_path), str(node_path)))
            else:
                raise NotImplementedError()
        elif file_path.suffix == '.zfs':
            parent = node['parent']
            if parent is None:
                zfs_send(node_snapshot, file_path, recursive=True)
            else:
                parent_snapshot = parent['snapshot']
                zfs_send(node_snapshot, file_path, 
                    first_snapshot=parent_snapshot, recursive=True)
        else:
            raise NotImplementedError()

    def remove(self, node_id):
        if len(self.children(node_id)) != 0:
            raise Exception('Can not remove diff id (%s), it has children' % node_id)
        node = self.filesystems.pop(node_id)
        node_snapshot = node['snapshot']
        if zfs_destroy(node_snapshot, recursive=True) != 0:
            raise Exception('Could not destroy snapshot (%s)' % node_snapshot)
        node_zfs = node['zfs']
        if zfs_destroy(node_zfs) != 0:
            raise Exception('Could not destroy diff zfs (%s)' % node_zfs)
        node_path = node['path']
        rm(node_path)
        node_parent = node['parent']
        if node_parent is None: # remove base zfs
            base_zfs = node['base_zfs']
            if zfs_destroy(base_zfs) != 0:
                raise Exception('Could not destroy image zfs (%s)' % base_zfs)

    def add_file(self, node_id, file_path, destination_path=None):
        node = self.filesystems[node_id]
        local_destination_path = node['path']
        if destination_path is not None:
            local_destination_path = local_destination_path.joinpath(destination_path).resolve()
        if file_path.suffix == '.tar':
            untar(file_path, local_destination_path)
        else:
            raise NotImplementedError()
        node['size'] = du(node['path'])
