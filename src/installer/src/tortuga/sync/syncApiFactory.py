# Copyright 2008-2018 Univa Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=no-member

from tortuga.config.configManager import ConfigManager


def getSyncApi(username=None, password=None):
    cm = ConfigManager()

    if username and password or not cm.isDbAvailable():
        from tortuga.wsapi import syncWsApi
        api = syncWsApi.SyncWsApi(username, password)
    else:
        from tortuga.sync import syncApi
        api = syncApi.SyncApi()

    return api
