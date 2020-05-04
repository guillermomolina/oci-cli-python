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
        for reference in options.image:
            name_and_tag = reference.split(':')            
            if len(name_and_tag) == 1:
                image_name = name_and_tag[0]
                tag_name = 'latest'
            elif len(name_and_tag) == 2:
                image_name = name_and_tag[0]
                tag_name = name_and_tag[1]
            else:
                continue
            try:
                distribution.remove_image(image_name, tag_name)
            except Exception as e:
                raise e
                print('Could not remove image (%s:%s)' % (image_name, tag_name))
