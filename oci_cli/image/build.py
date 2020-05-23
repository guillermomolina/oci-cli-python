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
from urllib.parse import urlparse
from oci_api import OCIError
from oci_api.image import ImageUnknownException, Distribution, create_config, config_set_command, \
    config_add_diff
from oci_api.graph import Driver
from oci_api.util.file import untar, cp

log = logging.getLogger(__name__)

class DockerfileParseException(OCIError):
    pass

class Build:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('build',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Build an image from a Dockerfile',
            help='Build an image from a Dockerfile')
        parser.add_argument('-f', '--file', 
            help='Name of the Dockerfile (relative to PATH)',
            default='Dockerfile',
            metavar='string')
        parser.add_argument('-t', '--tag',
            action='append',
            help='Name and optionally a tag in the "name:tag" format',
            metavar='list')
        parser.add_argument('path',
            metavar='PATH|URL|-',
            help='Path or URL of the context, or "-" for the standard input')
  
    def __init__(self, options):
        if options.path == '-':
            raise NotImplementedError()
        else:
            url = urlparse(options.path)
            if url.scheme is not '':
                raise NotImplementedError()
            self.context_path = pathlib.Path(options.path)
        dockerfile_path = pathlib.Path(options.file)
        if not dockerfile_path.is_absolute():
            dockerfile_path = self.context_path.joinpath(dockerfile_path)
        if not dockerfile_path.is_file():
            log.error('Dockerfile (%s) does not exist' % dockerfile_path)
        log.debug('Reading dockerfile (%s)' % dockerfile_path.resolve())
        self.layers = None
        self.config = None
        with dockerfile_path.open() as dockerfile:
            for line in dockerfile:
                stripped_line = line.strip()
                if len(stripped_line) == 0 or stripped_line.startswith('#'):
                    continue
                while stripped_line.endswith('\\'):
                    stripped_line = stripped_line[:-1] + dockerfile.readline().strip()
                records = stripped_line.split(' ', 1)
                if len(records) != 2:
                    raise DockerfileParseException('Malformed command (%s)' % line)
                command = records[0]
                self.do_command(command, records[1])
        image = Distribution().create_image(self.config, self.layers)
        if options.tag is not None:
            for tag in options.tag:
                Distribution().add_tag(image, tag)
        log.info('Created image (%s)' % image.id)

    def do_command(self, command, line):
        command_list = {
            'FROM': self.do_command_from,
            'ADD': self.do_command_add,
            'CMD': self.do_command_cmd,
            'RUN': self.do_command_run
        }
        if command in command_list:
            command_list[command](line)
        else:
            raise DockerfileParseException('Unrecognized command (%s)' % command)

    def do_command_from(self, line):
        records = line.split(' ')
        if len(records) != 1:
            raise DockerfileParseException('Use FROM <image> instead of FROM %s' % line)
        image_ref = records[0]
        if self.config is not None:
            raise DockerfileParseException('FROM is allowed only once')
        if image_ref == 'scratch':
            self.layers = []
            self.config = create_config()
        else:
            image = Distribution().get_image(image_ref)
            self.layers = image.layers.copy()
            self.config = image.config.copy()

    def do_command_add(self, line):
        records = line.split(' ')
        if len(records) != 2:
            raise DockerfileParseException('Use ADD <file> <dir_or_file> instead of ADD %s' % line)
        file_name = records[0]
        dir_name = records[1]
        file_path = self.context_path.joinpath(file_name)
        target_path = pathlib.Path(dir_name)
        if not file_path.is_file():
            log.error('File (%s) not found' % file_path)
            exit(-1)
        if len(self.layers) == 0:
            top_layer = None
        else:
            top_layer = self.layers[-1]
        filesystem = Driver().create_filesystem(top_layer)
        image_target_path = filesystem.path.joinpath(target_path.relative_to('/'))
        if file_path.suffix == '.tar':
            untar(image_target_path, tar_file_path=file_path)
        else:
            cp(file_path, image_target_path)
        layer = Driver().create_layer(filesystem) 
        config_add_diff(self.config, layer.diff_digest, 'ADD file:%s in /' % file_name) 
        self.layers.append(layer)
        
    def do_command_cmd(self, line):
        command = line.split(' ')
        config_set_command(self.config, command, 'CMD ["%s"]' % line) 
        
    def do_command_run(self, line):
        raise NotImplementedError()

