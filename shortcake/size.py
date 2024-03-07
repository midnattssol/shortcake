#!/usr/bin/env python3.11
"""Defines Sizes.

Sizes are classes which can update their values dynamically
over time or inherit them from a parent object. Example use
cases are easing colors, keeping a child with a permanent
offset from the parent, or changing the object size according
to a sine wave.
"""
from __future__ import annotations
import dataclasses as dc
import time
import typing as t

from .interpolate import (
    clamp,
    easing_average,
    in_back,
    in_bounce,
    in_circ,
    in_cubic,
    in_elastic,
    in_expo,
    in_out_back,
    in_out_bounce,
    in_out_circ,
    in_out_cubic,
    in_out_elastic,
    in_out_expo,
    in_out_quad,
    in_out_quart,
    in_out_quint,
    in_out_sine,
    in_quad,
    in_quart,
    in_quint,
    in_sine,
    lerp,
    linear,
    oscillate,
    oscillating,
    out_back,
    out_bounce,
    out_circ,
    out_cubic,
    out_elastic,
    out_expo,
    out_quad,
    out_quart,
    out_quint,
    out_sine,
)


# ===| Sizes |===


@dc.dataclass
class Size:
    """A size."""

    n: t.Union[float, callable]


@dc.dataclass
class Absolute(Size):
    """An absolute size."""

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n


@dc.dataclass
class Relative(Size):
    """A size calculated as a fraction of the relevant attribute of the parent object."""

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n * parent_size


@dc.dataclass
class Percentage(Size):
    """A size calculated as a percentage of the relevant attribute of the parent object."""

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n * parent_size * 100


@dc.dataclass
class Offset(Size):
    """A size which is offset from the parent object by some amount."""

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n + parent_size


@dc.dataclass
class ParentFunction(Size):
    """A size which is a function of the parent object.

    The `args` and `kwargs` attributes are passed along
    by to the `n` function. This is useful for changing
    offsets dynamically.
    """

    args: tuple = tuple()
    kwargs: t.Dict[str, t.Any] = dc.field(default_factory=dict)

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n(parent_size, parent, *self.args, **self.kwargs)


@dc.dataclass
class TimeFunction(Size):
    """A size which is a function of time."""

    start_time: float = dc.field(default_factory=time.time)
    offset: float = 0

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        dt = time.time() - self.start_time + self.offset
        return self.n(dt)


@dc.dataclass
class Easing(Size):
    """A size defined as an easing between two values."""

    target: t.Any
    period: float
    start_time: float = dc.field(default_factory=time.time)
    easing: t.Optional[callable] = None
    interpolator: callable = lerp
    clamp: bool = True

    _is_expired: bool = False

    @property
    def origin(self):
        """Get the origin of the easing."""
        return self.n

    @property
    def is_expired(self):
        """Get whether or not the process has expired."""
        self._is_expired = self._is_expired or time.time() >= (self.start_time + self.period)
        return self._is_expired

    def get_frac(self):
        """Get the current fraction of time passed to expiration."""
        frac = (time.time() - self.start_time) / self.period
        if self.clamp:
            frac = min(max(frac, 0), 1)
        return frac

    def value_at_frac(self, frac: float):
        """Get the value at some fraction of time."""
        if self.easing is not None:
            frac = self.easing(frac)

        return self.interpolator(self.origin, self.target, frac)

    def get(self, parent_size=None, parent=None):
        """Get the current value."""
        frac = self.get_frac()
        return self.value_at_frac(frac)


@dc.dataclass
class ContinousEasingSequence(Size):
    """A stack of easings applied one after the other.

    This is useful for having an item go through a series of
    transitions, while making sure that the item doesn't move abruptly
    from one position to another.

    Note that this sets the `start_time` to the moment the
    easing gets on top of the stack.
    """

    n: t.Any = None
    queue: list = dc.field(default_factory=list)

    @property
    def default(self):
        """Get the default value of the sequence."""
        return self.n

    def get(self, parent_size=None, parent=None):
        """Get the current value."""
        current_easing = None
        any_easings_expired = False

        # Go through the easings queue until a
        # valid easing is found.
        while current_easing is None:
            if not self.queue:
                return self.n

            candidate = self.queue[-1]

            # Update the new easing so that it starts
            # from the current time and value.
            if any_easings_expired:
                candidate.start = time.time()
                candidate.n = self.n

            # Check if the easing has expired, and if so
            # remove it & update the `n` attribute.
            if candidate.is_expired:
                any_easings_expired = True
                self.queue.pop()
                end_value = candidate.value_at_frac(1)
                self.n = end_value
                continue

            current_easing = candidate

        return current_easing.get(parent_size, parent)
