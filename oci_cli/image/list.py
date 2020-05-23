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

import argparse
import humanize
from datetime import datetime, timezone
from oci_api.util import split_image_name
from oci_api.util.print import print_table
from oci_api.image import Distribution

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
        images = []
        for image in Distribution().images.values():
            config = image.config
            image_json = {}
            image_json['repository'] = '<none>'
            image_json['tag'] = '<none>'
            if options.digests:
                image_json['digest'] = image.top_layer().digest
            image_id = image.id
            if not options.no_trunc:
                image_id = image.small_id
            image_json['image id'] = image_id
            image_json['created'] = config.get('Created')
            image_json['size'] = humanize.naturalsize(image.size())
            if len(image.tags) == 0:
                self.insert_image(images, image_json)
            else:
                for image_name in image.tags:
                    (repository, tag) = split_image_name(image_name)
                    image_json['repository'] = repository
                    image_json['tag'] = tag
                    self.insert_image(images, image_json)
                    image_json = image_json.copy()
        now = datetime.now(tz=timezone.utc)
        for image_json in images:
            created = image_json['created']
            image_json['created'] = humanize.naturaltime(now - created)
        print_table(images)

    def insert_image(self, images, image_json):
        for index, value in enumerate(images):
            if value['created'] < image_json['created']:
                images.insert(index, image_json)
                return
        images.append(image_json)
