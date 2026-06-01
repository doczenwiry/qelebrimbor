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

import logging
from typing import Iterator

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.reach import Reach
from qelebrimbor.helpers.blockgraph import Move
from qelebrimbor.helpers.spacetime import Step

console = logging.getLogger(__name__)


class ColorlessRing:
    def __init__(self) -> None:
        self.__positions: list[Coordinates] = list()
        self.__occupied: set[Coordinates] = set()

    @property
    def anchor(self) -> Coordinates:
        return self.__positions[0]

    @property
    def terminal(self) -> Coordinates:
        return self.__positions[-1]

    @property
    def volume(self) -> int:
        return len(self.__positions)

    @property
    def positions(self) -> Iterator[Coordinates]:
        return iter(self.__positions)

    @property
    def distance(self) -> int:
        return self.anchor.get_manhattan_distance(self.terminal)

    @property
    def steps(self) -> list[Step]:
        steps: list[Step] = list()
        for index in range(1, self.volume):
            steps.append(Step(self.__positions[index] - self.__positions[index - 1]))
        if self.closed():
            steps.append(Step(self.__positions[0] - self.__positions[-1]))
        return steps

    @property
    def moves(self) -> list[Move]:
        moves: list[Move] = list()
        steps: list[Step] = self.steps
        local_forward: Step = steps[0]
        local_up: Step = next(local_forward.orthogonals())
        local_left: Step = local_up.cross(local_forward)

        # By convention, we consider the first move to be Forward.
        moves.append(Move.FORWARD)
        for i in range(1, len(steps)):
            console.debug(f"Locals : LF:{local_forward}/LL:{local_left}/LU:{local_up}")
            console.debug(
                f"> Step {steps[i]} : {steps[i].dot(local_forward)} {steps[i].dot(local_left)} {steps[i].dot(local_up)}"
            )
            if steps[i] == local_forward:
                moves.append(Move.FORWARD)
                continue

            sll = steps[i].dot(local_left)
            if sll != 0:
                if sll == +1:
                    moves.append(Move.LEFT)
                elif sll == -1:
                    moves.append(Move.RIGHT)
                local_forward, local_left = sll * local_left, -sll * local_forward
                continue

            slu = steps[i].dot(local_up)
            if slu != 0:
                if slu == +1:
                    moves.append(Move.UP)
                elif slu == -1:
                    moves.append(Move.DOWN)
                local_forward, local_up = slu * local_up, -slu * local_forward

        return moves

    def equivalent(self, other: ColorlessRing) -> bool:
        return self.__equivalent(other) or self.__equivalent(other, reverse=True)

    def __equivalent(self, other: ColorlessRing, reverse: bool = False) -> bool:
        moves_s: list[Move] = self.moves
        steps_o: list[Step] = other.steps
        if reverse:
            steps_o = list(reversed(steps_o))

        for lu in steps_o[0].orthogonals():
            moves_o: list[Move] = list()
            local_forward: Step = steps_o[0]
            local_up: Step = lu
            console.debug(f"LF:{local_forward}/LU:{local_up}")
            local_left: Step = local_up.cross(local_forward)

            # By convention, we consider the first move to be Forward.
            moves_o.append(Move.FORWARD)
            for i in range(1, len(steps_o)):
                console.debug(f"Locals : LF:{local_forward}/LL:{local_left}/LU:{local_up}")
                console.debug(f"> Step {steps_o[i]}")
                if steps_o[i] == local_forward:
                    moves_o.append(Move.FORWARD)
                    continue

                sll = steps_o[i].dot(local_left)
                if sll != 0:
                    if sll == +1:
                        moves_o.append(Move.LEFT)
                    elif sll == -1:
                        moves_o.append(Move.RIGHT)
                    local_forward, local_left = sll * local_left, -sll * local_forward
                    continue

                slu = steps_o[i].dot(local_up)
                if slu != 0:
                    if slu == +1:
                        moves_o.append(Move.UP)
                    elif slu == -1:
                        moves_o.append(Move.DOWN)
                    local_forward, local_up = slu * local_up, -slu * local_forward

            if moves_s == moves_o:
                return True

        return False

    def quad_moves(self, reverse: bool = False) -> list[list[Move]]:
        quad_moves: list[list[Move]] = list()
        steps: list[Step] = self.steps
        if reverse:
            steps = list(reversed(steps))

        console.debug(f"LF:{steps[0]} : {list(steps[0].orthogonals())}")
        for lu in steps[0].orthogonals():
            moves: list[Move] = list()
            local_forward: Step = steps[0]
            local_up: Step = lu
            console.debug(f"LF:{local_forward}/LU:{local_up}")
            local_left: Step = local_up.cross(local_forward)

            # By convention, we consider the first move to be Forward.
            moves.append(Move.FORWARD)
            for i in range(1, len(steps)):
                console.debug(f"Locals : LF:{local_forward}/LL:{local_left}/LU:{local_up}")
                console.debug(f"> Step {steps[i]}")
                if steps[i] == local_forward:
                    moves.append(Move.FORWARD)
                    continue

                sll = steps[i].dot(local_left)
                if sll != 0:
                    if sll == +1:
                        moves.append(Move.LEFT)
                    elif sll == -1:
                        moves.append(Move.RIGHT)
                    local_forward, local_left = sll * local_left, -sll * local_forward
                    continue

                slu = steps[i].dot(local_up)
                if slu != 0:
                    if slu == +1:
                        moves.append(Move.UP)
                    elif slu == -1:
                        moves.append(Move.DOWN)
                    local_forward, local_up = slu * local_up, -slu * local_forward

            quad_moves.append(moves)

        return quad_moves

    def rotated(self, shift: int) -> ColorlessRing:
        ring = ColorlessRing()
        for index in range(self.volume):
            location = (index + shift) % self.volume
            ring.append(self.__positions[location])
        return ring

    def occupies(self, position: Coordinates) -> bool:
        return position in self.__occupied

    def closed(self):
        return self.volume >= 4 and self.distance == 1

    def append(self, position: Coordinates):
        if position in self.__occupied:
            raise Exception(f"Position {position} already occupied by ColorlessRing.")

        self.__positions.append(position)
        self.__occupied.add(position)

    def extend(self, position: Coordinates) -> ColorlessRing:
        cp = ColorlessRing()
        cp.__positions.extend(self.__positions)
        cp.__occupied.update(self.__occupied)
        cp.append(position)
        return cp

    def as_reaches(self) -> Iterator[set[Reach]]:
        return iter(
            Reach.from_moves(
                start=self.__positions[(index - 1) % self.volume],
                inter=self.__positions[index],
                final=self.__positions[(index + 1) % self.volume],
            )
            for index in range(0, self.volume)
        )

    def __lt__(self, other: ColorlessRing) -> bool:
        return self.volume.__lt__(other.volume)

    def __str__(self) -> str:
        content = f"{self.anchor}"

        for index in range(1, len(self.__positions)):
            content += f" -- {str(self.__positions[index])}"

        if self.closed():
            content += f" -- {self.anchor}"
        else:
            content += " -- [OPEN]"

        return content
