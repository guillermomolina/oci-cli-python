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
import humanize
import logging
from datetime import datetime, timezone
from oci_api.image import Distribution, ImageUnknownException
from oci_api.util.print import print_table

log = logging.getLogger(__name__)

class History:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('history',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Show the history of an image',
            help='Show the history of an image')
        parser.add_argument('--no-trunc',
            help='Don\'t truncate output', 
            action='store_true')
        parser.add_argument('image',
            metavar='IMAGE',
            help='Name of the image to show')
 
    def __init__(self, options):
        image_name = options.image
        try:
            distribution = Distribution()
            image = distribution.get_image(options.image)
            history_list = []
            layer_index = 0
            for history in image.config.get('History'):
                history_json = {
                    'image': image.small_id,
                    'created': history.get('Created'),
                    'created by': history.get('CreatedBy') or '',
                    'size': 0,
                    'comment': history.get('Comment') or '',
                    'author': history.get('Author') or ''
                }
                if options.no_trunc:
                    history_json['image'] = image.digest
                else:
                    if len(history_json['created by']) > 45:
                        history_json['created by'] = history_json['created by'][:44] + '…'
                if history.get('EmptyLayer'):
                    layer_index += 1
                else:
                    history_json['image'] = '<missing>'
                    history_json['size'] = image.layers[layer_index].size
                history_json['size'] = humanize.naturalsize(history_json['size'])
                self.insert_history(history_list, history_json)
            for history_json in history_list:
                history_json['created'] = humanize.naturaltime(datetime.now(tz=timezone.utc) - 
                    history_json['created'])
            print_table(history_list)
        except ImageUnknownException:
            log.error('Image (%s) does not exist' % image_name)
            exit(-1)


    def insert_history(self, history_list, history_json):
        for index, value in enumerate(history_list):
            if value['created'] < history_json['created']:
                history_list.insert(index, history_json)
                return
        history_list.append(history_json)
