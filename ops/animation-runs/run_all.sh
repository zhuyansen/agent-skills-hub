#!/bin/bash
# The animation test's queue: each kind's runs, one at a time (ops/ppt-runs/queue.py waits out usage limits).
# The sprite and rig briefs offer an image model (gpt-image-2, Gemini) through the sandbox's adapter.
cd "$(dirname "$0")/../.."
for kind in web lottie diagram art sprite rig; do
  extra=""; case $kind in sprite|rig) extra="IMAGE_ROUTES=1 IMAGE_KEY_NAME=APIMART_MULTI_KEY";; esac
  echo "$(date '+%m-%d %H:%M') $kind starts"
  env RUNS_DIR=ops/animation-runs/$kind SANDBOX_IMAGE=pptrun-3d:1 NO_RENDER=1 RUN_MINUTES=40 $extra \
    caffeinate -i python3 ops/ppt-runs/queue.py >> ops/animation-runs/$kind/run.log 2>&1
done
echo "$(date '+%m-%d %H:%M') all kinds done"
