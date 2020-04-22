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
import argparse
from solaris_oci.oci.image import Distribution

class Inspect:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('inspect',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Display detailed information on one or more images',
            help='Display detailed information on one or more images')
        parser.add_argument('image',
            nargs='+', 
            metavar='IMAGE',
            help='Name of the image to inspect')
 
    def __init__(self, options):
        images = self.images(options.image)
        print(json.dumps(images, indent=4, default=str))

    def images(self, filter):
        repositories = {}
        for reference in filter:
            records = reference.split(':')
            name = records[0]
            tag = None
            if len(records) == 2 and len(records[1]) != 0:
                tag = records[1]
            tags = repositories.get(name, [])
            if tag is None:
                value = None
            else:
                if tags is None:
                    value = None
                else:
                    tags.append(tag)
                    value = tags
            repositories[name] = value
    
        distribution = Distribution()
        distribution.load()
        images = []
        for repository in distribution.repositories:
            if repository.name in repositories.keys():
                tags = repositories[repository.name]
                for tag in repository.images:
                    if tags is None or tag.tag in tags:
                        for manifest in tag.manifests:
                            image = manifest['config']
                            images.append(image.to_dict(use_real_name=True))
        return images
