#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker

import logging
console = logging.getLogger(__name__)


class DefaultConnectivityTracker(ConnectivityTracker):
    def __init__(self):
        console.warning(f"DefaultConnectivityTracker doesn't track anything.")

    def preserved(self, start: BgCube, final: BgCube, position: Coordinates) -> bool:
        return True

    def available(self, start: BgCube, final: BgCube) -> bool:
        return True

    def reserve(self, cube: BgCube, required: int):
        pass

    def connect(self, source: tuple[BgCube, Port], target: tuple[BgCube, Port]):
        pass

    def occlude(self, position: Coordinates):
        pass

    def report(self, verbose: bool = False):
        pass
