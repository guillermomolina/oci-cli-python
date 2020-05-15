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
import tempfile
import sys
import logging
from oci_api import OCIError
from oci_api.image import Distribution, ImageExistsException
from oci_api.util.file import untar

log = logging.getLogger(__name__)

class Load:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('load',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Load an image from a tar archive or STDIN',
            help='Load an image from a tar archive or STDIN')
        parser.add_argument('-i', '--input', 
            help='Read from tar archive file',
            default='STDIN',
            metavar='string')
        parser.add_argument('image',
            metavar='IMAGE',
            help='Name of the image to load')
  
    def __init__(self, options):
        image_name = options.image
        try:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                tmp_dir_path = pathlib.Path(tmp_dir_name)
                input_file = sys.stdin
                if options.input != 'STDIN':
                    input_file = open(options.input, 'rb')
                log.debug('Start receiving tar from %s' % options.input)
                untar(tmp_dir_path, tar_file=input_file)
                log.debug('Finish receiving tar from %s' % options.input)
                distribution = Distribution()
                distribution.load_image(image_name, tmp_dir_path)
        except ImageExistsException:
            log.error('Image (%s) already exists' % image_name)
            exit(-1)
        except Exception as e:
            raise e
            log.error('Could not remove image (%s)' % image_name)
            exit(-1)
