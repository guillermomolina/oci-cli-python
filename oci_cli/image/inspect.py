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
import logging
from oci_api.image import Distribution, ImageUnknownException

log = logging.getLogger(__name__)

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
        distribution = Distribution()
        for image_name in options.image:
            try:
                image = distribution.get_image(image_name)
                image_json = image.config.to_dict(use_real_name=True)
                image_json.pop('History')
                image_json['Size'] = image.size()
                image_json['VirtualSize'] = image.virtual_size()
                if len(image.tags) > 0:
                    image_json['RepoTags'] = image.tags
                repositories = distribution.get_repositories(image)
                if len(repositories) > 0:
                    image_json['RepoDigests'] = [repository + '@' + image.digest for repository in repositories]
                print(json.dumps(image_json, indent=4, default=str))
            except ImageUnknownException:
                log.error('Image (%s) does not exist' % image_name)
                exit(-1)
