#!/usr/bin/python
# Copyright 2018 Google Inc. All Rights Reserved.
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


import logging
import re
import time
import uuid

import utils

utils.AptGetInstall(['python-pip'])
utils.Execute(['pip', 'install', '--upgrade', 'google-api-python-client'])

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

TESTEE = None
PROJECT = None
ZONE = None
COMPUTE = None

def gen_ssh_key():
  key_name = 'key-' + str(uuid.uuid4())
  utils.Execute(['ssh-keygen', '-t', 'rsa', '-N', '', '-f', key_name, '-C', key_name])
  with open(key_name + '.pub', 'r') as original: data = original.read()
  return "tester:" + data, key_name


def get_metadata_ssh_keys_instance_level():
  request = COMPUTE.instances().get(project=PROJECT, zone=ZONE, instance=TESTEE)
  response = request.execute()
  items = response['metadata']['items']
  fingerprint = response['metadata']['fingerprint']
  try:
    value = (metadata['value'] for metadata in items if metadata['key'] == 'ssh-keys').next()
  except StopIteration:
    value = None
  return value, fingerprint


def set_metadata_ssh_keys_instance_level(fingerprint, new_keys):
  metadata_body = {
    'fingerprint': fingerprint,
    'items': [
      {
        'key': 'ssh-keys',
        'value': new_keys,
      }
    ]
  }
  request = COMPUTE.instances().setMetadata(project=PROJECT, zone=ZONE, instance=TESTEE, body=metadata_body)
  response = request.execute()


def add_ssh_keys_instance_level():
  existent_ssh_keys, fingerprint = get_metadata_ssh_keys_instance_level()
  key, key_name = gen_ssh_key()
  new_keys = '\n'.join([existent_ssh_keys, key]) if existent_ssh_keys else key
  set_metadata_ssh_keys_instance_level(fingerprint, new_keys)
  return key_name


def remove_ssh_keys_instance_level(key):
  existent_ssh_keys, fingerprint = get_metadata_ssh_keys_instance_level()
  new_keys = re.sub('.*%s.*\n?' % key, '', existent_ssh_keys)
  set_metadata_ssh_keys_instance_level(fingerprint, new_keys)


def test_login(key, expect_fail=False):
  ret, _ = utils.Execute(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', 'tester@' + TESTEE, 'echo', 'Logged'], raise_errors=False)
  if expect_fail and ret == 0:
    raise ValueError('SSH Loging succeeded when expected to fail')
  elif not expect_fail and ret != 0:
    raise ValueError('SSH Loging failed when expected to succeed')


def test_login_ssh_instance_level_key():
  key = add_ssh_keys_instance_level()
  time.sleep(5)
  test_login(key)
  remove_ssh_keys_instance_level(key)
  time.sleep(5)
  test_login(key, expect_fail=True)


'''
def test_login_ssh_project_level_key():
  key = add_ssh_keys_project_level()
  test_login(key)
  remove_ssh_keys_project_level()
  test_login(key, expect_fail=True)


def test_ssh_keys_with_sshKeys():
  ssh_keys_key = add_ssh_keys_instance_level()
  sshKey_key = add_sshKey_instance_level()
  test_login(ssh_keys_key)
  test_login(sshKey_key)
  remove_ssh_keys_instance_level(ssh_keys_key)
  remove_sshKey_instance_level(sshKey_key)
  test_login(ssh_keys_key, expect_fail=True)
  test_login(sshKey_key, expect_fail=True)


def test_ssh_keys_mixed_project_instance_level():
  i_key = add_ssh_keys_instance_level()
  p_key = add_ssh_keys_project_level()
  test_login(p_key)
  test_login(i_key)
  remove_ssh_keys_instance_level(i_key)
  remove_ssh_keys_project_level(p_key)
  test_login(p_key, expect_fail=True)
  test_login(i_key, expect_fail=True)


def test_sshKeys_ignores_project_level_keys():
  ssh_keys_key = add_ssh_keys_project_level()
  sshKey_key = add_sshKey_instance_level()
  test_login(ssh_keys_key, expect_fail=True)
  test_login(sshKey_key)
  remove_sshKey_instance_level(sshKey_key)
  test_login(sshKey_key, expect_fail=True)
  test_login(ssh_keys_key)
  remove_ssh_keys_project_level(ssh_keys_key)
  test_login(ssh_keys_key, expect_fail=True)


def test_block_project_ssh_keys_ignores_project_level_keys():
  set_block_project_ssh_keys(True)
  i_key = add_ssh_keys_instance_level()
  p_key = add_ssh_keys_project_level()
  test_login(p_key, expect_fail=True)
  test_login(i_key)
  set_block_project_ssh_keys(False)
  test_login(p_key)
  test_login(i_key)
  remove_ssh_keys_instance_level(i_key)
  remove_ssh_keys_project_level(p_key)
  test_login(p_key, expect_fail=True)
  test_login(i_key, expect_fail=True)


def test_ssh_keys_sshKeys_project_level():
  ssh_keys_key = add_ssh_keys_project_level()
  sshKey_key = add_sshKey_project_level()
  test_login(ssh_keys_key)
  test_login(sshKey_key)
  remove_sshKey_project_level(sshKey_key)
  remove_ssh_keys_project_level(ssh_keys_key)
  test_login(sshKey_key, expect_fail=True)
  test_login(ssh_keys_key, expect_fail=True)
'''

def main():
  global COMPUTE
  global ZONE
  global PROJECT
  global TESTEE

  COMPUTE = utils.GetCompute(discovery, GoogleCredentials) 
  ZONE = utils.GetMetadataParam('zone')
  PROJECT = utils.GetMetadataParam('project')
  TESTEE = utils.GetMetadataParam('testee')

  test_login_ssh_instance_level_key()
'''
  test_login_ssh_project_level_key()
  test_ssh_keys_with_sshKeys()
  test_ssh_keys_mixed_project_instance_level()
  test_sshKeys_ignores_project_level_keys()
  test_block_project_ssh_keys_ignores_project_level_keys()
  test_ssh_keys_sshKeys_project_level()
'''

if __name__=='__main__':
  utils.RunTest(main) 
