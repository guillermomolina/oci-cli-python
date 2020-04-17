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

from .layer import Layer
from .image import Image
from .descriptor import Descriptor

class Manifest():
    def __init__(self, descriptor_json=None):
        self.descriptor = None
        self.image = None
        self.layers = None
        self.size = None
        if descriptor_json is not None:
            self.descriptor = Descriptor(descriptor_json)
            self.load()

    def load(self):
        manifest_json = self.descriptor.read()
        image_descriptor_json = manifest_json['config']
        self.image = Image(image_descriptor_json)

        self.layers = []
        self.size = 0
        for layer_descriptor_json in manifest_json['layers']:
            layer = Layer(layer_descriptor_json)
            self.size += layer.descriptor.size
            self.layers.append(layer)
