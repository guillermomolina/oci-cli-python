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
from opencontainers.image.v1.mediatype import MediaTypeImageIndex

class Repository(Struct):
    """Repository references indexes.
       This structure provides `application/vnd.oci.image.index.v1+json` 
       mediatype when marshalled to JSON.
    """

    def __init__(self, indexes=None, schemaVersion=None, annotations=None):
        super().__init__()

        self.newAttr(name="schemaVersion", attType=Versioned, required=True)

        # Indexes references image indexes.
        self.newAttr(
            name="Indexes", attType=[Descriptor], jsonName="indexes", required=True
        )

        # Annotations contains arbitrary metadata for the image index.
        self.newAttr(name="Annotations", attType=dict, jsonName="annotations")

        self.add("Indexes", indexes)
        self.add("Annotations", annotations)
        self.add("schemaVersion", schemaVersion)

    def _validate(self):
        """custom validation function to ensure that Manifests mediaTypes
           are valid.
        """
        # No indexes, not valid
        indexes = self.attrs.get("Indexes").value
        if not indexes:
            return False

        # Check against valid mediaType Indexes
        for index in indexes:
            mediaType = index.attrs.get("MediaType").value
            if mediaType != MediaTypeImageIndex:
                bot.error("index mediaType %s is invalid" % mediaType)
                return False

        return True
