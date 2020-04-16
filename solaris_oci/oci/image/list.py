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
import pathlib
import json
from dateutil import parser
import humanize
from datetime import *

from opencontainers.digest import NewDigestFromEncoded, Parse
from opencontainers.image.v1 import Index

from solaris_oci.util.print import print_table

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
        oci_path = pathlib.Path('/var/lib/oci')
        self.images_path = oci_path.joinpath('image')

        distribution = self.load_distribution()
        #print(json.dumps(distribution, indent=2))
        
        images = []
        for repository in distribution['repositories']:
            repository_name = repository['annotations']['org.opencontainers.repository.ref.name']
            for index in repository['indexes']:
                image = {
                    'repository': repository_name,
                }
                image['tag'] = index['annotations']['org.opencontainers.tag.ref.name']
                if options.digests:
                    image['digest'] = index['digest']
                image_id = repository['digest']
                if not options.no_trunc:
                    image_id = image_id.split(':')[1][0:12]
                image['image id'] = image_id
                manifest = index['manifests'][0]
                config = manifest['config']
                created = parser.isoparse(config['created'])
                image['created'] = created
                #image['created'] = relativedelta(created, now)
                size = 0
                for layer in manifest['layers']:
                    size += layer['size']
                image['size'] = humanize.naturalsize(size)
                self.insert_image(images, image)
        
        for image in images:
            image['created'] = humanize.naturaltime(datetime.now(tz=timezone.utc) - image['created'])
        print_table(images)

    def insert_image(self, images, image):
        for index, value in enumerate(images):
            if value['created'] < image['created']:
                images.insert(index, image)
                return
        images.append(image)
        
    def load_distribution(self):
        distribution_path = self.images_path.joinpath('distribution.json')
        with distribution_path.open() as distribution_file:
            # load distribution.json
            distribution = json.load(distribution_file)
            for repository in distribution['repositories']:
                # load repository.json
                repository.update(self.load_blob(repository['digest']))
                for index in repository['indexes']:
                    # load index.json
                    index.update(self.load_blob(index['digest']))
                    for manifest in index['manifests']:
                        # load manifest.json
                        manifest.update(self.load_blob(manifest['digest']))
                        config = manifest['config']
                        # load config.json
                        config.update(self.load_blob(config['digest']))
            return distribution      
        return {}

    def load_blob(self, digest):
        blobs_path = self.images_path.joinpath('blobs')
        blob_path = blobs_path.joinpath(digest.replace(':', '/'))
        with blob_path.open() as blob_file:
            return json.load(blob_file)
        return {}

