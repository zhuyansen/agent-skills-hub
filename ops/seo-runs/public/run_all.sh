#!/bin/bash
# The public rerun (2026-11-12): the same test site at https://lumentea-test.vercel.app/, for the control and the three
# tools that refuse private addresses. Plain sandbox image: nothing to serve locally.
cd "$(dirname "$0")/../../.."
R="caffeinate -i python3 ops/ppt-runs/run.py"
export SANDBOX_IMAGE=pptrun:1 NO_RENDER=1 RUNS_DIR=ops/seo-runs/public
$R control >> ops/seo-runs/public/run.log 2>&1
FORCE_SETUP=1 $R --all >> ops/seo-runs/public/run.log 2>&1
