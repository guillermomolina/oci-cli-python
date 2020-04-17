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

import subprocess
import argparse
import humanize
from datetime import *

from solaris_oci.util.print import print_table
from solaris_oci.oci import config as oci_config
from solaris_oci.oci.image.distribution import Distribution

class List:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('ls',
            parents=[parent_parser],
            aliases=['list'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='List images',
            help='List images')
        parser.add_argument('--digests',
            help='Show digests', 
            action='store_true')
        parser.add_argument('--no-trunc',
            help='Don\'t truncate output', 
            action='store_true')
             
    def __init__(self, options):
        distribution = Distribution() 
        distribution.load()
        images = []
        for image in distribution.images():
            data = {}
            data['registry'] = image['registry']
            data['tag'] = image['tag']
            if options.digests:
               data['digest'] = image['digest']
            image_id = image['id']
            if not options.no_trunc:
                image_id = image_id.split(':')[1][0:12]
            data['image id'] = image_id
            data['created'] = image['created']
            data['size'] = humanize.naturalsize(image['size'])
            self.insert_image(images, data)
        for image in images:
            image['created'] = humanize.naturaltime(datetime.now(tz=timezone.utc) - image['created'])
        print_table(images)

    def insert_image(self, images, image):
        for index, value in enumerate(images):
            if value['created'] < image['created']:
                images.insert(index, image)
                return
        images.append(image)
