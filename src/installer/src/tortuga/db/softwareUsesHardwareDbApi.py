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

from sqlalchemy.orm.session import Session
from tortuga.db.softwareProfilesDbHandler import SoftwareProfilesDbHandler
from tortuga.db.softwareUsesHardwareDbHandler import \
    SoftwareUsesHardwareDbHandler
from tortuga.db.tortugaDbApi import TortugaDbApi
from tortuga.exceptions.tortugaException import TortugaException
from tortuga.objects.tortugaObject import TortugaObjectList


class SoftwareUsesHardwareDbApi(TortugaDbApi):
    """
    SoftwareUsesHardware DB API class.
    """

    def __init__(self):
        TortugaDbApi.__init__(self)

        self._softwareProfilesDbHandler = SoftwareProfilesDbHandler()
        self._softwareUsesHardwareDbHandler = \
            SoftwareUsesHardwareDbHandler()

    def getSoftwareUsesHardwareList(self, session: Session):
        """
        Get list of all mappings

            Returns:
                [softwareProfileId, hardwareProfileId]
            Throws:
                DbError
        """

        try:
            dbMappings = self._softwareUsesHardwareDbHandler.\
                getSoftwareUsesHardwareList(session)

            mappingList = TortugaObjectList()

            for dbMapping in dbMappings:
                mappingList.append((dbMapping.softwareProfileId,
                                    dbMapping.hardwareProfileId))

            return mappingList
        except TortugaException:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise

    def getAllowedHardwareProfilesBySoftwareProfileName(
            self, session: Session, softwareProfileName):
        """
        Get list of hardware profiles for the given software profile

            Returns:
                [hardwareProfileId]
            Throws:
                DbError
        """

        try:
            dbMappings = self._softwareUsesHardwareDbHandler.\
                getAllowedHardwareProfilesBySoftwareProfileName(
                    session, softwareProfileName)

            mappingList = TortugaObjectList()

            for dbMapping in dbMappings:
                mappingList.append(dbMapping.hardwareProfileId)

            return mappingList
        except TortugaException:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise
