#!/usr/bin/env python3.10
"""Enumerations."""
import enum

import numpy as np
import collections as col

HELD_DOWN = col.defaultdict(lambda: False)


class Direction(enum.Enum):
    """Packing directions for boxes."""

    VERTICAL = enum.auto()
    HORIZONTAL = enum.auto()


class Packing(enum.Enum):
    """Packings for Boxes."""

    START = enum.auto()
    CENTER = enum.auto()
    END = enum.auto()
    NONE = enum.auto()


class Anchor(enum.Flag):
    """The position at which the item is anchored."""

    TOP = enum.auto()
    BOTTOM = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()

    def to_arr(self) -> np.ndarray:
        """Turn the enum into an array which when multiplied by the item's size
        gives the offset from the top left corner at which the item should be drawn."""
        assert not (self.BOTTOM & self.TOP)
        assert not (self.LEFT & self.RIGHT)

        arr = np.array([0.5, 0.5])

        if self & Anchor.RIGHT:
            arr[0] = 1
        if self & Anchor.LEFT:
            arr[0] = 0
        if self & Anchor.BOTTOM:
            arr[1] = 1
        if self & Anchor.TOP:
            arr[1] = 0

        return arr
