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

from opencontainers.struct import Struct
from opencontainers.logger import bot
from opencontainers.image.specs import Versioned
from opencontainers.image.v1.descriptor import Descriptor
from opencontainers.image.v1.mediatype import MediaTypeImageRepository

class Distribution(Struct):
    """Distribution references repositories.
       This structure provides `application/vnd.oci.image.repository.v1+json` 
       mediatype when marshalled to JSON.
    """

    def __init__(self, repositories=None, schemaVersion=None, annotations=None):
        super().__init__()

        self.newAttr(name="schemaVersion", attType=Versioned, required=True)

        # Repositories references image repositories.
        self.newAttr(
            name="Repositories", attType=[Descriptor], jsonName="repositories", required=True
        )

        # Annotations contains arbitrary metadata for the image repository.
        self.newAttr(name="Annotations", attType=dict, jsonName="annotations")

        self.add("Repositories", repositories)
        self.add("schemaVersion", schemaVersion)

    def _validate(self):
        """custom validation function to ensure that Manifests mediaTypes
           are valid.
        """
        # No repositories, not valid
        repositories = self.attrs.get("Repositories").value
        if not repositories:
            return False

        # Check against valid mediaType Repositories
        for repository in repositories:
            mediaType = repository.attrs.get("MediaType").value
            if mediaType != MediaTypeImageRepository:
                bot.error("repository mediaType %s is invalid" % mediaType)
                return False

        return True
