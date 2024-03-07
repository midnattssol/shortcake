#!/usr/bin/env python3.11
"""A skeleton widget."""
import math
import time
from datetime import datetime

import cairo
import numpy as np
import shortcake

# Graphics
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib


# ===| Globals |===

FPS = 60
SIZE = np.array([300, 600])
WHITE = shortcake.normalize_color("#f0f0f0")
BLACK = shortcake.normalize_color("#142424")

TIME_TO_KILL_AT = None

WIDGETS = []


# A top container.
def get_widgets():
    global WIDGETS
    rectangle = shortcake.RoundedRectangle(
        position=shortcake.TimeFunction(
            shortcake.oscillating(
                SIZE / 2 - [0, 100],
                SIZE / 2 + [0, 100],
            )
        ),
        size=[200, 100],
        direction=shortcake.Direction.VERTICAL,
        # direction=Direction.HORIZONTAL,
    )

    r, c = 3, 4

    rectangle.make_grid(
        [
            [
                shortcake.Arc(
                    radius=20,
                    color=shortcake.TimeFunction(
                        shortcake.oscillating(shortcake.Color.ACCENT_0, shortcake.Color.WHITE)
                    ),
                )
                for _ in range(r)
            ]
            for _ in range(c)
        ]
    )

    # rectangle.children = [
    #     shortcake.RoundedRectangle(size=[20, 30], color=shortcake.Color.ACCENT_0),
    #     shortcake.RoundedRectangle(size=[60, 30], color=shortcake.Color.ACCENT_0),
    #     shortcake.RoundedRectangle(
    #         size=[30, 40],
    #         color=shortcake.Easing(
    #             shortcake.Color.ACCENT_0,
    #             shortcake.Color.WHITE,
    #             2,
    #             easing=easings.in_out_back,
    #         ),
    #         anchor=Anchor.BOTTOM | Anchor.RIGHT,
    #     ),
    # ]

    WIDGETS = [rectangle]


def draw(da, ctx):
    """Draw everything that should be drawn to the screen. Called once per frame."""
    if TIME_TO_KILL_AT is not None and TIME_TO_KILL_AT < time.time():
        exit()

    for widget in WIDGETS:
        widget.render(ctx)


def kill(seconds_left=0):
    """Kill the widget in some time."""
    global TIME_TO_KILL_AT
    TIME_TO_KILL_AT = time.time() + seconds_left


# ===| Callbacks |===


def timeout_callback(widget):
    """Update the screen."""
    widget.queue_draw()
    return True


def press_callback(window, key):
    """Callback for button presses."""
    val = key.keyval

    if val == Gdk.KEY_Escape:
        kill()


def click_callback(window, event):
    """Callback for mouse clicks."""
    window.begin_move_drag(
        event.button,
        round(event.x + window.get_window().get_root_origin()[0]),
        round(event.y + window.get_window().get_root_origin()[1]),
        event.time,
    )


def main():
    colors = [
        "#E7F7C9",
        "#101D24",
        "#468C61",
        "#133845",
    ]

    shortcake.Color.WHITE = shortcake.normalize_color(colors[0])
    shortcake.Color.BLACK = shortcake.normalize_color(colors[1])
    shortcake.Color.ACCENT_0 = shortcake.normalize_color(colors[2])
    shortcake.Color.ACCENT_1 = shortcake.normalize_color(colors[3])

    get_widgets()

    win = Gtk.Window(title="picom-widget-main")
    win.move(0, 0)
    screen = win.get_screen()
    rgba = screen.get_rgba_visual()
    win.set_visual(rgba)
    win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    # Connect callbacks.
    win.connect("key-press-event", press_callback)
    win.connect("destroy", lambda w: Gtk.main_quit())
    win.connect("button-press-event", click_callback)

    # Make the window floating.
    win.set_default_size(*SIZE)
    win.set_app_paintable(True)
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)

    # Prepare for drawing.
    drawing_area = Gtk.DrawingArea()
    drawing_area.connect("draw", draw)
    GLib.timeout_add(1000 / FPS, timeout_callback, win)
    win.add(drawing_area)
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
