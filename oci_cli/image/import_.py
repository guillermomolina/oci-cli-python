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

class Import:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('import',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Import the contents from a tarball to create a filesystem image',
            help='Import the contents from a tarball')
        parser.add_argument('-m', '--message', 
            help='Set commit message for imported image',
            metavar='string')
        parser.add_argument('-r', '--runc-config', 
            help='path to the runc spec file config.json')
        parser.add_argument('file',
            metavar='file|URL|-',
            help='Name of the file or URL to import, or "-" for the standard input')
        parser.add_argument('tag',
            metavar='REPOSITORY[:TAG]',
            nargs='?',
            help='Name of the repository to import to')
  
    def __init__(self, options):
        log.debug('Start importing (%s)' % options.file)
        layer = None
        with tempfile.TemporaryDirectory() as temp_dir_name:
            if options.file == '-':
                input_file = os.fdopen(sys.stdin.fileno(), 'rb')
            else:
                try:
                    input_file = urlopen(options.file)
                except ValueError:
                    input_file = open(options.file, 'rb')
            rootfs_tar_path = pathlib.Path(temp_dir_name, 'rootfs.tar')
            with rootfs_tar_path.open('wb') as output_file:
                log.debug('Start copying (%s) to (%s)', options.file, str(rootfs_tar_path))
                shutil.copyfileobj(input_file, output_file)
                log.debug('Finish copying (%s) to (%s)', options.file, str(rootfs_tar_path))
            if rootfs_tar_path.is_file():
                filesystem = Driver().create_filesystem()
                untar(filesystem.path, tar_file=input_file)
                layer = Driver().create_layer(filesystem)
        if layer is None:
            log.error('Could not create layer')        
            exit(-1)
        try:
            distribution = Distribution()
            history = '/bin/sh -c #(nop) IMPORTED file:%s in / ' % options.file
            image = Distribution().create_image(layer=layer, history=history)
            if options.runc_config is not None:
                config_file_path = pathlib.Path(options.runc_config)
                if not config_file_path.is_file():
                    OCIError('Runc config file (%s) does not exist' % str(config_file_path))
                spec = Spec.from_file(config_file_path)
                process = spec.get('Process')
                command = process.get('Args')
                if command is not None:
                    image.set_command(command)
                environment = process.get('Env')
                if environment is not None:
                    image.set_environment(environment)
                working_dir = process.get('Cwd')
                if working_dir is not None:
                    image.set_working_dir(working_dir)
                    if options.tag is not None:
                        for tag in options.tag:
                            Distribution().add_tag(self.image, tag)
        except Exception as e:
            log.error(e.args[0])
            exit(-1)
        log.debug('Finish importing (%s)' % options.file)
