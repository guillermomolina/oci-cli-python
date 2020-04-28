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

class Remove:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('rm',
            parents=[parent_parser],
            aliases=['remove', 'rmi'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Remove one or more images',
            help='Remove one or more images')
        parser.add_argument('image',
            nargs='+', 
            metavar='IMAGE',
            help='Name of the image to remove')
 
    def __init__(self, options):
        distribution = Distribution()
        images = self.images(distribution, options.image)
        for repository, tag in images:
            distribution.destroy_image(repository, tag)

    def images(self, distribution, filter):
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
    
        images = []
        for repository in distribution.repositories.values():
            if repository.name in repositories:
                tags = repositories[repository.name]
                for tag in repository.images:
                    if tags is None or tag in tags:
                        images.append((repository.name, tag))
        return images
