#!/usr/bin/env python3.10
""""""
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
    """A size which is a function of the parent object."""

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        return self.n(parent_size, parent)


@dc.dataclass
class TimeFunction(Size):
    """A size which is a function of time."""

    start_time: float = dc.field(default_factory=time.time)

    def get(self, parent_size=None, parent=None):
        """Get the value of the size."""
        dt = time.time() - self.start_time
        return self.n(dt)


@dc.dataclass
class Easing(Size):
    """A size defined as an easing between two values."""

    target: t.Any
    period: float
    start_time: float = dc.field(default_factory=time.time)
    easing: t.Optional[callable] = None
    _is_expired: bool = False
    interpolator: callable = lerp
    clamp: bool = True

    @property
    def origin(self):
        """Get the origin of the easing."""
        return self.n

    @property
    def is_expired(self):
        """Get whether or not the process has expired."""
        self._is_expired = self._is_expired or time.time() >= (
            self.start_time + self.period
        )
        return self._is_expired

    def get_frac(self):
        """Get the current fraction of time passed to expiration."""
        frac = (time.time() - self.start_time) / self.period
        if self.clamp:
            frac = min(max(frac, 0), 1)
        return frac

    def get(self, parent_size=None, parent=None):
        """Get the current value."""
        frac = self.get_frac()

        if self.easing is not None:
            frac = self.easing(frac)

        return self.interpolator(self.origin, self.target, frac)
