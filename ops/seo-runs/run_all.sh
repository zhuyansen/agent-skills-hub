#!/bin/bash
# The SEO test, serially (the subscription allows one run at a time): the control, then every candidate,
# each installed by an agent session that follows its README (FORCE_SETUP=1), then the judge.
cd "$(dirname "$0")/../.."
R="caffeinate -i python3 ops/ppt-runs/run.py"
export SANDBOX_IMAGE=seorun:1 NO_RENDER=1 RUNS_DIR=ops/seo-runs
$R control >> ops/seo-runs/run.log 2>&1
FORCE_SETUP=1 $R --all >> ops/seo-runs/run.log 2>&1
