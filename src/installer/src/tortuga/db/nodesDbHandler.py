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

# pylint: disable=not-callable,no-member,multiple-statements,no-self-use

from typing import Dict, List, NoReturn, Optional, Tuple, Union

from sqlalchemy import and_, func, or_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session

from tortuga.db.globalParametersDbHandler import GlobalParametersDbHandler
from tortuga.db.hardwareProfilesDbHandler import HardwareProfilesDbHandler
from tortuga.db.nicsDbHandler import NicsDbHandler
from tortuga.db.softwareProfilesDbHandler import SoftwareProfilesDbHandler
from tortuga.db.softwareUsesHardwareDbHandler import \
    SoftwareUsesHardwareDbHandler
from tortuga.db.tortugaDbObjectHandler import TortugaDbObjectHandler
from tortuga.events.types import NodeStateChanged
from tortuga.exceptions.nodeNotFound import NodeNotFound
from tortuga.exceptions.nodeSoftwareProfileLocked import \
    NodeSoftwareProfileLocked
from tortuga.exceptions.nodeTransferNotValid import NodeTransferNotValid
from tortuga.exceptions.operationFailed import OperationFailed
from tortuga.exceptions.profileMappingNotAllowed import \
    ProfileMappingNotAllowed
from tortuga.objects.node import Node as TortugaNode
from tortuga.resourceAdapter import resourceAdapterFactory

from .models.hardwareProfile import HardwareProfile
from .models.nic import Nic
from .models.node import Node
from .models.softwareProfile import SoftwareProfile

Tags = List[Tuple[str, str]]


