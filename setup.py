#!/usr/bin/env python3.10
"""Setup the package."""
import setuptools

setuptools.setup(
    name="shortcake",
    version="0.1",
    description="A private Gdk library",
    url="#",
    author="luna",
    install_requires=["numpy", "pycairo", "more_itertools", "colour", "nerdfonts"],
    author_email="",
    packages=setuptools.find_packages(),
    zip_safe=False,
)
