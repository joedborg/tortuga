#!/usr/bin/env python

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

from tortuga.cli.tortugaCli import TortugaCli
from tortuga.exceptions.invalidCliRequest import InvalidCliRequest
from tortuga.exceptions.softwareUsesHardwareAlreadyExists \
    import SoftwareUsesHardwareAlreadyExists
from tortuga.wsapi.softwareProfileWsApi import SoftwareProfileWsApi


class SetProfileMappingCli(TortugaCli):
    """Hardware/software profile mapping CLI"""

    def __init__(self):
        super().__init__()

        option_group = _('Set profile mapping options')

        self.addOptionGroup(
            option_group,
            _('Software and hardware profile must be specified.'))

        self.addOptionToGroup(option_group,
                              '--software-profile',
                              metavar='NAME',
                              dest='swprofile',
                              help=_('software profile'))

        self.addOptionToGroup(option_group,
                              '--hardware-profile',
                              metavar='NAME',
                              dest='hwprofile',
                              help=_('hardware profile'))

    def runCommand(self):
        self.parseArgs(_("""
Multiple software profiles can be mapped to a single hardware profile to
accomodate a consistent software stack across mulitple resource adapters,
for example. All profiles must be mapped in order to be used for active nodes.
"""))

        if not self.getArgs().swprofile:
            raise InvalidCliRequest(
                _('Software profile name must be specified'))

        if not self.getArgs().hwprofile:
            raise InvalidCliRequest(
                _('Hardware profile name must be specified'))

        api = SoftwareProfileWsApi(username=self.getUsername(),
                                   password=self.getPassword(),
                                   baseurl=self.getUrl())

        try:
            api.addUsableHardwareProfileToSoftwareProfile(
                self.getArgs().hwprofile, self.getArgs().swprofile)
        except SoftwareUsesHardwareAlreadyExists:
            pass


def main():
    SetProfileMappingCli().run()