class NodesDbHandler(TortugaDbObjectHandler):
    """
    This class handles nodes table.
    """

    NODE_STATE_INSTALLED = 'Installed'
    NODE_STATE_DELETED = 'Deleted'

    def __init__(self):
        TortugaDbObjectHandler.__init__(self)

        self._nicsDbHandler = NicsDbHandler()
        self._hardwareProfilesDbHandler = HardwareProfilesDbHandler()
        self._softwareProfilesDbHandler = SoftwareProfilesDbHandler()
        self._softwareUsesHardwareDbHandler = SoftwareUsesHardwareDbHandler()
        self._globalParametersDbHandler = GlobalParametersDbHandler()

    def __isNodeLocked(self, dbNode: Node) -> bool:
        return dbNode.lockedState != 'Unlocked'

    def __isNodeHardLocked(self, dbNode: Node) -> bool:
        return dbNode.lockedState == 'HardLocked'

    def __isNodeSoftLocked(self, dbNode: Node) -> bool:
        return dbNode.lockedState == 'SoftLocked'

    def __getNodeState(self, dbNode: Node) -> bool:
        return dbNode.state

    def __isNodeStateDeleted(self, node: Node) -> bool:
        return self.__getNodeState(node) == NodesDbHandler.NODE_STATE_DELETED

    def __isNodeStateInstalled(self, dbNode: Node) -> bool:
        return self.__getNodeState(dbNode) == \
            NodesDbHandler.NODE_STATE_INSTALLED

    def getNode(self, session: Session, name: str) -> Node:
        """
        Return node.

        Raises:
            NodeNotFound
        """

        try:
            if '.' in name:
                # Attempt exact match on fully-qualfied name
                return session.query(Node).filter(
                    func.lower(Node.name) == name.lower()).one()

            # 'name' is short host name; attempt to match on either short
            # host name or any host starting with same host name
            return session.query(Node).filter(
                or_(func.lower(Node.name) == name.lower(),
                    func.lower(Node.name).like(name.lower() + '.%'))).one()
        except NoResultFound:
            raise NodeNotFound("Node [%s] not found" % (name))

    def getNodesByTags(self, session: Session,
                       tags: Optional[Tags] = None):
        """'tags' is a list of (key, value) tuples representing tags.
        tuple may also contain only one element (key,)
        """

        searchspec = []

        # iterate over list of tag tuples making SQLAlchemy search
        # specification
        for tag in tags:
            if len(tag) == 2:
                # Match tag 'name' and 'value'
                searchspec.append(and_(Node.tags.any(name=tag[0]),
                                       Node.tags.any(value=tag[1])))
            else:
                # Match tag 'name' only
                searchspec.append(Node.tags.any(name=tag[0]))

        return session.query(Node).filter(or_(*searchspec)).all()

    def getNodesByAddHostSession(self, session: Session, ahSession: str) \
            -> List[Node]:
        """
        Get nodes by add host session
        Returns a list of nodes
        """

        self.getLogger().debug(
            'getNodesByAddHostSession(): ahSession [%s]' % (ahSession))

        return session.query(Node).filter(
            Node.addHostSession == ahSession).order_by(Node.name).all()

    def getNodesByNameFilter(self, session: Session,
                             filter_spec: Union[str, list]) -> List[Node]:
        """
        Filter follows SQL "LIKE" semantics (ie. "something%")

        Returns a list of Node
        """

        filter_spec_list = [filter_spec] \
            if not isinstance(filter_spec, list) else filter_spec

        node_filter = []

        for filter_spec_item in filter_spec_list:
            if '.' not in filter_spec_item:
                # Match exactly (ie. "hostname-01")
                node_filter.append(Node.name.like(filter_spec_item))

                # Match host name only (ie. "hostname-01.%")
                node_filter.append(Node.name.like(filter_spec_item + '.%'))

                continue

            # Match fully-qualified node names exactly
            # (ie. "hostname-01.domain")
            node_filter.append(Node.name.like(filter_spec_item))

        return session.query(Node).filter(or_(*node_filter)).all()

    def getNodeById(self, session: Session, _id: int) -> Node:
        """
        Return node.

        Raises:
            NodeNotFound
        """

        self.getLogger().debug('Retrieving node by ID [%s]' % (_id))

        dbNode = session.query(Node).get(_id)

        if not dbNode:
            raise NodeNotFound('Node ID [%s] not found.' % (_id))

        return dbNode

    def getNodeByIp(self, session: Session, ip: str) -> Node:
        """
        Raises:
            NodeNotFound
        """

        self.getLogger().debug('Retrieving node by IP [%s]' % (ip))

        try:
            return session.query(Node).join(Nic).filter(Nic.ip == ip).one()
        except NoResultFound:
            raise NodeNotFound(
                'Node with IP address [%s] not found.' % (ip))

    def getNodeList(self, session: Session,
                    softwareProfile: Optional[str] = None,
                    tags: Tags = None) -> List[Node]:
        """
        Get sorted list of nodes from the db.

        Raises:
            SoftwareProfileNotFound
        """

        self.getLogger().debug('getNodeList()')

        if softwareProfile:
            dbSoftwareProfile = self._softwareProfilesDbHandler.\
                getSoftwareProfile(session, softwareProfile)

            return dbSoftwareProfile.nodes

        searchspec = []

        if tags:
            # Build searchspec from specified tags
            for tag in tags:
                if len(tag) == 2:
                    searchspec.append(
                        and_(Node.tags.any(name=tag[0]),
                             Node.tags.any(value=tag[1])))
                else:
                    searchspec.append(Node.tags.any(name=tag[0]))

        return session.query(Node).filter(
            or_(*searchspec)).order_by(Node.name).all()

    def getNodeListByNodeStateAndSoftwareProfileName(
            self, session: Session, nodeState: str,
            softwareProfileName: str) -> List[Node]:
        """
        Get list of nodes from the db.
        """

        self.getLogger().debug(
            'Retrieving nodes with state [%s] from software'
            ' profile [%s]' % (nodeState, softwareProfileName))

        return session.query(Node).join(SoftwareProfile).filter(and_(
            SoftwareProfile.name == softwareProfileName,
            Node.state == nodeState)).all()

    def evacuateChildren(self, session: Session, dbNode: Node):
        swProfile = dbNode.softwareprofile
        if not swProfile:
            return

        # Migrate or idle any children
        remainingNodeList = self.__getRemainingNodeList(dbNode, swProfile)

        self.__migrateOrIdleChildren(
            session, dbNode, remainingNodeList)

    def updateNode(self, session: Session, node: Node,
            updateNodeRequest: dict) -> NoReturn:
        """Calls updateNode() method of resource adapter"""

        adapter = self.__getResourceAdapter(node.hardwareprofile)

        adapter.updateNode(session, node, updateNodeRequest)

    def transferNode(self, session: Session, dbNodes: List[Node],
                     newSoftwareProfile: SoftwareProfile,
                     bForce: bool = False): \
            # pylint: disable=unused-argument
        """
        Raises:
            NodeNotFound
        """

        results = []

        for node in dbNodes:
            if node.hardwareprofile not in newSoftwareProfile.\
                    hardwareprofiles:
                raise ProfileMappingNotAllowed(
                    'Node [%s] belongs to hardware profile [%s] which is'
                    ' not allowed to use software profile [%s]' % (
                        node.name, node.hardwareprofile.name,
                        newSoftwareProfile.name))

            # Check to see if the node is already using the requested
            # software profile
            if not bForce and not self.__isNodeStateInstalled(node):
                raise NodeTransferNotValid(
                    "Can't transfer node [%s], because of its state [%s]" % (
                        node.name, node.state))

            # Check to see if the node is already using the requested
            # software profile
            if node.softwareprofile == newSoftwareProfile:
                msg = 'Node [%s] is already in software profile [%s]' % (
                    node.name, newSoftwareProfile.name)

                self.getLogger().info(msg)

                raise NodeTransferNotValid(msg)

            self.getLogger().debug(
                'transferNode: Transferring node [%s] to'
                ' software profile [%s]' % (
                    node.name, newSoftwareProfile.name))

            # Check to see if the node is locked
            if self.__isNodeLocked(node):
                raise NodeSoftwareProfileLocked(
                    "Node [%s] can't be transferred while locked" % (
                        node.name))

            result = {
                'prev_softwareprofile': node.softwareprofile,
                'node': node,
            }

            node.softwareprofile = newSoftwareProfile

            results.append(result)

        return results

    def __isNodeTransferrable(self, dbNode: Node) -> bool:
        # Only nodes that are not locked and in Installed state are
        # eligible for transfer.
        return not self.__isNodeLocked(dbNode) and \
            self.__isNodeStateInstalled(dbNode)

    def __getNodeTransferCandidates(
            self, dbSrcSoftwareProfile: SoftwareProfile,
            dbDstSoftwareProfile: SoftwareProfile, compare_func):
        """
        Helper method for determining which nodes should be considered for
        transfer.
        """
        if dbSrcSoftwareProfile:
            # Find all nodes within this software profile that are in the
            # same hardware profile as the destination software profile.
            # Exclude all nodes that are HardLocked or not in "Installed"
            # state.
            return [
                dbNode for dbNode in dbSrcSoftwareProfile.nodes
                if dbNode.hardwareprofile in
                dbDstSoftwareProfile.hardwareprofiles and
                compare_func(dbNode)]

        # Find all nodes that are in the same hardware profile(s) as
        # the destination software profile. Exclude all nodes that are
        # HardLocked or not in "Installed" state.
        return [
            dbNode for dbHardwareProfile in
            dbDstSoftwareProfile.hardwareprofiles
            for dbNode in dbHardwareProfile.nodes
            if dbNode.softwareprofile != dbDstSoftwareProfile and
            compare_func(dbNode)]

    def __getTransferrableNodes(
            self, dbSrcSoftwareProfile: SoftwareProfile,
            dbDstSoftwareProfile: SoftwareProfile) -> List[Node]:
        """Return list of Unlocked nodes"""
        return self.__getNodeTransferCandidates(
            dbSrcSoftwareProfile, dbDstSoftwareProfile,
            self.__isNodeTransferrable)

    def __getSoftLockedNodes(
            self, dbSrcSoftwareProfile: SoftwareProfile,
            dbDstSoftwareProfile: SoftwareProfile) -> List[Node]:
        """Return list of SoftLocked nodes"""
        return self.__getNodeTransferCandidates(
            dbSrcSoftwareProfile, dbDstSoftwareProfile,
            self.__isNodeSoftLocked)

    def transferNodes(self, session: Session,
                      dbSrcSoftwareProfile: SoftwareProfile,
                      dbDstSoftwareProfile: SoftwareProfile,
                      count: int, bForce: bool = False): \
            # pylint: disable=unused-argument
        """
        Raises:
            NodeTransferNotValid
        """

        # First sanity check... ensure there is actually something to do.
        if dbSrcSoftwareProfile == dbDstSoftwareProfile:
            raise NodeTransferNotValid(
                'Source and destination software profiles are the same')

        # Get list of Unlocked nodes
        dbUnlockedNodeList = self.__getTransferrableNodes(
            dbSrcSoftwareProfile, dbDstSoftwareProfile)

        # If the source software profile is specified, only use nodes from
        # it, otherwise get list of nodes for compatible hardware profile.

        nUnlockedNodes = len(dbUnlockedNodeList)

        if nUnlockedNodes < count:
            # Not enough nodes available, include SoftLocked nodes as well.

            dbSoftLockedNodes = self.__getSoftLockedNodes(
                dbSrcSoftwareProfile, dbDstSoftwareProfile)

            nSoftLockedNodes = len(dbSoftLockedNodes)

            if nSoftLockedNodes == 0:
                self.getLogger().debug(
                    '[%s] No softlocked nodes available' % (
                        self.__module__))

            nNodesAvailable = nUnlockedNodes + nSoftLockedNodes

            if nNodesAvailable == 0:
                # Use a different error message to be friendly...
                msg = 'No nodes available to transfer'

                self.getLogger().error(msg)

                raise NodeTransferNotValid(msg)

            if nNodesAvailable < count:
                # We still do not have enough nodes to transfer.
                msg = ('Insufficient nodes available to transfer;'
                       ' %d available, %d requested' % (
                           nNodesAvailable, count))

                self.getLogger().info(msg)

                raise NodeTransferNotValid(msg)

            nRequiredNodes = count - nUnlockedNodes

            dbNodeList = dbUnlockedNodeList + \
                dbSoftLockedNodes[:nRequiredNodes]
        else:
            dbNodeList = dbUnlockedNodeList[:count]

        return self.transferNode(session, dbNodeList, dbDstSoftwareProfile)

    def idleNode(self, session: Session, dbNodes: List[Node]):
        """
        Raises:
            NodeAlreadyIdle
            NodeSoftwareProfileLocked
        """

        idleSoftwareProfilesDict = {}
        d = {}

        results = {
            'NodeAlreadyIdle': [],
            'NodeSoftwareProfileLocked': [],
            'success': [],
        }

        # Iterate over all nodes in the node spec, idling each one
        for dbNode in dbNodes:
            # Check to see if the node is already idle
            if dbNode.isIdle:
                results['NodeAlreadyIdle'].append(dbNode)

                continue

            hardware_profile = dbNode.hardwareprofile

            # Get the software profile
            # dbSoftwareProfile = dbNode.softwareprofile

            # Check to see if the node is locked
            if self.__isNodeLocked(dbNode):
                results['NodeSoftwareProfileLocked'].append(dbNode)

                continue

            if hardware_profile.name not in d:
                # Get the ResourceAdapter
                adapter = self.__getResourceAdapter(hardware_profile)

                d[hardware_profile.name] = {
                    'adapter': adapter,
                    'nodes': [],
                }
            else:
                adapter = d[hardware_profile.name]['adapter']

            # Migrate or idle any children
            # TODO: this really isn't necessary anymore. We do not
            # provision hypervisors.
            # remainingNodeList = self.__getRemainingNodeList(
            #     session, dbNode, dbSoftwareProfile)

            # self.__migrateOrIdleChildren(
            #     session, dbNode, remainingNodeList)

            # Call suspend action extension
            if adapter.suspendActiveNode(dbNode):
                # Change node status in the DB
                dbNode.isIdle = True

                continue

            # If we could not suspend the node, shut it down
            if dbNode.softwareprofile.name not in idleSoftwareProfilesDict:
                idleSoftwareProfilesDict[dbNode.softwareprofile.name] = {
                    'idled': [],
                    'added': [],
                }

            idleSoftwareProfilesDict[dbNode.
                                     softwareprofile.
                                     name]['idled'].append(dbNode)

            # Idle the Node
            if hardware_profile.idlesoftwareprofile:
                self.getLogger().debug(
                    'Idling node [%s] to idle software profile [%s]' % (
                        dbNode.name,
                        hardware_profile.idlesoftwareprofile.name))

                idle_profile_name = \
                    hardware_profile.idlesoftwareprofile.name

                # If the idle software profile is defined, include it in
                # the refresh information for this node.
                if idle_profile_name not in idleSoftwareProfilesDict:
                    idleSoftwareProfilesDict[idle_profile_name] = {
                        'idled': [],
                        'added': [],
                    }

                idleSoftwareProfilesDict[
                    hardware_profile.idlesoftwareprofile.name][
                        'added'].append(dbNode)

            dbNode.softwareprofile = hardware_profile.idlesoftwareprofile

            # The idle status has to go with this commit or we are
            # inconsistent...
            dbNode.isIdle = True

            # session.commit()

            # TODO: fix this at some point. Basically, it is a list of
            # nodes that have been successfully idled.
            d[hardware_profile.name]['nodes'].append(dbNode)

        events_to_fire = []

        # Call idle action extension
        for nodeDetails in d.values():
            # Call resource adapter
            nodeState = nodeDetails['adapter'].\
                idleActiveNode(nodeDetails['nodes'])

            # Node state is consistent for all nodes within the same
            # hardware profile.
            for dbNode in nodeDetails['nodes']:
                event_data = None
                #
                # If the node state is changing, then we need to be prepared
                # to fire an event after the data has been persisted.
                #
                if dbNode.state != nodeState:
                    event_data = {'previous_state': dbNode.state}

                dbNode.state = nodeState

                #
                # Serialize the node for the event, if required
                #
                if event_data:
                    event_data['node'] = TortugaNode.getFromDbDict(
                        dbNode.__dict__).getCleanDict()
                    events_to_fire.append(event_data)

            # Add idled node to 'success' list
            results['success'].extend(nodeDetails['nodes'])

        session.commit()

        #
        # Fire node state change events
        #
        for event in events_to_fire:
            NodeStateChanged.fire(node=event['node'],
                                  previous_state=event['previous_state'])

        return results

    def migrateNode(self, session: Session, nodeName: str,
                    remainingNodeList: List[Node], liveMigrate: bool):
        dbNode = self.getNode(session, nodeName)

        # Get the ResourceAdapter
        adapter = self.__getResourceAdapter(dbNode.hardwareprofile)

        # Try to migrate the Node
        self.getLogger().debug(
            'Attempting to migrate node [%s]' % (dbNode.name))

        # Call migrate action extension
        adapter.migrateNode(dbNode, remainingNodeList, liveMigrate)

    def activateNode(self, session: Session, dbNodes: List[Node],
                     dbDstSoftwareProfile: SoftwareProfile = None):
        d = {}

        activateNodeResults = {
            'NodeAlreadyActive': [],
            'SoftwareProfileNotFound': [],
            'InvalidArgument': [],
            'NodeSoftwareProfileLocked': [],
            'ProfileMappingNotAllowed': [],
            'success': [],
        }

        activateSoftwareProfilesDict = {}

        for dbNode in dbNodes:
            self.getLogger().debug(
                'Attempting to activate node [%s]' % (dbNode.name))

            # Check to see if the node is already active
            if not dbNode.isIdle:
                # Attempting to activate an "active" node
                activateNodeResults['NodeAlreadyActive'].append(dbNode)

                continue

            # Flag to indicate if the node has been activated to a software
            # profile that differs from the software profile that it was
            # previously in
            softwareProfileChanged = False

            # If the node is only suspended and has a software profile, no
            # need to force the user to tell us what the software profile
            # is.
            if not dbDstSoftwareProfile:
                if not dbNode.softwareprofile:
                    # We don't know what to do with the specified node.
                    # Destination software profile not specified and node
                    # does not have an associated software profile.

                    activateNodeResults['SoftwareProfileNotFound'].append(
                        dbNode)

                    continue

                dbSoftwareProfile = dbNode.softwareprofile
            else:
                softwareProfileChanged = dbNode.softwareprofile is None or \
                    dbNode.softwareprofile != dbDstSoftwareProfile

                dbSoftwareProfile = dbNode.softwareprofile \
                    if not softwareProfileChanged else dbDstSoftwareProfile

            if dbSoftwareProfile and dbSoftwareProfile.isIdle:
                # Attempt to activate node into an idle software profile
                activateNodeResults['InvalidArgument'].append(dbNode)

                continue

            # Check to see if the node is locked
            if self.__isNodeLocked(dbNode):
                # Locked nodes cannot be activated
                activateNodeResults['NodeSoftwareProfileLocked'].append(
                    dbNode)

                continue

            if dbSoftwareProfile and \
                    dbNode.hardwareprofile not in dbSoftwareProfile.\
                    hardwareprofiles:
                # This result list is a tuple of (node, hardwareprofile
                # name, software profile name) for reporting the error back
                # to the caller.
                activateNodeResults['ProfileMappingNotAllowed'].\
                    append((dbNode,
                            dbNode.hardwareprofile.name,
                            dbSoftwareProfile.name,))

                continue

            # Migrate or idle any children
            # remainingNodeList = self.__getRemainingNodeList(
            #     session, dbNode, dbSoftwareProfile)

            # self.__migrateOrIdleChildren(session, dbNode, remainingNodeList)

            # Activate the Node
            self.getLogger().debug(
                'Activating node [%s] to software profile [%s]' % (
                    dbNode.name, dbSoftwareProfile.name))

            if dbNode.softwareprofile:
                activateSoftwareProfilesDict[dbNode.softwareprofile.name] = {
                    'removed': [dbNode],
                }

            if softwareProfileChanged and dbSoftwareProfile.name:
                activateSoftwareProfilesDict[dbSoftwareProfile.name] = {
                    'activated': [dbNode],
                }

            dbNode.softwareprofile = dbSoftwareProfile

            session.commit()

            if dbNode.hardwareprofile.name not in d:
                # Get the ResourceAdapter
                adapter = self.__getResourceAdapter(dbNode.hardwareprofile)

                d[dbNode.hardwareprofile.name] = {
                    'adapter': adapter,
                    'nodes': [],
                }

            d[dbNode.hardwareprofile.name]['nodes'].append(
                (dbNode, dbSoftwareProfile.name, softwareProfileChanged))

        # 'd' dict is indexed by hardware profile
        for nodesDetail in d.values():
            # Iterate over all idled nodes
            for dbNode, softwareProfileName, bSoftwareProfileChanged in \
                    nodesDetail['nodes']:
                nodesDetail['adapter'].activateIdleNode(
                    dbNode, softwareProfileName,
                    bSoftwareProfileChanged)

                dbNode.isIdle = False

                activateNodeResults['success'].append(dbNode)

        session.commit()

        return activateNodeResults

    def __processNodeList(self, dbNodes: List[Node]) \
            -> Dict[HardwareProfile, Dict[str, list]]:
        """
        Returns dict indexed by hardware profile, each with a list of
        nodes in the hardware profile
        """

        d = {}

        for dbNode in dbNodes:
            if dbNode.hardwareprofile not in d:
                d[dbNode.hardwareprofile] = {
                    'nodes': [],
                }

            d[dbNode.hardwareprofile]['nodes'].append(dbNode)

        return d

    def startupNode(self, session: Session, nodespec: str,
                    remainingNodeList: List[Node] = None,
                    bootMethod: str = 'n') -> NoReturn: \
            # pylint: disable=unused-argument
        nodes = nodespec if isinstance(nodespec, list) else [nodespec]

        # Break list of nodes into dict keyed on hardware profile
        nodes_dict = self.__processNodeList(nodes)

        for dbHardwareProfile, detailsDict in nodes_dict.items():
            # Get the ResourceAdapter
            adapter = self.__getResourceAdapter(dbHardwareProfile)

            # Call startup action extension
            adapter.startupNode(
                detailsDict['nodes'],
                remainingNodeList=remainingNodeList or [],
                tmpBootMethod=bootMethod)

    def shutdownNode(self, session: Session, nodespec: str,
                     bSoftShutdown: bool = False) -> NoReturn: \
            # pylint: disable=unused-argument
        nodeList = nodespec if isinstance(nodespec, list) else [nodespec]

        d = self.__processNodeList(nodeList)

        for dbHardwareProfile, detailsDict in d.items():
            # Get the ResourceAdapter
            adapter = self.__getResourceAdapter(dbHardwareProfile)

            # Call shutdown action extension
            adapter.shutdownNode(detailsDict['nodes'], bSoftShutdown)

    def rebootNode(self, session: Session, nodespec: str,
                   bSoftReset: bool = False) -> NoReturn: \
            # pylint: disable=unused-argument
        nodeList = nodespec if isinstance(nodespec, list) else [nodespec]

        d = self.__processNodeList(nodeList)

        for dbHardwareProfile, detailsDict in d.items():
            adapter = self.__getResourceAdapter(dbHardwareProfile)

            # Call reboot action extension
            adapter.rebootNode(detailsDict['nodes'], bSoftReset)

    def checkpointNode(self, session: Session, nodeName: str) -> NoReturn:
        # Get the Node
        dbNode = self.getNode(session, nodeName)

        # Get the ResourceAdapter
        adapter = self.__getResourceAdapter(dbNode.hardwareprofile)

        # Call checkpoint action extension
        adapter.checkpointNode(dbNode)

    def revertNodeToCheckpoint(self, session: Session, nodeName: str) \
            -> NoReturn:
        dbNode = self.getNode(session, nodeName)

        # Get the ResourceAdapter
        adapter = self.__getResourceAdapter(dbNode.hardwareprofile)

        # Call revert to checkpoint action extension
        adapter.revertNodeToCheckpoint(dbNode)

    def __getResourceAdapter(self, hardwareProfile: HardwareProfile):
        """
        Raises:
            OperationFailed
        """

        if not hardwareProfile.resourceadapter:
            raise OperationFailed(
                'Hardware profile [%s] does not have an associated'
                ' resource adapter' % (hardwareProfile.name))

        return resourceAdapterFactory.get_api(
            hardwareProfile.resourceadapter.name) \
            if hardwareProfile.resourceadapter else None

    # def __migrateOrIdleChildren(self, session, dbNode, remainingNodeList):
    #     remainingNodeNameList = [
    #         remainingNode.name for remainingNode in remainingNodeList]
    #
    #     try:
    #         for dbChildNode in dbNode.children:
    #             migrateSucessful = False
    #
    #             if remainingNodeNameList:
    #                 try:
    #                     self.migrateNode(
    #                         session, dbChildNode.name,
    #                         remainingNodeNameList, True)
    #
    #                     migrateSucessful = True
    #                 except Exception, ex:
    #                     self.getLogger().debug(
    #                         '__migrateOrIdleChildren: Failed live migrate'
    #                         ' on %s: %s' % (dbChildNode.name, ex))
    #
    #                     migrateSucessful = False
    #
    #             if not migrateSucessful:
    #                 try:
    #                     self.idleNode(session, dbChildNode.name)
    #
    #                     self.getLogger().debug(
    #                         'Idled node [%s]' % (dbChildNode.name))
    #                 except Exception, ex:
    #                     self.getLogger().error(
    #                         '__migrateOrIdleChildren: Exception: %s on'
    #                         ' child' % (ex, dbChildNode.name))
    #             else:
    #                 self.getLogger().debug(
    #                     'Migrated node [%s]' % (dbChildNode.name))
    #     except Exception, ex:
    #         self.getLogger().error(
    #             '__migrateOrIdleChildren: Exception: %s' % (ex))

    def __getRemainingNodeList(self, dbnode: Node,
                               dbSoftwareProfile: SoftwareProfile) \
            -> List[Node]:
        if not dbSoftwareProfile:
            return []

        return list(set(dbSoftwareProfile.nodes) - set([dbnode]))

    def getNodesByNodeState(self, session: Session, state: str) -> List[Node]:
        return session.query(Node).filter(Node.state == state).all()

    def getNodesByMac(self, session: Session, usedMacList: List[str]) \
            -> List[Node]:
        if not usedMacList:
            return []

        return session.query(Node).join(Nic).filter(
            Nic.mac.in_(usedMacList)).all()
