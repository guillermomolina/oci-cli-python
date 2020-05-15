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
                layer_id = '<empty>'
                layer_size = 0
                if not history.get('EmptyLayer'):
                    if options.no_trunc:
                        layer_id = image.layers[layer_index].digest
                    else:
                        layer_id = image.layers[layer_index].small_id
                    layer_size = image.layers[layer_index].size()
                    layer_index += 1
                created_by = history.get('CreatedBy') or ''
                comment = history.get('Comment') or ''
                author = history.get('Author') or ''
                if not options.no_trunc:                    
                    if len(created_by) > 45:
                        created_by = created_by[:44] + '…'
                    if len(comment) > 45:
                        comment = comment[:44] + '…'
                    if len(author) > 45:
                        author = author[:44] + '…'
                history_json = {
                    'layer': layer_id,
                    'created': history.get('Created'),
                    'created by': created_by,
                    'size': humanize.naturalsize(layer_size),
                    'comment': comment,
                    'author': author
                }
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
