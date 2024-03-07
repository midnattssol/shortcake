#!/usr/bin/env python3.11
"""An updated render system."""
from __future__ import annotations

import copy as cp
import dataclasses as dc
import typing as t

import cairo
import numpy as np

from .enums import Anchor, Direction, Packing
from .size import Absolute, Easing, Offset, ParentFunction, Percentage, Relative, Size, TimeFunction
from .utils import TAU, is_rectangular, shape_of

# ===| Base classes |===


@dc.dataclass
class Renderable:
    """An object with a parent, anchor, position, and a render method.

    The `__getattribute__` dunder method is overridden in this object, so that any
    attribute which is an instance of `Size` is unwrapped before being returned. This
    is done so that `Size`s can be mixed with other objects.

    To get the unwrapped attribute, use the `get` method with `unwrap` set to False.
    """

    anchor: Anchor = Anchor.CENTER
    position: Size = dc.field(default_factory=lambda: Absolute(np.array([0.0, 0.0])))
    parent: t.Any = None
    visible: bool = True  # WIP: Add visibility.

    def render(self, ctx):
        """Render the item."""
        raise NotImplementedError()

    # ===| Derived methods |===

    def copy(self):
        """Get a copy of the item."""
        return cp.deepcopy(self)

    def get(self, attr, unwrap=True):
        """Get the object attribute."""
        gotten = object.__getattribute__(self, attr)
        if not unwrap:
            return gotten

        if not isinstance(gotten, Size):
            return gotten

        if isinstance(gotten, (Relative, Percentage, ParentFunction, Offset)):
            parent = object.__getattribute__(self, "parent")
            if parent is None or not hasattr(parent, attr):
                raise ValueError(
                    f"Attribute '{attr}' ({gotten}) of {self} of type {type(self)} requires"
                    f" a parent with the same attribute, but {parent} of type {type(parent)}"
                    " lacks it."
                )

            return gotten.get(parent.get(attr), parent)

        return gotten.get()

    def __getattribute__(self, name):
        """Get the attribute, resolving Sizes."""
        if (name.startswith("__") and name.endswith("__")) or name == "get":
            return object.__getattribute__(self, name)

        return self.get(name)


@dc.dataclass
class Sized(Renderable):
    """A renderable object with some notion of a size."""

    size: Size = dc.field(default_factory=lambda: Relative(np.array([0.5, 0.5])))

    def render(self, ctx):
        """Render the item."""
        raise NotImplementedError()

    def get_top_left(self):
        """Get the top-left corner of the sized item."""
        out = self.position - self.size * self.anchor.to_arr()
        return out

    def get_anchor_coord(self, anchor: Anchor = Anchor.CENTER):
        """Get the coordinates at this anchor in the sized item.

        For example, sized.get_anchor_coord(Anchor.BOTTOM) will get
        the position of the bottom centre coordinate of the Sized.
        """
        return self.position - (self.size * (self.anchor.to_arr() - anchor.to_arr()))


