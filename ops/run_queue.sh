#!/bin/bash
# One serial queue for the sandbox tests (the subscription allows one run at a time).
# Order: the code review rerun, hooks, Obsidian, design (twice). Each test scores itself after.
cd "$(dirname "$0")/.."
R="caffeinate -i python3 ops/ppt-runs/run.py"
rm -rf ops/review-runs/out/nathankim0__clean-architecture-skills
TEXT_PROXY=1 NO_RENDER=1 RUNS_DIR=ops/review-runs $R nathankim0/clean-architecture-skills >> ops/review-runs/run.log 2>&1
python3 ops/review-runs/score_review.py nathankim0/clean-architecture-skills >> ops/review-runs/score.log 2>&1
NO_PREINSTALL=1 NO_RENDER=1 RUNS_DIR=ops/hooks-runs $R octocat/Hello-World > ops/hooks-runs/run.log 2>&1
FORCE_SETUP=1 TEXT_PROXY=1 NO_RENDER=1 RUNS_DIR=ops/hooks-runs $R --all >> ops/hooks-runs/run.log 2>&1
python3 ops/hooks-runs/score_hooks.py > ops/hooks-runs/score.log 2>&1
NO_PREINSTALL=1 NO_RENDER=1 RUNS_DIR=ops/obsidian-runs $R octocat/Hello-World > ops/obsidian-runs/run.log 2>&1
FORCE_SETUP=1 NO_RENDER=1 RUNS_DIR=ops/obsidian-runs $R --all >> ops/obsidian-runs/run.log 2>&1
python3 ops/obsidian-runs/score_obsidian.py > ops/obsidian-runs/score.log 2>&1
for sfx in "" "-b"; do
  NO_PREINSTALL=1 NO_RENDER=1 OUT_SUFFIX=$sfx RUNS_DIR=ops/design-runs $R octocat/Hello-World >> ops/design-runs/run.log 2>&1
  NO_RENDER=1 OUT_SUFFIX=$sfx RUNS_DIR=ops/design-runs $R --all >> ops/design-runs/run.log 2>&1
done
python3 ops/design-runs/score_design.py > ops/design-runs/score.log 2>&1
