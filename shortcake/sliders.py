#!/usr/bin/env python3.11
"""Progress widgets."""
from __future__ import annotations
import dataclasses as dc

import numpy as np

from .enums import *
from .poller import *
from .render import *
from .utils import *


@dc.dataclass
class ProgressBar(RoundedRectangle):
    """A rounded rectangular progress bar."""

    poller: Poller = dc.field(default_factory=Poller(lambda: 0.618))
    filler: RoundedRectangle = dc.field(default_factory=lambda: RoundedRectangle(anchor=Anchor.LEFT))
    fill_direction: Direction = Direction.HORIZONTAL

    def __post_init__(self):
        """Set the object's parent."""
        self.filler.parent = self

    def render(self, ctx):
        """Render the object."""
        super().render(ctx)

        frac = self.poller.get()
        frac = min(max(frac, 0), 1)

        # Make sure the fraction isn't way too small.
        frac = max(
            frac,
            self.filler.radius * 2 / self.size[self.fill_direction == Direction.VERTICAL],
        )

        scaler = [1, frac] if self.fill_direction == Direction.VERTICAL else [frac, 1]

        assert self.filler.parent is self

        filler_anchor = self.filler.anchor

        self.filler.position = self.get_top_left() + (self.filler.anchor.to_arr() * self.size)
        self.filler.anchor = Anchor(0)
        self.filler.size = Relative(np.array(scaler))
        self.filler.anchor = filler_anchor
        self.filler.render(ctx)


@dc.dataclass
class ProgressCircle(Arc):
    """A circular progress bar."""

    poller: Poller = dc.field(default_factory=Poller(lambda: 0.618))
    filler: Arc = dc.field(default_factory=Arc)

    def __post_init__(self):
        """Set the object's parent."""
        self.filler.parent = self

    def render(self, ctx):
        """Render the object."""
        frac = self.poller.get()
        frac = min(max(frac, 0), 1)
        self.filler.end_arc = self.filler.begin_arc + frac * TAU

        assert self.filler.parent is self
        super().render(ctx)
        self.filler.render(ctx)


@dc.dataclass
class Slider(RoundedRectangle):
    """A rounded rectangular slider."""

    poller: Poller = dc.field(default_factory=lambda: Poller(lambda: 0.618))
    pointer: Renderable = None
    fill_direction: Direction = Direction.HORIZONTAL

    def __post_init__(self):
        """Set the object's parent and pointer."""
        if self.pointer is None:
            self.pointer = Arc(
                radius=min(self.size) / 2,
                color=Color.WHITE,
                position=Offset(0),
            )

        self.pointer.parent = self

    def render(self, ctx):
        """Render the object."""
        super().render(ctx)

        frac = self.poller.get()
        frac = min(max(frac, 0), 1)

        scaler = np.array([0.5, frac] if self.fill_direction == Direction.VERTICAL else [frac, 0.5])

        assert self.pointer.parent is self

        self.pointer.position = scaler * self.size + self.get_top_left()
        self.pointer.render(ctx)
