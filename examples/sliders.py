#!/usr/bin/env python3.11
"""Sample progress widgets."""
import math
import time
from datetime import datetime

import cairo
import numpy as np
import shortcake as sc

# Graphics
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ===| Globals |===

FPS = 60
SIZE = np.array([300, 600])

TIME_TO_KILL_AT = None

WIDGETS = []


# A top container.
def get_widgets():
    global WIDGETS

    slider = sc.Slider(
        position=np.array([SIZE[0] / 2, SIZE[1] / 4]),
        size=[200, 15],
        poller=sc.Poller(lambda: sc.oscillating(0.3, 0.7, sc.in_out_elastic)(time.time() / 1.5)),
    )

    progress = sc.ProgressCircle(
        position=SIZE / 2,
        poller=sc.Poller(lambda: sc.oscillating(0.2, 0.7, sc.in_out_elastic)(time.time() / 1.5)),
        filler=sc.Arc(
            color=sc.Color.WHITE,
            position=sc.Offset(0),
        ),
    )

    WIDGETS = [progress, slider]


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

    sc.Color.WHITE = sc.normalize_color(colors[0])
    sc.Color.BLACK = sc.normalize_color(colors[1])
    sc.Color.ACCENT_0 = sc.normalize_color(colors[2])
    sc.Color.ACCENT_1 = sc.normalize_color(colors[3])

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
