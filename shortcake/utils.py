#!/usr/bin/env python3.11
"""Utilities."""
from __future__ import annotations
import itertools as it
import typing as t

import colour
import numpy as np

# ===| Constants |===

TAU = np.pi * 2
Numeric = t.Union[int, float, np.ndarray]
SIZE = np.array([0, 0])
PHI = (1 + np.sqrt(5)) / 2


# ===| Coordinates |===


def isiterable(item: object) -> bool:
    """Get whether or not an object is iterable."""
    return hasattr(item, "__iter__")


def shape_of(nested: iter, dims=2) -> bool:
    """Get the shape of a nested iterable."""
    assert isinstance(dims, int) and dims > 0, dims
    if not is_rectangular(nested, dims):
        return None

    top = nested
    out = [len(top)]
    for _ in range(dims - 1):
        top = top[0]
        out.append(len(top))
    return out


def is_rectangular(nested: iter, dims: int = 2) -> bool:
    """Get whether or not a nested iterable is (hyper?)rectangular.

    >>> is_rectangular([[1, 2, 3], [1, 2]])
    False
    >>> is_rectangular([[1, 2, 3], [1, 2, 3]])
    True
    """
    assert isinstance(dims, int) and dims > 0, dims
    if dims == 1:
        return isiterable(nested)

    lengths = map(len, nested)
    prev = None
    for length in lengths:
        if prev is not None and length != prev:
            return False
        prev = length

    if dims > 2:
        return all(map(is_rectangular, nested, it.repeat(dims - 1)))
    return True


def polar2cartesian(coords: Numeric) -> Numeric:
    """Convert polar coordinates to cartesian coordinates."""
    cos = np.cos(coords[1])
    sin = np.sin(coords[1])
    length = coords[0]

    return np.array([cos, sin]) * length


def cartesian2polar(coords: Numeric) -> Numeric:
    """Convert cartesian coordinates to polar coordinates."""
    length = np.linalg.norm(coords)
    if length == 0:
        return np.zeros(2)

    phi = np.arctan2(*coords[::-1])
    return np.array([length, phi])


def rotate2d(arr: np.ndarray, angle: float) -> np.ndarray:
    """Rotate a 2D array with respect to (0, 0)."""
    cos = np.cos(angle)
    sin = np.sin(angle)

    rotated = np.dot(arr, np.array([[cos, -sin], [sin, cos]]))
    return rotated


# ===| Interpolation |===


def rotating_interpolation(origin: Numeric, target: Numeric, frac: float) -> Numeric:
    """Interpolates 2 2D points with a rotation."""
    delta = target - origin
    angle_image_width = 0.25

    return rotate2d(delta * frac, TAU * (1 - frac) * angle_image_width) + origin


# ===| Colors |===


def normalize_color(color):
    """Normalize a color into RGBA."""
    if color is None:
        return color
    if isinstance(color, str):
        return np.array([*colour.hex2rgb(color), 1])
    if len(color) == 3:
        return np.array([*color, 1])
    if len(color) == 4:
        assert isinstance(color, np.ndarray)
        return color

    raise NotImplementedError()


class Color:
    """Global colors."""

    ACCENT_0 = None
    ACCENT_1 = None
    ACCENT_2 = None
    ACCENT_3 = None
    WHITE = None
    GREY_L1 = None
    GREY = None
    GREY_D1 = None
    GREY_D2 = None
    BLACK = None


# ===| Misc |===


def index_or(container: t.Iterable, obj: t.Any) -> t.Optional[int]:
    """Get the index of an item in a container if it's in the container or None otherwise."""
    return container.index(obj) if obj in container else None


def lerp(origin: Numeric, target: Numeric, frac: Numeric) -> Numeric:
    """Linearly interpolate between the origin and the target by the fraction."""
    return (target - origin) * frac + origin


def lerp_fn(origin: Numeric, target: Numeric, frac: Numeric) -> Numeric:
    """Linearly interpolate between two functions."""

    def inner(passed: Numeric):
        o_result = origin(passed)
        t_result = target(passed)

        return (t_result - o_result) * frac + o_result

    return inner


def filled(fn: callable, *shape):
    """Create a filled nested list of lists shaped according to `shape`."""
    # could be rewritten without recursion
    if len(shape) > 1:
        return [filled(fn, *shape[1:]) for _ in range(shape[0])]
    if len(shape) == 1:
        return [fn() for _ in range(shape[0])]

    raise ValueError
