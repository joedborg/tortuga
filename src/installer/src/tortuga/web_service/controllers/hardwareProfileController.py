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

import cherrypy

from tortuga.exceptions.hardwareProfileNotFound import HardwareProfileNotFound
from tortuga.exceptions.userNotAuthorized import UserNotAuthorized
from tortuga.hardwareprofile.hardwareProfileManager import \
    HardwareProfileManager
from tortuga.objects.hardwareProfile import HardwareProfile
from tortuga.objects.osInfo import OsInfo
from tortuga.objects.tortugaObject import TortugaObjectList
from tortuga.web_service.auth.decorators import authentication_required
from .common import parse_tag_query_string, make_options_from_query_string
from .tortugaController import TortugaController


class HardwareProfileController(TortugaController):
    actions = [
        {
            'name': 'getHardwareProfiles',
            'path': '/v1/hardwareprofiles/',
            'action': 'getHardwareProfiles',
            'method': ['GET'],
        },
        {
            'name': 'getHardwareProfile',
            'path': '/v1/hardwareprofiles/:(hwprofile_id)',
            'action': 'getHardwareProfile',
            'method': ['GET'],
        },
        {
            'name': 'deleteHardwareProfile',
            'path': '/v1/hardwareprofiles/:(hardwareProfileName)',
            'action': 'deleteHardwareProfile',
            'method': ['DELETE'],
        },
        {
            'name': 'createHardwareProfile',
            'path': '/v1/hardwareprofiles/',
            'action': 'createHardwareProfile',
            'method': ['POST'],
        },
        {
            'name': 'updateHardwareProfile',
            'path': '/v1/hardwareprofiles/:(hardwareProfileId)',
            'action': 'updateHardwareProfile',
            'method': ['PUT'],
        },
        {
            'name': 'copyHardwareProfile',
            'path': '/v1/hardwareprofiles/:(srcHardwareProfileName)/copy/:(dstHardwareProfileName)',
            'action': 'copyHardwareProfile',
            'method': ['POST'],
        },
        {
            'name': 'getHardwareProfileNodes',
            'path': '/v1/hardwareprofiles/:(hardwareProfileName)/nodes',
            'action': 'getNodes',
            'method': ['GET'],
        },
        {
            'name': 'getHardwareProfileProvisioningInfo',
            'path': '/v1/hardwareprofiles/:(hardwareProfileName)'
                    '/provisioningInfo',
            'action': 'getProvisioningInfo',
            'method': ['GET'],
        },
        {
            'name': 'addHwAdmin',
            'path': '/v1/hardwareprofiles/:(hardwareProfileName)'
                    '/admin/:(adminUsername)',
            'action': 'addAdmin',
            'method': ['POST'],
        },
        {
            'name': 'deleteHwAdmin',
            'path': '/v1/hardwareprofiles/:(hardwareProfileName)'
                    '/admin/:(adminUsername)',
            'action': 'deleteAdmin',
            'method': ['DELETE'],
        },
        {
            'name': 'getVirtualContainerNodes',
            'path': '/v1/hardwareprofiles/:hardwareProfileName'
                    '/virtualContainerNodes',
            'action': 'getHypervisorNodes',
            'method': ['GET'],
        },
    ]

    @authentication_required()
    @cherrypy.tools.json_out()
    def getHardwareProfiles(self, **kwargs):
        tagspec = []

        if 'tag' in kwargs and kwargs['tag']:
            tagspec.extend(parse_tag_query_string(kwargs['tag']))

        try:
            if 'name' in kwargs and kwargs['name']:
                options = make_options_from_query_string(
                    kwargs['include']
                    if 'include' in kwargs else None, ['resourceadapter'])

                hardwareProfiles = TortugaObjectList(
                    [HardwareProfileManager().getHardwareProfile(
                        kwargs['name'], optionDict=options)])
            else:
                hardwareProfiles = \
                    HardwareProfileManager().getHardwareProfileList(
                        tags=tagspec)

            response = {
                'hardwareprofiles': hardwareProfiles.getCleanDict(),
            }
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API getHardwareProfiles() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @authentication_required()
    @cherrypy.tools.json_out()
    def getHardwareProfile(self, hwprofile_id):
        """
        TODO: implement support for optionDict through query string
        """
        try:
            hp = HardwareProfileManager().getHardwareProfileById(hwprofile_id)

            response = createHwProfileResponse(hp)
        except HardwareProfileNotFound as ex:
            self.handleException(ex)
            code = self.getTortugaStatusCode(ex)
            response = self.notFoundErrorResponse(str(ex), code)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API getHardwareProfile() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @authentication_required()
    def createHardwareProfile(self):
        """
        Create hardware profile
        """

        response = None

        postdata = cherrypy.request.json

        hwProfileDict = postdata['hardwareProfile']

        settingsDict = postdata['settingsDict'] \
            if 'settingsDict' in postdata else {}

        if 'osInfo' in settingsDict and settingsDict['osInfo']:
            settingsDict['osInfo'] = OsInfo.getFromDict(
                settingsDict['osInfo'])

        hwProfile = HardwareProfile.getFromDict(hwProfileDict)

        try:
            HardwareProfileManager().createHardwareProfile(
                hwProfile, settingsDict=settingsDict)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API createHardwareProfile() failed')

            self.getLogger().exception(ex)

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @authentication_required()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def deleteHardwareProfile(self, hardwareProfileName):
        """Delete hardware profile"""

        response = None

        try:
            HardwareProfileManager().deleteHardwareProfile(
                hardwareProfileName)
        except HardwareProfileNotFound as ex:
            self.handleException(ex)
            code = self.getTortugaStatusCode(ex)
            response = self.notFoundErrorResponse(str(ex), code)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API deleteHardwareProfile() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @authentication_required()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def updateHardwareProfile(self, hardwareProfileId):
        """
        Handle PUT to "hardwareprofiles/:(hardwareProfileId)"

        """
        response = None

        try:
            postdata = cherrypy.request.json
            hw_profile = HardwareProfile.getFromDict(postdata)
            hw_profile.setId(hardwareProfileId)
            hp_mgr = HardwareProfileManager()
            hp_mgr.updateHardwareProfile(hw_profile)

        except HardwareProfileNotFound as ex:
            self.handleException(ex)
            code = self.getTortugaStatusCode(ex)
            response = self.notFoundErrorResponse(str(ex), code)

        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API updateHardwareProfile() failed')
            self.handleException(ex)
            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @authentication_required()
    def getHypervisorNodes(self, hardwareProfileName):
        # self.getLogger().debug(
        #     'getHypervisorNodes: hardwareProfileName [%s]' % (
        #         hardwareProfileName))

        hpMgr = HardwareProfileManager()

        try:
            nodes = hpMgr.getHypervisorNodes(hardwareProfileName)

            # self.getLogger().debug('Number of nodes: %s' % len(nodes))

            response = nodes.getCleanDict()
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API getHypervisorNodes() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @authentication_required()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def addAdmin(self, hardwareProfileName, adminUsername):
        response = None

        hpMgr = HardwareProfileManager()

        try:
            self.__checkUser(hardwareProfileName)

            hpMgr.addAdmin(hardwareProfileName, adminUsername)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API addAdmin() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    @authentication_required()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def deleteAdmin(self, hardwareProfileName, adminUsername):
        response = None

        hpMgr = HardwareProfileManager()

        try:
            self.__checkUser(hardwareProfileName)

            hpMgr.deleteAdmin(hardwareProfileName, adminUsername)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API deleteAdmin() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)

    def __checkUser(self, hardwareProfileName):
        hpMgr = HardwareProfileManager()

        admins = hpMgr.getHardwareProfile(
            hardwareProfileName, {
                'admins': True,
            }).getAdmins()

        self.getLogger().debug(
            'Checking %s against %s' % (cherrypy.request.login, admins))

        for admin in admins:
            if admin.getUsername() == cherrypy.request.login:
                return

        raise UserNotAuthorized(
            'User %s is not a manager of %s' % (
                cherrypy.request.login, hardwareProfileName))

    @authentication_required()
    def copyHardwareProfile(self, srcHardwareProfileName, dstHardwareProfileName):
        response = None

        try:
            hpMgr = HardwareProfileManager()

            hpMgr.copyHardwareProfile(
                srcHardwareProfileName, dstHardwareProfileName)
        except HardwareProfileNotFound as ex:
            self.handleException(ex)
            code = self.getTortugaStatusCode(ex)
            response = self.notFoundErrorResponse(str(ex), code)
        except Exception as ex:
            self.getLogger().exception(
                'hardware profile WS API copyHardwareProfile() failed')

            self.handleException(ex)

            response = self.errorResponse(str(ex))

        return self.formatResponse(response)


def createHwProfileResponse(hp):
    response = {
        'hardwareprofile': hp.getCleanDict(),
    }

    return response


