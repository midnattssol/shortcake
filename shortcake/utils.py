#!/usr/bin/env python3.10
"""Utilities."""
import typing as t

import colour
import nerdfonts
import numpy as np

TAU = np.pi * 2
Numeric = t.Union[int, float, np.ndarray]


def get_nf_icon(name: str) -> str:
    """Get a nerd font icon from its name."""

    def nerdify(name):
        return name.removeprefix("nf-").replace("-", "_")

    if name is None or (norm_name := nerdify(name)) not in nerdfonts.icons:
        norm_name = nerdify("fa-question_circle_o")

    return nerdfonts.icons[norm_name]


# ===| Coordinates |===


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

    BLACK = None
    WHITE = None
    ACCENT_0 = None
    ACCENT_1 = None


# ===| Misc |===


def index_or(container: t.Iterable, obj: t.Any) -> t.Optional[int]:
    """Get the index of an item in a container if it's in the container or None otherwise."""
    return container.index(obj) if obj in container else None


def lerp(origin: Numeric, target: Numeric, frac: Numeric) -> Numeric:
    """Linearly interpolate between the origin and the target by the fraction."""
    return (target - origin) * frac + origin


def filled(fn: callable, *shape):
    """Create a filled nested list of lists shaped according to `shape`."""
    # could be rewritten without recursion
    if len(shape) > 1:
        return [filled(fn, *shape[1:]) for _ in range(shape[0])]
    if len(shape) == 1:
        return [fn() for _ in range(shape[0])]

    raise ValueError
