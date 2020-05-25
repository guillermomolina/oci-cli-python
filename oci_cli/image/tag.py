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
import pathlib
import logging
import sys
import tempfile
import shutil
import os
from urllib.request import urlopen
from oci_spec.image.v1 import ImageConfig
from oci_spec.runtime.v1 import Spec
from oci_api import OCIError
from oci_api.util.file import untar
from oci_api.image import Distribution
from oci_api.graph import Driver
log = logging.getLogger(__name__)

class Tag:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('tag',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Create a tag TARGET_IMAGE that refers to SOURCE_IMAGE',
            help='Create a tag TARGET_IMAGE that refers to SOURCE_IMAGE')
        parser.add_argument('image',
            metavar='SOURCE_IMAGE[:TAG]',
            nargs='?',
            help='Name of the tag to refer to')
        parser.add_argument('tag',
            metavar='TARGET_IMAGE[:TAG]',
            nargs='?',
            help='Name of tag to create')
  
    def __init__(self, options):
        log.debug('Start adding tag (%s) to image (%s)' % (options.tag, options.image))
        distribution = Distribution()
        try:
            image = distribution.get_image(options.image)
            distribution.add_tag(image, options.tag)
        except OCIError as e:
            log.error(e.args[0])
            exit(-1)
        log.debug('Finish adding tag (%s) to image (%s)' % (options.tag, options.image))
