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

import mock
import pytest

import tortuga.kit.registry
import tortuga.os_utility.osUtility
from tortuga.exceptions.nodeTransferNotValid import NodeTransferNotValid
from tortuga.kit.actions.manager import KitActionsManager
from tortuga.node.nodeApi import NodeApi
from tortuga.events.types import NodeStateChanged
from .osUtilityMock import get_os_object_factory


def get_kit_installer(kit_spec):
    return 'xxxx'


@mock.patch('tortuga.os_utility.osUtility.getOsObjectFactory',
            side_effect=get_os_object_factory)
@mock.patch.object(KitActionsManager, 'refresh')
@mock.patch('tortuga.softwareprofile.softwareProfileManager.get_kit_installer',
            side_effort=get_kit_installer)
@mock.patch.object(NodeStateChanged, 'fire')
class TestTransferNode:
    def test_basic(self, node_state_change_object, get_kit_installer_function,
                   MockClass1, get_os_object_factory_function, dbm):
        """
        Transfer a single node
        """

        name = 'compute-01'

        with dbm.session() as session:
            # xfer node 'compute-01' to 'compute2' software profile
            result = NodeApi().transferNodes(
                session, 'compute2', nodespec=name)

            # get node after xfer
            node = NodeApi().getNode(session, name)

            # validate new software profile
            assert node.getSoftwareProfile().getName() == 'compute2'

            # validate state (which is fudged above)
            assert node.getState() != 'Installed'

            # update status from 'Expired' to 'Installed' to allow xfer
            NodeApi().updateNodeStatus(session, name, state='Installed')

            # ensure event fired to indicate node state change
            node_state_change_object.assert_called()

            # xfer node back to 'compute' software profile
            NodeApi().transferNodes(session, 'compute', nodespec=name)

            NodeApi().updateNodeStatus(session, name, state='Installed')

            node = NodeApi().getNode(session, name)

            assert node.getSoftwareProfile().getName() == 'compute'

    def test_invalid_transfer(self, node_state_change_object,
                              get_kit_installer_function, MockClass1,
                              get_os_object_factory_function, dbm):
        """
        Attempt to transfer node to current software profile
        """

        with dbm.session() as session:
            with pytest.raises(NodeTransferNotValid):
                NodeApi().transferNodes(
                    session, 'compute', nodespec='compute-02.private')
