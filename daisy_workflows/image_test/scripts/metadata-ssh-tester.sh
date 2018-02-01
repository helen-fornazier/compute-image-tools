#!/bin/bash
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

set -x

TESTEE=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/testee)
ZONE=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone)
SSH_KEY=tester-ssh-key

# Generate ssh key
ssh-keygen -t rsa -N "" -f ${SSH_KEY} -C tester
echo -n "tester:$(cat ${SSH_KEY}.pub)" > formatted-${SSH_KEY}.pub

# Add key in instance level
gcloud compute instances add-metadata ${TESTEE} --metadata-from-file ssh-keys=formatted-${SSH_KEY}.pub --zone ${ZONE}

# Try to login
ssh -i ${SSH_KEY} -o "StrictHostKeyChecking no" tester@${TESTEE} echo "Logged"
if [[ $? -eq 0 ]]; then
  echo "MetadataSshTestSuccess"
else
  echo "MetadataSshTestFailed"
fi
