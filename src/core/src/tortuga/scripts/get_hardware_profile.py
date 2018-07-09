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

import argparse
import json

from tortuga.cli.tortugaCli import TortugaCli
from tortuga.wsapi.hardwareProfileWsApi import HardwareProfileWsApi


class GetHardwareProfileCli(TortugaCli):
    """
    Get hardware profile command line interface.
    """

    def parseArgs(self, usage=None):
        hardwareProfileAttrGroup = _('Hardware Profile Attribute Options')

        self.addOptionGroup(hardwareProfileAttrGroup, None)

        self.addOptionToGroup(
            hardwareProfileAttrGroup, '--name', required=True,
            help=_('hardware profile name'))

        self.addOptionToGroup(
            hardwareProfileAttrGroup, '--nodes', action='store_true',
            dest='getNodes', default=False, help=_('get list of nodes'))

        self.addOptionToGroup(
            hardwareProfileAttrGroup, '--networks', action='store_true',
            dest='getNetworks', default=False,
            help=_('get list of networks'))

        self.addOptionToGroup(
            hardwareProfileAttrGroup, '--admins',
            action='store_true', dest='getAdmins', default=False,
            help=_('get list of admins'))

        outputAttrGroup = _('Output formatting options')

        self.addOptionGroup(outputAttrGroup, None)

        self.addOptionToGroup(
            outputAttrGroup, '--json',
            action='store_true', default=False,
            help=_('JSON formatted output')
        )
        self.addOptionToGroup(
            outputAttrGroup, '--xml',
            action='store_true', default=False,
            help=argparse.SUPPRESS
        )

        super().parseArgs(usage=usage)

    def runCommand(self):
        self.parseArgs(usage=_('Display hardware profile details'))

        api = HardwareProfileWsApi(username=self.getUsername(),
                                   password=self.getPassword(),
                                   baseurl=self.getUrl())

        optionDict = {}

        if self.getArgs().getNodes:
            optionDict['nodes'] = True

        if self.getArgs().getNetworks:
            optionDict['hardwareprofilenetworks'] = True

        if self.getArgs().getAdmins:
            optionDict['admins'] = True

        if self.getArgs().getNetworks:
            optionDict['nics'] = True

        optionDict['resourceadapter'] = True

        hardwareProfile = api.getHardwareProfile(
            self.getArgs().name, optionDict)

        if self.getArgs().xml:
            print(hardwareProfile.getXmlRep())
        elif self.getArgs().json:
            print(json.dumps({
                'hardwareProfile': hardwareProfile.getCleanDict(),
            }, sort_keys=True, indent=4, separators=(',', ': ')))
        else:
            self.__console_output(hardwareProfile)

    def __console_output(self, hwprofile):
        print(hwprofile.getName())

        print(' ' * 2 + '- Description: {0}'.format(
            hwprofile.getDescription()))

        print(' ' * 2 + '- Install type: {0}'.format(
            hwprofile.getInstallType()))

        if self.getArgs().getNetworks:
            if hwprofile.getProvisioningNics():
                print(' ' * 2 + '- Provisioning networks:')

                for nic in hwprofile.getProvisioningNics():
                    print(' ' * 4 + '- {0}: {1}/{2}'.format(
                        nic.getNetworkDevice().getName(),
                        nic.getNetwork().getAddress(),
                        nic.getNetwork().getNetmask()))
            else:
                print(' ' * 2 + '- Provisioning networks: (none)')

        if self.getArgs().getNodes:
            if hwprofile.getNodes():
                print(' ' * 2 + '- Node(s):')

                for node in hwprofile.getNodes():
                    print(' ' * 4 + '- {0} (State: {1}, IP: {2})'.format(
                        node.getName(), node.getState(),
                        ', '.join([nic.getIp() for nic in node.getNics()])))
            else:
                print(' ' * 2 + '- Node(s): (none)')

        print(' ' * 2 + '- Name format: {0}'.format(hwprofile.getNameFormat()))

        if hwprofile.getLocation() != 'local' and \
                hwprofile.getResourceAdapter():
            # display add'l information for non-default resource adapter

            print(' ' * 2 + '- Resource adapter: {0}'
                  ' (location: {1}, cost: {2})'.format(
                      hwprofile.getResourceAdapter().getName(),
                      hwprofile.getLocation(), hwprofile.getCost()))

            print(' ' * 6 + '- Default configuration profile: {}'.format(
                hwprofile.getDefaultResourceAdapterConfig()
                if hwprofile.getDefaultResourceAdapterConfig() else
                'default'))

        if self.getArgs().getAdmins:
            if hwprofile.getAdmins():
                print(' ' * 2 + '- Admins:')

                for admin in hwprofile.getAdmins():
                    print(' ' * 4 + '- {0}'.format(admin.getUsername()))
            else:
                print(' ' * 2 + '- Admins: (none)')

        if hwprofile.getTags():
            print(' ' * 2 + '- {0} Tags:')

            for tag_key, tag_value in list(hwprofile.getTags().items()):
                print(' ' * 4 + '- {0}={1}'.format(tag_key, tag_value))
        else:
            print(' ' * 2 + '- Tags: (none)')


def main():
    GetHardwareProfileCli().run()


if __name__ == '__main__':
    main()
