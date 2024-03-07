#!/bin/sh
set -eux pipefail

pybuild pybuild.cson

cloc shortcake > info/sloc.txt
