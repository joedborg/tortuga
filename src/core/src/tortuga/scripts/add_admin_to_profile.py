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
from tortuga.wsapi.hardwareProfileWsApi import HardwareProfileWsApi
from tortuga.wsapi.softwareProfileWsApi import SoftwareProfileWsApi


class AddAdminToProfileCli(TortugaCli):
    """
    Add an admin to a hw/sw profile command line interface.

    """
    def __init__(self):
        TortugaCli.__init__(self)

        profile_attr_group = _('Profile Attribute Options')

        self.addOptionGroup(
            profile_attr_group,
            _('Hardware or software profile must be specified.'))

        self.addOptionToGroup(
            profile_attr_group, '--software-profile', dest='swprofile',
            help=_('hardware profile name'))

        self.addOptionToGroup(
            profile_attr_group, '--hardware-profile', dest='hwprofile',
            help=_('software profile name'))

        profile_attr_group = _('Admin Attribute Options')

        self.addOptionGroup(
            profile_attr_group, _('Admin username must be specified.'))

        self.addOptionToGroup(
            profile_attr_group, '--admin-username', dest='adminUsername',
            help=_('Admin username'))

    def runCommand(self):
        self.parseArgs(_("""
Associates an existing adminstrative user with a hardware or software profile.
"""))
        swprofile = self.getArgs().swprofile
        hwprofile = self.getArgs().hwprofile

        if swprofile and hwprofile:
            raise InvalidCliRequest(
                _('Only one of --software-profile and --hardware-profile'
                  ' can be specified.'))

        if not swprofile and not hwprofile:
            raise InvalidCliRequest(
                _('Either --software-profile or --hardware-profile must'
                  ' be specified.'))

        admin_username = self.getArgs().adminUsername

        if admin_username is None:
            raise InvalidCliRequest(_('Missing Admin Username'))

        if swprofile:
            profile = swprofile
            api = SoftwareProfileWsApi(username=self.getUsername(),
                                       password=self.getPassword(),
                                       baseurl=self.getUrl(),
                                       verify=self._verify)
        else:
            profile = hwprofile
            api = HardwareProfileWsApi(username=self.getUsername(),
                                       password=self.getPassword(),
                                       baseurl=self.getUrl(),
                                       verify=self._verify)

        api.addAdmin(profile, admin_username)


def main():
    AddAdminToProfileCli().run()
