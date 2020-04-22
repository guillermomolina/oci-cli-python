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
from datetime import datetime 
from opencontainers.image.v1 import ImageConfig, Descriptor, Index, \
    RootFS, History, Manifest, ImageLayout as Layout, Image as Config
from opencontainers.image.v1 import MediaTypeImageLayerNonDistributableGzip, \
    MediaTypeImageConfig, MediaTypeImageManifest
from solaris_oci.util.file import gzip, sha256sum

class Image():
    def __init__(self, repository, tag):
        self.repository = repository
        self.tag = tag
        self.id = None
        self.layout = None
        self.index = None
        self.manifests = None

    def load_config(self, blobs_path, config_descriptor):
        config_descriptor_digest = config_descriptor.get('Digest')
        config_json_path = blobs_path.joinpath(config_descriptor_digest.replace(':', '/'))
        with config_json_path.open() as config_json_file:
            config_json = json.load(config_json_file)
            config = Config()
            config.load(config_json)
            return config

    def load_manifest(self, blobs_path, manifest_descriptor):
        manifest_descriptor_digest = manifest_descriptor.get('Digest')
        manifest_json_path = blobs_path.joinpath(manifest_descriptor_digest.replace(':', '/'))
        with manifest_json_path.open() as manifest_json_file:
            manifest_json = json.load(manifest_json_file)
            manifest = Manifest()
            manifest.load(manifest_json)
            config_descriptor = manifest.get('Config')
            config = self.load_config(blobs_path, config_descriptor)
            return {
                'manifest': manifest,
                'config': config
            }

    def load_layout(self, tag_path):
        layout_json_path = tag_path.joinpath('oci-layout')
        with layout_json_path.open() as layout_json_file:
            layout_json = json.load(layout_json_file)
            self.layout = Layout()
            self.layout.load(layout_json)

    def load(self, distribution_path):
        tag_path = distribution_path.joinpath(self.repository, self.tag)
        self.load_layout(tag_path)
        tag_sha256 = tag_path.resolve().name
        self.id = 'sha256:' + tag_sha256
        blobs_path = tag_path.joinpath('blobs')
        index_json_path = tag_path.joinpath('index.json')
        with index_json_path.open() as index_json_file:
            index_json = json.load(index_json_file)
            self.index = Index()
            self.index.load(index_json)
            self.manifests = [
                self.load_manifest(blobs_path, manifest_descriptor)
                    for manifest_descriptor in self.index.get('Manifests')
            ]

    def save_layer(self, blobs_sha256_path, layer_tar_path):
        layer_tgz_path = blobs_sha256_path.joinpath('layer.tgz')
        if gzip(layer_tar_path, layer_tgz_path) != 0:
            raise Exception('could not compress layer file (%s) to %s' 
                % (str(layer_tar_path), str(layer_tgz_path)))
        layer_tgz_sha256 = sha256sum(layer_tgz_path)
        if layer_tgz_sha256 is None:
            raise Exception('could not get hash of file %s' % str(layer_tgz_sha256))
        blobs_sha256_layer_tgz_path = blobs_sha256_path.joinpath(layer_tgz_sha256)
        layer_tgz_path.rename(blobs_sha256_layer_tgz_path)
        layer_descriptor = Descriptor(
            digest='sha256:' + layer_tgz_sha256,
            size=blobs_sha256_layer_tgz_path.stat().st_size,
            media_type=MediaTypeImageLayerNonDistributableGzip,
        )
        return layer_descriptor
    
    def create_config(self, layer_tar_path, config_json):
        layer_tar_sha256 = sha256sum(layer_tar_path)
        if layer_tar_sha256 is None:
            raise Exception('could not get hash of file %s' % str(layer_tar_path))
        process = config_json.get('process', {})
        cmd = process.get('args', [ '/bin/sh' ])
        image_config = ImageConfig(
            #user=None,
            #ports=None,
            env=process.get('env', [ 'PATH=/usr/sbin:/usr/bin:/sbin:/bin' ]),
            #entrypoint=None,
            cmd=cmd,
            #volumes=None,
            working_dir=process.get('cwd', '/')
        )
        rootfs = RootFS(
            rootfs_type='layers', 
            diff_ids=['sha256:' + layer_tar_sha256]
        )
        history = [
            History(
                created=datetime.now(), 
                created_by='/bin/sh -c #(nop) ADD file:%s in / ' % layer_tar_sha256
            ),
            History(
                created=datetime.now(), 
                created_by='/bin/sh -c #(nop)  CMD [\"%s\"]' % cmd, 
                empty_layer=True
            )
        ]
        platform = config_json.get('platform', {})
        config = Config(
            created=datetime.now(),
            architecture=platform.get('arch', 'sparc64'),
            os=platform.get('os', 'SunOS'),
            config=image_config,
            rootfs=rootfs,
            history=history
        )
        return config
    
    def save_config(self, blobs_sha256_path, config):
        config_json_path = blobs_sha256_path.joinpath('config.json')
        config.save(config_json_path)
        config_json_sha256 = sha256sum(config_json_path)
        if config_json_sha256 is None:
            raise Exception('could not get hash of file %s' % str(config_json_path))
        blobs_sha256_config_json_path = blobs_sha256_path.joinpath(config_json_sha256)
        config_json_path.rename(blobs_sha256_config_json_path)
        config_descriptor = Descriptor(
            digest='sha256:' + config_json_sha256,
            size=blobs_sha256_config_json_path.stat().st_size,
            media_type=MediaTypeImageConfig,
        )
        return config_descriptor

    def create_manifest(self, blobs_sha256_path, layer_tar_path, config_json):
        config = self.create_config(layer_tar_path, config_json)
        config_descriptor = self.save_config(blobs_sha256_path, config)
        layer_descriptor = self.save_layer(blobs_sha256_path, layer_tar_path)
        manifest = Manifest(
            config=config_descriptor,
            layers=[layer_descriptor]
        )
        return manifest
    
    def save_manifest(self, blobs_sha256_path, manifest):
        manifest_json_path = blobs_sha256_path.joinpath('manifest.json')
        manifest.save(manifest_json_path)
        manifest_json_sha256 = sha256sum(manifest_json_path)
        if manifest_json_sha256 is None:
            raise Exception('could not get hash of file %s' % str(manifest_json_path))
        blobs_sha256_manifest_json_path = blobs_sha256_path.joinpath(manifest_json_sha256)
        manifest_json_path.rename(blobs_sha256_manifest_json_path)
        manifest_descriptor = Descriptor(
            digest='sha256:' + manifest_json_sha256,
            size=blobs_sha256_manifest_json_path.stat().st_size,
            media_type=MediaTypeImageManifest,
        )
        return manifest_descriptor

    def create_index(self, tag_path, layer_tar_path, config_json):
        blobs_sha256_path = tag_path.joinpath('blobs', 'sha256')
        blobs_sha256_path.mkdir(parents=True)
        manifest = self.create_manifest(blobs_sha256_path, layer_tar_path, config_json)
        manifest_descriptor = self.save_manifest(blobs_sha256_path, manifest)
        self.index = Index(
            manifests=[manifest_descriptor]
        )
    
    def save_index(self, tag_path):
        index_json_path = tag_path.joinpath('index.json')
        self.index.save(index_json_path)
        return sha256sum(index_json_path)

    def create_layout(self):
        self.layout = Layout(version='1.0.0')

    def save_layout(self, tag_path):
        layout_json_path = tag_path.joinpath('oci-layout')
        self.layout.save(layout_json_path)

    def create(self, distribution_path, layer_tar_path, config_json):
        tag_path = distribution_path.joinpath(self.repository, self.tag)
        if tag_path.exists():
            date_string = datetime.now().strftime("_%Y%m%d%H%M%S")
            backup_path = tag_path.parent.joinpath(tag_path.name + date_string)
            tag_path.rename(backup_path)
        tag_path.mkdir(parents=True)
        self.create_layout()
        self.save_layout(tag_path)
        self.create_index(tag_path, layer_tar_path, config_json)
        index_json_sha256 = self.save_index(tag_path)
        tag_sha256_path = distribution_path.joinpath(self.repository, index_json_sha256)
        tag_path.rename(tag_sha256_path)
        tag_path.symlink_to(index_json_sha256)
        




