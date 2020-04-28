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
from opencontainers.distribution.v1 import TagList
from solaris_oci import oci
from solaris_oci.util.file import rm
from . import Image

class Repository():
    def __init__(self, name):
        self.name = name
        self.images = None
        images_path = pathlib.Path(oci.config['images']['path'])
        self.path = images_path.joinpath(self.name)
        self.registry_file_path = self.path.joinpath('repository.json')
        if self.registry_file_path.is_file():
            self.load()
        else:
            self.create()

    def load(self):
        tag_list = TagList.from_file(self.registry_file_path)
        self.images = {}
        for tag_name in tag_list.get('Tags'):
            image = Image(self.name, tag_name)
            image.load()
            self.images[tag_name] = image

    def create(self):
        self.images = {}
        self.save()

    def save(self):
        if not self.path.is_dir():
            self.path.mkdir(parents=True)
        tag_list_json = {
            'name': self.name,
            'tags': list(self.images.keys())
        }
        tag_list = TagList.from_json(tag_list_json)
        tag_list.save(self.registry_file_path)

    def create_image(self, tag_name, rootfs_tar_file, config_json):
        image = self.images.get(tag_name, None)
        if image is not None:
            raise Exception('Image (%s:%s) already exists, can not create'
                % (self.name, tag_name))
        image = Image(self.name, tag_name)
        self.images[tag_name] = image
        self.save()
        image.create(rootfs_tar_file, config_json)
        return image

    def destroy_image(self, tag_name):
        image = self.images.get(tag_name, None)
        if image is None:
            raise Exception('Image tagged (%s) does not exist' % tag_name)
        image.destroy()
        del self.images[tag_name]
        if len(self.images) == 0:
            rm(self.registry_file_path)
            rm(self.path)
            return None
        else:
            self.save()
        return self
