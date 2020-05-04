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
import shutil
from datetime import datetime 
from opencontainers.image.v1 import ImageConfig, Descriptor, Index, \
    RootFS, History, Manifest, ImageLayout as Layout, Image as Config
from opencontainers.image.v1 import MediaTypeImageLayerNonDistributableGzip, \
    MediaTypeImageLayerNonDistributableZfsXZ, MediaTypeImageConfig, \
    MediaTypeImageManifest
from solaris_oci import oci
from solaris_oci.util import generate_random_sha256
from solaris_oci.util.file import compress, sha256sum, rm
from .layer import Layer

class ImageSave():
    def __init__(self, repository, tag):
        self.repository = repository
        self.tag = tag
        self.id = None
        self.layout = None
        self.digest = None
        self.index = None
        self.manifests = None
        self.layers = None
        self.history = None
        self.size = None
        images_path = pathlib.Path(oci.config['images']['path'])
        self.repository_path = images_path.joinpath(self.repository)
        self.tag_path = self.repository_path.joinpath(self.tag)
        self.blobs_sha256_path = self.tag_path.joinpath('blobs', 'sha256')

    def load_config(self, config_descriptor):
        config_descriptor_digest = config_descriptor.get('Digest')
        config_json_path = self.blobs_sha256_path.joinpath(config_descriptor_digest.encoded())
        config = Config.from_file(config_json_path)
        rootfs_diff_ids = config.get('RootFS').get('DiffIDs')
        self.layers = [ Layer(self.id, layer_digest) for layer_digest in rootfs_diff_ids ]
        self.digest = self.layers[-1].digest
        self.size = sum([layer.size for layer in self.layers])
        return config

    def load_manifest(self, manifest_descriptor):
        manifest_descriptor_digest = manifest_descriptor.get('Digest')
        manifest_json_path = self.blobs_sha256_path.joinpath(manifest_descriptor_digest.encoded())
        manifest = Manifest.from_file(manifest_json_path)
        config_descriptor = manifest.get('Config')
        config = self.load_config(config_descriptor)
        return {
            'manifest': manifest,
            'config': config
        }

    def load_layout(self):
        layout_json_path = self.tag_path.joinpath('oci-layout')
        return Layout.from_file(layout_json_path)

    def load_index(self):
        index_json_path = self.tag_path.joinpath('index.json')
        return Index.from_file(index_json_path)

    def load(self):
        self.layout = self.load_layout()
        self.index = self.load_index()
        self.id = self.tag_path.resolve().name
        self.manifests = [
            self.load_manifest(manifest_descriptor)
                for manifest_descriptor in self.index.get('Manifests')
        ]
 
    def create_layer(self, parent_layer=None):
        layer = Layer(self.id, parent_layer)
        layer.create()
        return layer

    def command_add(self, layer, file_path):
        layer.add(file_path)
        history_item = History(
            created=datetime.utcnow(), 
            created_by='/bin/sh -c #(nop) ADD file:%s in / ' % str(file_path)
        )
        self.history.append(history_item)

    def command_cmd(self, command):
        history_item = History(
            created=datetime.utcnow(), 
            created_by='/bin/sh -c #(nop)  CMD ["%s"]' % ' '.join(command), 
            empty_layer=True
        )
        self.history.append(history_item)

    def create_base_layer(self, rootfs_tar_file):
        self.history = []
        layer = self.create_layer()
        self.command_add(layer, rootfs_tar_file)
        self.layers = [layer]
        self.digest = layer.digest
        return layer

    def save_layer_as_tar(self, layer):
        layer_tar_path = self.blobs_sha256_path.joinpath('layer.tar')
        layer.commit()
        layer.create_archive(layer_tar_path)        
        layer_tar_gz_path = self.blobs_sha256_path.joinpath('layer.tar.gz')
        if compress(layer_tar_path, method='gz', parallel=True, 
                keep_original=False) != 0:
            raise Exception('could not compress layer file (%s) to %s' 
                % (str(layer_tar_path), str(layer_tar_gz_path)))
        layer_tar_gz_sha256 = sha256sum(layer_tar_gz_path)
        if layer_tar_gz_sha256 is None:
            raise Exception('could not get hash of file %s' % str(layer_tar_gz_sha256))
        blobs_sha256_layer_tar_gz_path = self.blobs_sha256_path.joinpath(layer_tar_gz_sha256)
        layer_tar_gz_path.rename(blobs_sha256_layer_tar_gz_path)
        layer_descriptor = Descriptor(
            digest='sha256:' + layer_tar_gz_sha256,
            size=blobs_sha256_layer_tar_gz_path.stat().st_size,
            media_type=MediaTypeImageLayerNonDistributableGzip,
        )
        return layer_descriptor
 
    def save_layer(self, layer):
        layer_zfs_path = self.blobs_sha256_path.joinpath('layer.zfs')
        layer.commit()
        layer.create_archive(layer_zfs_path)        
        layer_zfs_xz_path = self.blobs_sha256_path.joinpath('layer.zfs.xz')
        if compress(layer_zfs_path, method='xz', parallel=True, 
                keep_original=False) != 0:
            raise Exception('could not compress layer file (%s) to %s' 
                % (str(layer_zfs_path), str(layer_zfs_xz_path)))
        layer_zfs_xz_sha256 = sha256sum(layer_zfs_xz_path)
        if layer_zfs_xz_sha256 is None:
            raise Exception('could not get hash of file %s' % str(layer_zfs_xz_sha256))
        blobs_sha256_layer_zfs_xz_path = self.blobs_sha256_path.joinpath(layer_zfs_xz_sha256)
        layer_zfs_xz_path.rename(blobs_sha256_layer_zfs_xz_path)
        layer_descriptor = Descriptor(
            digest='sha256:' + layer_zfs_xz_sha256,
            size=blobs_sha256_layer_zfs_xz_path.stat().st_size,
            media_type=MediaTypeImageLayerNonDistributableZfsXZ,
        )
        return layer_descriptor
        
   
    def create_root_fs(self):
        diff_ids = [layer.digest for layer in self.layers]
        root_fs = RootFS(
            rootfs_type='layers', 
            diff_ids=diff_ids
        )
        return root_fs

    def create_config(self, layer, config_json):        
        process = config_json.get('process', {})
        command = process.get('args', [ '/bin/sh' ])
        self.command_cmd(command)
        image_config = ImageConfig(
            #user=None,
            #ports=None,
            env=process.get('env', [ 'PATH=/usr/sbin:/usr/bin:/sbin:/bin' ]),
            #entrypoint=None,
            cmd=command,
            #volumes=None,
            working_dir=process.get('cwd', '/')
        )
        history = self.history
        platform = config_json.get('platform', {})
        root_fs = self.create_root_fs()
        config = Config(
            created=datetime.utcnow(),
            architecture=platform.get('arch', 'sparc64'),
            os=platform.get('os', 'SunOS'),
            config=image_config,
            rootfs=root_fs,
            history=history
        )
        return config
    
    def save_config(self, config):
        config_json_path = self.blobs_sha256_path.joinpath('config.json')
        config.save(config_json_path)
        config_json_sha256 = sha256sum(config_json_path)
        if config_json_sha256 is None:
            raise Exception('could not get hash of file %s' % str(config_json_path))
        blobs_sha256_config_json_path = self.blobs_sha256_path.joinpath(config_json_sha256)
        config_json_path.rename(blobs_sha256_config_json_path)
        config_descriptor = Descriptor(
            digest='sha256:' + config_json_sha256,
            size=blobs_sha256_config_json_path.stat().st_size,
            media_type=MediaTypeImageConfig,
        )
        return config_descriptor

    def create_manifest(self, rootfs_tar_path, config_json):
        layer = self.create_base_layer(rootfs_tar_path)
        layer_descriptor = self.save_layer(layer)
        config = self.create_config(layer, config_json)
        config_descriptor = self.save_config(config)
        manifest = Manifest(
            config=config_descriptor,
            layers=[layer_descriptor]
        )
        return manifest
    
    def save_manifest(self, manifest):
        manifest_json_path = self.blobs_sha256_path.joinpath('manifest.json')
        manifest.save(manifest_json_path)
        manifest_json_sha256 = sha256sum(manifest_json_path)
        if manifest_json_sha256 is None:
            raise Exception('could not get hash of file %s' % str(manifest_json_path))
        blobs_sha256_manifest_json_path = self.blobs_sha256_path.joinpath(manifest_json_sha256)
        manifest_json_path.rename(blobs_sha256_manifest_json_path)
        manifest_descriptor = Descriptor(
            digest='sha256:' + manifest_json_sha256,
            size=blobs_sha256_manifest_json_path.stat().st_size,
            media_type=MediaTypeImageManifest,
        )
        return manifest_descriptor

    def create_index(self, rootfs_tar_path, config_json):
        manifest = self.create_manifest(rootfs_tar_path, config_json)
        manifest_descriptor = self.save_manifest(manifest)
        self.index = Index(
            manifests=[manifest_descriptor]
        )
    
    def save_index(self):
        index_json_path = self.tag_path.joinpath('index.json')
        self.index.save(index_json_path)
        tag_sha256 = sha256sum(index_json_path)
        return tag_sha256

    def create_layout(self):
        self.layout = Layout(version='1.0.0')

    def save_layout(self):
        layout_json_path = self.tag_path.joinpath('oci-layout')
        self.layout.save(layout_json_path)

    def create(self, rootfs_tar_path, config_json):
        if self.tag_path.exists():
            raise Exception('Image (%s:%s) already exist, remove it first' 
                % (self.repository, self.tag))
        self.id = generate_random_sha256()
        tag_sha256_path = self.repository_path.joinpath(self.id)
        tag_sha256_path.mkdir(parents=True)
        self.tag_path.symlink_to(self.id)
        self.blobs_sha256_path.mkdir(parents=True)
        self.create_layout()
        self.save_layout()
        self.create_index(rootfs_tar_path, config_json)
        index_json_sha256 = self.save_index()

    def remove(self):
        for layer in reversed(self.layers):
            layer.remove()
        rm(self.tag_path.resolve())
        rm(self.tag_path)