@dc.dataclass
class Container(Sized):
    """A container for organizing other renderable objects."""

    direction: Direction = Direction.HORIZONTAL
    packing: Packing = Packing.NONE
    children: t.List[Renderable] = dc.field(default_factory=list)
    spacing: int = 5

    def make_grid(self, items, scale=(1, 1)):
        """Create a grid of items."""
        assert items and is_rectangular(items), items
        rows, cols = shape_of(items)

        for i, row in enumerate(items):
            for j, item in enumerate(row):
                item.parent = self
                anchor_like = np.array([i / (rows - 1), j / (cols - 1)])
                anchor_like -= 0.5
                anchor_like *= scale

                item.position = ParentFunction(
                    lambda pos, parent, k=anchor_like: parent.size * (k) + parent.get_anchor_coord(Anchor.CENTER)
                )

            self.children += row

    def occupied_space(self) -> float:
        """Get the current amount of space along the relevant direction taken up by packed items."""
        assert self.packing is not Packing.NONE
        i = int(self.direction == Direction.HORIZONTAL)
        return sum(child.size[i] + 2 * self.spacing for child in self) - self.spacing

    def render(self, ctx):
        """Render the container."""
        if self.packing == Packing.NONE or not self.children:
            for child in self.children:
                child.render(ctx)
            return

        # Recalculate the positions based on the packing.
        i = int(self.direction == Direction.HORIZONTAL)
        i_0 = int(not i)

        rel_pos = np.array([0.0, 0.0])
        rel_pos[i] -= self.spacing
        # rel_pos[i] += self.children[0].size[i] / 2

        locations = []

        for child in self:
            anchor_array = child.anchor.to_arr()
            anchor_array[i] = 0
            offset = anchor_array * self.size

            # If the child is anchored to the side, it has to be moved closer
            # to the center, since otherwise the child would be centered on the border.
            n = anchor_array[i_0] * 2 - 1
            offset[i_0] -= n * (self.spacing + child.size[i_0] / 2)

            # Get the total of the difference relative to the top right.
            rel_pos[i] += self.spacing
            rel_tot = rel_pos + offset

            # Update the position and render the child.
            locations.append([child, rel_tot])
            rel_pos[i] += child.size[i] + self.spacing

        # Move the anchor to the correct side.
        new_anchor = (
            {
                Packing.START: Anchor.TOP,
                Packing.CENTER: Anchor.CENTER,
                Packing.END: Anchor.BOTTOM,
            }[self.packing]
            if self.direction == Direction.HORIZONTAL
            else {
                Packing.START: Anchor.LEFT,
                Packing.CENTER: Anchor.CENTER,
                Packing.END: Anchor.RIGHT,
            }[self.packing]
        )

        # Center pack by getting the empty space at the bottom
        # and then redistributing it on either side.
        if self.packing == Packing.CENTER:
            p_first = [l for x, l in locations if x == self.children[0]][0]
            p_last = [l for x, l in locations if x == self.children[-1]][0]

            width = p_last + self.children[-1].size - p_first
            avg_pos = (self.size - width) / 2
            avg_pos[i_0] = 0
            locations = [[c, l + avg_pos] for c, l in locations]

        # End pack by moving everything down as far as the emepty space allows.
        if self.packing == Packing.END:
            locations = [[c, self.size - l] for c, l in locations]

        for child, loc in locations:
            child.position = loc + self.get_top_left()
            old_anchor = child.anchor
            child.anchor = new_anchor
            child.render(ctx)
            child.anchor = old_anchor

    def __iter__(self):
        """Iterate over the children."""
        return iter(self.children)

    def __len__(self):
        """Get the number of children."""
        return len(self.children)


@dc.dataclass
class Shape:
    """Abstract base class for a shape."""

    color: Color = dc.field(default_factory=lambda: np.array([0.1, 0.1, 0.1]))
    filled: bool = True
    width: int = 3


@dc.dataclass
class Rectangle(Shape, Container):
    """A rectangle."""

    def render(self, ctx):
        """Render the rectangle."""
        ctx.new_path()
        ctx.set_source_rgba(*self.color)
        ctx.rectangle(*self.get_top_left(), *self.get("size"))
        ctx.fill()
        ctx.stroke()

        Container.render(self, ctx)


@dc.dataclass
class Arc(Renderable, Shape):
    """An arc."""

    radius: float = 20
    begin_arc: float = 0
    end_arc: float = TAU

    @property
    def size(self):
        """Get the size of the arc."""
        return np.array([self.radius, self.radius]) * 2

    def render(self, ctx):
        """Render the arc."""
        ctx.new_path()
        ctx.set_source_rgba(*self.color)
        center_arr = self.anchor.to_arr() - [0.5, 0.5]

        center = self.position - self.size * center_arr

        ctx.arc(*center, self.radius, self.begin_arc, self.end_arc)

        if abs(self.begin_arc - self.end_arc) != TAU:
            ctx.line_to(*center)

        ctx.fill()
        ctx.stroke()


@dc.dataclass
class RoundedRectangle(Rectangle):
    """A rounded rectangle. The radius attribute determines the corner rounding."""

    corner_radius: float = 8

    def render(self, ctx):
        """Render the rounded rectangle."""
        ctx.set_source_rgba(*self.color)
        ctx.stroke()
        rounded_rect(ctx, *self.get_top_left(), *self.size, self.corner_radius)
        ctx.fill()
        ctx.stroke()

        Container.render(self, ctx)


