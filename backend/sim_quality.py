"""Read-only simulation to recalibrate quality_score. NO DB writes.

Pulls a sample of skills, runs the real QualityAnalyzer per-dimension methods,
compares the current composite vs a proposed rebalanced+curved one, and prints
the projected new distribution. Lets us validate the recalibration before any
full re-scan.
"""
import os, json, statistics as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.skill import Skill
from app.services.quality_analyzer import QualityAnalyzer

load_dotenv()
engine = create_engine(os.environ["SUPABASE_DB_URL"])
Session = sessionmaker(bind=engine)
db = Session()
qa = QualityAnalyzer()

# Representative RANDOM sample of stars>=5 (not top-by-stars, which biases high).
sample = (db.query(Skill)
          .filter(Skill.stars >= 5, Skill.readme_content.isnot(None))
          .order_by(func.random())
          .limit(800).all())

# Proposed NEW weights — shift ~16% off the 3 "advanced/rare" dims
# (procedural/instruction/security) that most normal repos score ~0 on, onto
# achievable core dims. Sum = 1.0.
NEW_W = dict(completeness=0.14, clarity=0.13, specificity=0.10, examples=0.12,
             structure=0.16, agent=0.18, procedural=0.06, instruction=0.06, security=0.05)
# Final power-curve calibration: display = raw**CURVE * 100. A curve <1 lifts the
# compressed mid/top range across the scale WITHOUT inflating (smooth, monotonic,
# no clamping). Honest spread, not min-max stretch that bunches at the ceiling.
CURVE = 0.65
def calib(raw):
    return (raw ** CURVE) * 100

def dims(s):
    return dict(
        completeness=qa._completeness(s), clarity=qa._clarity(s),
        specificity=qa._specificity(s), examples=qa._examples(s),
        structure=qa._readme_structure(s), agent=qa._agent_readiness(s),
        procedural=qa._procedural_content(s), instruction=qa._instruction_quality(s),
        security=qa._security_awareness(s))

OLD_W = dict(completeness=0.11, clarity=0.11, specificity=0.11, examples=0.09,
             structure=0.14, agent=0.16, procedural=0.10, instruction=0.09, security=0.09)

rows = []
dim_sum = {k: 0.0 for k in NEW_W}
for s in sample:
    d = dims(s)
    for k in dim_sum: dim_sum[k] += d[k]
    old = sum(d[k]*OLD_W[k] for k in OLD_W) * 100
    new_raw = sum(d[k]*NEW_W[k] for k in NEW_W)
    new = calib(new_raw)
    rows.append((s.repo_full_name, s.stars, old, new, new_raw))

n = len(rows)
def dist(vals):
    vals = sorted(vals)
    p = lambda q: vals[int(len(vals)*q)]
    return f"avg {st.mean(vals):.1f} | p50 {p(.5):.0f} | p90 {p(.9):.0f} | max {vals[-1]:.0f}"

print(f"sample: {n} skills (stars>=5, with README)\n")
print("== per-dimension mean (0-1) — low ones drag the score ==")
for k in NEW_W: print(f"  {k:<12} {dim_sum[k]/n:.2f}")
print(f"\n== new_raw (pre-calib, x100): {dist([r[4]*100 for r in rows])}  [curve={CURVE}]")
print(f"== OLD composite:  {dist([r[2] for r in rows])}")
print(f"== NEW composite:  {dist([r[3] for r in rows])}")
print("\n== named repos (old -> new) ==")
for name in ["browser-use/browser-use", "microsoft/playwright-mcp",
             "modelcontextprotocol/servers"]:
    for r in rows:
        if r[0] == name: print(f"  {name:<38} {r[2]:.0f} -> {r[3]:.0f} ({r[1]}*)")
print("\n== top 5 NEW ==")
for r in sorted(rows, key=lambda x: -x[3])[:5]:
    print(f"  {r[3]:.0f}  (was {r[2]:.0f})  {r[0]} ({r[1]}*)")
db.close()
