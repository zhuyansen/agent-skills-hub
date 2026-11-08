#!/bin/bash
# The 3D sandbox's entry: a virtual screen on :99 (Blender's window, OpenSCAD's renderer), then the usual run.
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp > /tmp/xvfb.log 2>&1 &
for _ in $(seq 1 20); do xdpyinfo -display :99 > /dev/null 2>&1 && break; sleep 0.5; done
exec bash /home/runner/bin/run_one.sh "$@"
