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

# pylint: disable=too-few-public-methods

from sqlalchemy import Column, ForeignKey, Integer

from .base import ModelBase


class SoftwareProfileComponent(ModelBase):
    __tablename__ = 'softwareprofile_components'

    softwareProfileId = Column(Integer, ForeignKey('softwareprofiles.id'),
                               index=True, primary_key=True)
    componentId = Column(Integer, ForeignKey('components.id'),
                         index=True, primary_key=True)

    def __init__(self, softwareProfileId=None, componentId=None):
        super().__init__()

        self.softwareProfileId = softwareProfileId
        self.componentId = componentId
