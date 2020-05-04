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
from solaris_oci import oci
from solaris_oci.util import generate_random_sha256

class Container():
    def __init__(self, id=None):
        self.id = id
        self.path = None
        self.image = None
        if id is not None:
            self.load()

    def load(self):
        raise NotImplementedError()

    def create(self, image):
        self.image = image
        self.id = generate_random_sha256()
        containers_path = pathlib.Path(oci.config['containers']['path'])
        self.path = containers_path.joinpath(self.id)
        raise NotImplementedError()

    def remove(self):
        raise NotImplementedError()


