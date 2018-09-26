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
from json import dumps
from datetime import date
from typing import Generator
from tortuga.objects.tortugaObject import TortugaObject


class Costing(TortugaObject):
    """
    Handle costing of resource adapters
    and physical hardware.
    """
    def __init__(start: date, end: date) -> None:
        """

        :param start: Datetime start of report
        :param end: Datetime end of report
        :returns: None
        """
        self.start = start
        self.end = end

    def _get(self) -> Generator[dict, None, None]:
        """
        Implement retrieval of data from 
        provider and format as 

        {
            'date': date object,
            'cost': float,
            'currency': string
        }

        :returns: Generator Dictionary
        """
        raise NotImplementedError

    def json(self) -> Generator[str, None, None]:
        """
        Format to JSON.

        :returns: Generator String
        """
        for day in self._get():
            day['date'] = day['date'].start.strftime('%Y-%m-%d')
            yield dumps(day)