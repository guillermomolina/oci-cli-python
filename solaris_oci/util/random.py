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


import secrets
import random
from .random_names import left, right

def generate_random_sha256():
    return secrets.token_hex(nbytes=32)

def generate_random_id():
    return secrets.token_hex(nbytes=8)

def digest_to_id(digest):
    return digest.split(':')[1]

# Based on: https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go
def generate_random_name(exclude_list=None):
	exclude = exclude_list or []
	exclude.append('boring_wozniak') # Steve Wozniak is not boring
	retry = 0 
	while True:
		name = random.choice(left) + '_' + random.choice(right)

		if retry > 10:
			name += str(random.randrange(0, retry))

		if name not in exclude:
			return name

		retry += 1
