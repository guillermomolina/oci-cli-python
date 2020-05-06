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
from opencontainers.image.v1 import Index, ImageLayout
from solaris_oci.oci import oci_config, OCIError
from solaris_oci.util import id_to_digest
from solaris_oci.util.file import rm
from .image import Image

class Repository():
    def __init__(self, name):
        self.name = name
        self.index = None
        self.images = {}
        try:
            self.load()
        except:
            pass

    def load(self):
        repositories_path = pathlib.Path(oci_config['global']['path'], 'repositories')
        index_file_path = repositories_path.joinpath(self.name + '.json')
        self.index = Index.from_file(index_file_path)
        for manifest_descriptor in self.index.get('Manifests'):
            manifest_annotations = manifest_descriptor.get('Annotations')
            manifest_tag = manifest_annotations.get('org.opencontainers.image.ref.name', None)
            manifest_descriptor_digest = manifest_descriptor.get('Digest')
            manifest_id = manifest_descriptor_digest.encoded()
            image = Image(self.name, manifest_tag)
            image.load(manifest_id)
            if image is not None:
                self.images[image.tag] = image

    def save(self):
        if self.index is None:
            raise OCIError('Can not save repository (%s), it is not initialized' % self.name)
        repositories_path = pathlib.Path(oci_config['global']['path'], 'repositories')
        if not repositories_path.is_dir():
            repositories_path.mkdir(parents=True)
        index_file_path = repositories_path.joinpath(self.name + '.json')
        self.index.save(index_file_path)
        oci_layout_file_path = repositories_path.joinpath('oci-layout')
        if not oci_layout_file_path.is_file():
            oci_layout = ImageLayout(version='1.0.0')
            oci_layout.save(oci_layout_file_path)

    def remove(self):
        if len(self.images) != 0:
            raise OCIError('There are (%d) images in the repository (%s), can not remove' 
                % (len(self.images), self.name))
        self.images = None
        self.index = None
        repositories_path = pathlib.Path(oci_config['global']['path'], 'repositories')
        index_file_path = repositories_path.joinpath(self.name + '.json')
        rm(index_file_path)

    def get_image(self, tag):
        try:
            return self.images[tag]
        except:
            raise OCIError('Image (%s) does not exist in this repository' % tag)

    def create_image(self, tag, rootfs_tar_path, config_json):
        image = self.images.get(tag, None)
        if image is not None:
            raise OCIError('Image tag (%s) already exist' % tag)
        image = Image(self.name, tag)
        manifest_descriptor = image.create(rootfs_tar_path, config_json)
        self.images[tag] = image
        if self.index is None:
            self.index = Index(
                manifests=[manifest_descriptor]
            )
        else: 
            manifests = self.index.get('Manifests')
            manifests.append(manifest_descriptor)
        self.save()
        return image        

    def remove_image(self, tag):
        image = self.get_image(tag)
        manifest_digest = id_to_digest(image.id)
        image.remove()
        del self.images[tag]
        if self.index is None:
            raise OCIError('Can not remove image from repository (%s)' % self.name)
        manifests = self.index.get('Manifests')
        for index, manifest_descriptor in enumerate(manifests):
            if manifest_descriptor.get('Digest') == manifest_digest:
                manifests.pop(index)
                break
        if len(manifests) == 0:
            self.remove()
            return
        self.save()
