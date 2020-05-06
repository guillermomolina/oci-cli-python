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
import hashlib
from datetime import datetime 
from opencontainers.image.v1 import ImageConfig, Descriptor, \
    RootFS, History, Manifest, Image as Config, MediaTypeImageConfig, \
    MediaTypeImageManifest
from solaris_oci.oci import oci_config, OCIError
from solaris_oci.util import digest_to_id, id_to_digest
from solaris_oci.util.file import rm
from .layer import Layer
from .exceptions import ImageInUseException

class Image():
    def __init__(self, repository, tag):
        self.repository = repository
        self.tag = tag
        self.manifest_id = None
        self.manifest = None
        self.layers = None
        self.history = None
        self.config = None

    @property
    def id(self):
        return self.manifest_id

    @property
    def name(self):
        return '%s:%s' % (self.repository, self.tag)

    @property
    def size(self):
        if self.layers is not None and len(self.layers) != 0:
            return sum([layer.size for layer in self.layers])
        return None

    @property
    def digest(self):
        # not "id_to_digest(self.id)", compatible with "docker image ls --digests"
        if self.layers is not None and len(self.layers) != 0:
            return self.layers[-1].diff_digest
        return None

    def top_layer(self):
        if self.layers is not None:
            return self.layers[-1]
        return None

    def load(self, manifest_id):
        manifest_file_path = pathlib.Path(oci_config['global']['path'], 'manifests', manifest_id)
        self.manifest = Manifest.from_file(manifest_file_path)
        self.load_config()
        self.manifest_id = manifest_id

    def load_config(self):
        if self.manifest is None:
            raise OCIError('Image (%s) has no manifest' % self.name)
        config_descriptor = self.manifest.get('Config')
        config_descriptor_digest = config_descriptor.get('Digest')
        config_id = config_descriptor_digest.encoded()
        config_file_path = pathlib.Path(oci_config['global']['path'], 'configs', config_id)
        self.config = Config.from_file(config_file_path)
        self.load_layers()

    def load_layers(self):
        if self.config is None:
            raise OCIError('Image (%s) has no config' % self.name)
        if self.manifest is None:
            raise OCIError('Image (%s) has no manifest' % self.name)
        root_fs = self.config.get('RootFS')
        diff_ids = [
            digest_to_id(diff_digest)
                for diff_digest in root_fs.get('DiffIDs')
        ]
        layer_ids = [
            digest_to_id(layer_descriptor.get('Digest'))
                for layer_descriptor in self.manifest.get('Layers')
        ]
        self.layers = [
            Layer(diff_id, layer_id) 
                for diff_id, layer_id in zip(diff_ids, layer_ids) 
        ]

    def create(self, rootfs_tar_path, config_file):
        if self.manifest is not None:
            raise OCIError('Image (%s) already exists' % self.name)
        manifest_descriptor = self.create_manifest(rootfs_tar_path, config_file)
        return manifest_descriptor

    def create_manifest(self, rootfs_tar_path, config_file):
        layer_descriptor = self.create_layer(rootfs_tar_path)
        config_descriptor = self.create_config(config_file)
        self.manifest = Manifest(
            config=config_descriptor,
            layers=[layer_descriptor]
        )
        manifest_json = self.manifest.to_json(compact=True).encode()
        manifest_id = hashlib.sha256(manifest_json).hexdigest()
        manifests_path = pathlib.Path(oci_config['global']['path'], 'manifests')
        if not manifests_path.is_dir():
            manifests_path.mkdir(parents=True)
        manifest_file_path = manifests_path.joinpath(manifest_id)
        manifest_file_path.write_bytes(manifest_json)
        self.manifest_id = manifest_id
        manifest_descriptor = Descriptor(
            digest=id_to_digest(manifest_id),
            size=len(manifest_json),
            media_type=MediaTypeImageManifest,
            annotations={ 'org.opencontainers.image.ref.name': self.tag }
        )
        return manifest_descriptor

    def create_layer(self, rootfs_tar_path):
        layer = Layer()
        layer.create_diff()
        self.create_history('/bin/sh -c #(nop) ADD file:%s in / ' % str(rootfs_tar_path))
        layer.add_file_to_diff(rootfs_tar_path)
        layer_descriptor = layer.commit_diff()
        if self.layers is None:
            self.layers = [layer]
        else: 
            self.layers.append(layer)
        return layer_descriptor

    def create_history(self, command, empty_layer=None):
        history = History(
            created=datetime.utcnow(), 
            created_by=command,
            empty_layer=empty_layer
        )
        if self.history is None:
            self.history = [history]
        else:
            self.history.append(history)
        return history

    def create_root_fs(self):
        diff_ids = [layer.diff_digest for layer in self.layers]
        root_fs = RootFS(
            rootfs_type='layers', 
            diff_ids=diff_ids
        )
        return root_fs

    def create_config(self, config_json):        
        process = config_json.get('process', {})
        command = process.get('args', [ '/bin/sh' ])
        self.create_history('/bin/sh -c #(nop)  CMD ["%s"]' % ' '.join(command), empty_layer=True)
        image_config = ImageConfig(
            #user=None,
            #ports=None,
            env=process.get('env', [ 'PATH=/usr/sbin:/usr/bin:/sbin:/bin' ]),
            #entrypoint=None,
            cmd=command,
            #volumes=None,
            working_dir=process.get('cwd', '/')
        )
        platform = config_json.get('platform', {})
        root_fs = self.create_root_fs()
        self.config = Config(
            created=datetime.utcnow(),
            architecture=platform.get('arch', 'sparc64'),
            os=platform.get('os', 'SunOS'),
            config=image_config,
            rootfs=root_fs,
            history=self.history
        )
        config_json = self.config.to_json(compact=True).encode()
        config_id = hashlib.sha256(config_json).hexdigest()
        configs_path = pathlib.Path(oci_config['global']['path'], 'configs')
        if not configs_path.is_dir():
            configs_path.mkdir(parents=True)
        config_file_path = configs_path.joinpath(config_id)
        config_file_path.write_bytes(config_json)
        config_descriptor = Descriptor(
            digest=id_to_digest(config_id),
            size=len(config_json),
            media_type=MediaTypeImageConfig
        )
        return config_descriptor

    def remove(self):
        if self.id is None:
            raise OCIError('Can not remove image (%s)' % self.name)
        if self.top_layer().is_parent():
            raise ImageInUseException()
        self.remove_manifest()
        self.manifest_id = None

    def remove_manifest(self):
        if self.manifest is None:
            raise OCIError('Image (%s) has no manifest' % self.name)
        if self.manifest_id is None:
            raise OCIError('Image (%s) has no manifest id' % self.name)
        self.remove_layers()
        self.remove_config()
        manifests_path = pathlib.Path(oci_config['global']['path'], 'manifests')
        manifest_file_path = manifests_path.joinpath(self.manifest_id)
        rm(manifest_file_path)
        self.history = None
        self.manifest = None

    def remove_layers(self):
        if self.layers is None:
            raise OCIError('Image (%s) has no layers' % self.name)
        for layer in reversed(self.layers):
            try:
                layer.remove()
            except:
                # Do not delete if it has children from another image
                pass
        self.layers = None

    def remove_config(self):
        if self.config is None:
            raise OCIError('Image (%s) has no config' % self.name)
        config_descriptor = self.manifest.get('Config')
        config_id = digest_to_id(config_descriptor.get('Digest'))
        configs_path = pathlib.Path(oci_config['global']['path'], 'configs')
        config_file_path = configs_path.joinpath(config_id)
        rm(config_file_path)
        self.config = None