@dc.dataclass(frozen=True)
class TextState:
    """The state of some text."""

    fore: Color = dc.field(default_factory=lambda: np.array([0.1, 0.1, 0.1]))
    slant: int = cairo.FONT_SLANT_NORMAL
    weight: int = cairo.FONT_WEIGHT_NORMAL


@dc.dataclass
class ColoredText(Renderable):
    """Some colored text."""

    font: str = "Iosevka Nerd Font"
    font_size: int = 20
    text: str = "Hello world"
    default_state: TextState = TextState()
    escape_indices: dict = dc.field(default_factory=dict)

    def get_state(self, index):
        """Return the state at some index."""
        state = self.default_state

        for key in sorted(self.escape_indices):
            if key > index:
                break
            state = self.escape_indices[key]

        return state

    def set_state(self, start: int, end: int, state: TextState):
        """Set the state between the start and end indices."""
        self.escape_indices[start] = state
        self.escape_indices = {k: v for k, v in self.escape_indices.items() if k not in range(start + 1, end)}
        self.escape_indices[end] = self.default_state

    def render(self, ctx):
        """Render the text."""
        ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        (_, _, width, height, _, _) = ctx.text_extents(self.text)
        height = self.font_size

        pos = self.position - ([width, height] * self.anchor.to_arr())
        keys = sorted(self.escape_indices)
        prev_state = self.default_state

        index = 0
        prev_index = 0

        for index in keys:
            x_distance = self._render_chunk(self.text[prev_index:index], prev_state, pos, ctx)
            pos += [x_distance, 0]
            prev_index = index
            prev_state = self.escape_indices[index]

        final_state = self.escape_indices[keys[-1]] if keys else self.default_state

        self._render_chunk(self.text[index:], final_state, pos, ctx)

    def _render_chunk(self, text, state, pos, ctx) -> int:
        """Render a chunk of text at some position and return its width."""
        ctx.select_font_face(self.font, state.slant, state.weight)
        ctx.set_font_size(self.font_size)
        ctx.set_source_rgba(*state.fore)

        # Use the full block to get the full character size.
        _, _, width, _, _, _ = ctx.text_extents("█")
        width *= len(text)

        ctx.move_to(*pos)
        ctx.show_text(text)

        return width


@dc.dataclass
class Text(Renderable):
    """Some text."""

    color: ... = dc.field(default_factory=lambda: np.array([0.3, 0.25, 0.1]))
    text: str = "Hello world!"
    font_size: int = 20
    font_face: str = "Iosevka Nerd Font"
    font_slant: int = cairo.FONT_SLANT_NORMAL
    font_weight: int = cairo.FONT_WEIGHT_NORMAL

    use_font_size_as_y: bool = True

    def render(self, ctx):
        """Render the text."""
        ctx.select_font_face(self.font_face, self.font_slant, self.font_weight)
        ctx.set_font_size(self.font_size)
        ctx.set_source_rgba(*self.color)

        (_, _, width, height, _, _) = ctx.text_extents(self.text)

        if self.use_font_size_as_y:
            height = self.font_size

        ctx.move_to(*self.position - ([width, height] * (self.anchor.to_arr() - [0, 1])))
        ctx.show_text(self.text)
        ctx.stroke()

        # # DEBUG: Uncomment this to see circles.
        # ctx.set_source_rgba(1, 0.2, 0, 1)
        # ctx.arc(
        #     *self.position - ([width, height] * (self.anchor.to_arr() - [0, 1])),
        #     4,
        #     0,
        #     TAU,
        # )
        # ctx.fill()
        # ctx.stroke()
        #
        # ctx.set_source_rgba(1, 0.2, 1, 1)
        # ctx.arc(*self.position, 4, 0, TAU)
        # ctx.fill()
        # ctx.stroke()


# ===| Utilities |===


def rounded_rect(ctx, x, y, width, height, radius) -> None:
    """Draw a rounded rectangle."""
    x_0 = x + radius
    x_1 = x + width - radius
    y_0 = y + radius
    y_1 = y + height - radius

    ctx.arc(x_0, y_0, radius, TAU / 2, 3 * TAU / 4)
    ctx.arc(x_1, y_0, radius, 3 * TAU / 4, 0)
    ctx.arc(x_1, y_1, radius, 0, TAU / 4)
    ctx.arc(x_0, y_1, radius, TAU / 4, TAU / 2)
