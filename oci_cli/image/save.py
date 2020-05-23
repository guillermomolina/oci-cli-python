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
import logging
from oci_api.image import Distribution, ImageUnknownException
from oci_api.util.file import tar

log = logging.getLogger(__name__)

class Save:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('save',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Save one or more images to a tar archive (streamed to STDOUT by default)',
            help='Save one or more images to a tar archive')
        parser.add_argument('-o', '--output', 
            help='Write to a file',
            default='STDOUT',
            metavar='string')
        parser.add_argument('image',
            nargs='+',
            metavar='IMAGE',
            help='Name of the image to save')
  
    def __init__(self, options):
        try:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                tmp_dir_path = pathlib.Path(tmp_dir_name)
                distribution = Image.distribution()
                for image_name in options.image:
                    distribution.save_image(image_name, tmp_dir_path)
                tar_file_path = None
                if options.output != 'STDOUT':
                    tar_file_path = pathlib.Path(options.output)
                log.debug('Sending tar to %s' % options.output)
                tar(tmp_dir_path, tar_file_path=tar_file_path)            
        except ImageUnknownException as e:
            log.error(e.args[0])
            exit(-1)
           