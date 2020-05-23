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
from oci_api import OCIError
from oci_api.image import Distribution, ImageInUseException, ImageUnknownException
from oci_api.runtime import Runtime

log = logging.getLogger(__name__)

class Remove:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('rm',
            parents=[parent_parser],
            aliases=['remove', 'rmi'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Remove one or more images',
            help='Remove one or more images')
        parser.add_argument('-f', '--force',
            help='Force removal of the image', 
            action='store_true')
        parser.add_argument('--no-prune',
            help='Do not delete untagged parents', 
            action='store_true')
        parser.add_argument('image',
            nargs='+', 
            metavar='IMAGE',
            help='Name of the image to remove')
 
    def __init__(self, options):
        distribution = Distribution()
        for image_name in options.image:
            try:
                image = distribution.get_image(image_name)
                distribution.remove_image(image, options.force)
            except ImageInUseException:
                runtime = Runtime()
                containers =  runtime.get_containers_using_image(image.id)
                container_ids = [container.small_id for container in containers]
                log.error('Image (%s) is being by containers (%s), can not remove' %
                    (image_name, ','.join(container_ids)))
                exit(-1)
            except ImageUnknownException:
                log.error('Image (%s) does not exist' % image_name)
                exit(-1)
            except Exception as e:
                log.error('Could not remove image (%s)' % image_name)
                raise e
                exit(-1)
