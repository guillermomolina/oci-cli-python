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
from dateutil import parser

from .. import config as oci_config
from opencontainers.struct import Struct, StrStruct, IntStruct
from opencontainers.image.v1 import Index, Manifest, Image
from .opencontainers.image.v1 import Repository

media_type_registry = {
    'application/vnd.oci.image.repository.v1+json': Repository,
    'application/vnd.oci.image.index.v1+json': Index,
    'application/vnd.oci.image.manifest.v1+json': Manifest,
    'application/vnd.oci.image.config.v1+json': Image
}

def attr_to_dict(attr_data):
    """return a dictionary representation of the attribute. This won't
        be called unless the attribute in question is a struct.
    """
    if isinstance(attr_data.value, (str, int)):
        return attr_data.value

    if isinstance(attr_data.value, list):
        items = []
        for item in attr_data.value:
            if isinstance(item, (str, int)):
                items.append(item)
            elif isinstance(item, (Struct, StrStruct, IntStruct)):
                items.append(struct_to_dict(item))
            else:
                items.append(item)
        return items

    return struct_to_dict(attr_data.value)

def struct_to_dict(struct_data):
    """return a Struct as a dictionary, must be valid
    """
    # A lookup of "empty" values based on types (mirrors Go)
    lookup = {str: "", int: None, list: [], dict: {}}

    # import code
    # code.interact(local=locals())

    if struct_data.validate():
        result = {}
        for att in struct_data.attrs.values():
            # Don't show if unset and omit empty, OR marked to hide
            if (not att.value and att.omitempty) or att.hide:
                continue
            if not att.value:
                value = lookup.get(att.attType, [])
            else:
                # If structure or list, call to_dict
                if att._is_struct() or isinstance(att.value, list):
                    value = attr_to_dict(att)
                else:
                    value = att.value
            if att.attType == datetime:
                value = parser.isoparse(value)
            result[att.jsonName] = value

        return result


class Descriptor:
    def __init__(self, descriptor_json=None):
        if descriptor_json is not None:
            self.__dict__.update(descriptor_json)
    
    def read(self):
        digest_path = self.digest.replace(':', '/')
        blob_path = oci_config.blob_path.joinpath(digest_path)  
        with blob_path.open() as descriptor_file:
            json_data = json.load(descriptor_file)
            # Do some struct checking
            OC_Struct = media_type_registry[self.mediaType]
            struct_data = OC_Struct()
            struct_data.load(json_data, validate=True)
            json_data = struct_to_dict(struct_data)
            # Done
            return json_data
        return {}

