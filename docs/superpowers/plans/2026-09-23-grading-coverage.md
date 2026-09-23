# Grading Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise security-grade coverage from 15.6% of the catalog to every ≥1★ repo that has a README, without pushing the 8-hourly sync past its 120-minute timeout, and make every surface say honestly why a repo is ungraded.

**Architecture:** A fetch-attempt marker (`readme_fetched_at`) and one shared rule (`readme_coverage.py`) make the sync and a new scheduled backfill agree on which repos still need a README. The backfill walks dormant ungraded rows off-peak at 1 req/s. Grading moves out of `security_scanner.py` into `grade_refresh.py`, which re-grades only rows whose inputs changed unless the rules file's fingerprint changed. Frontend and static pages derive a four-way state (`graded / pending / no_readme / not_fetched`) from the marker.

**Tech Stack:** Python 3.12 + SQLAlchemy 2.0 + psycopg2 (backend, pytest), Supabase Postgres, GitHub Actions, React 19 + TypeScript (SPA), Node ESM build scripts.

**Spec:** `docs/superpowers/specs/2026-09-23-grading-coverage-design.md`

**Deviations from the spec (decided while reading the code):**
- **No partial index.** The candidate query runs 3×/day; an index build on this instance is the kind of load that 504'd the site in June.
- **The migration does not stamp the 426 `''` rows.** Some came from extra_repos artifacts where GitHub *does* have a README (gozen3ji/consulting-pptx-skill). Left unstamped, the shared rule treats them as "never fetched" and the backfill re-checks each once.
- **The backfill does not join sync's concurrency group.** In a GitHub concurrency group a newly queued run cancels the group's pending run — a backfill could cancel a queued sync. The script instead checks the Actions API every 100 rows and stops if a sync is queued or running; its schedule and 45-minute timeout keep it clear of sync and refresh-stale.
- **Fingerprint = sha256 of `security_scanner.py`, after moving `scan_all` out of it** into `grade_refresh.py`. Then the hashed file contains only grading logic, and editing the bookkeeping does not force a full re-grade.
- **Grade writes preserve `last_synced`.** `Skill.last_synced` has `onupdate=func.now()`; stamping every graded row would hide it from the stale-row probe (`refresh-stale.yml` picks rows by oldest `last_synced`) and freeze its stars.
- **Category-page copy is not rewritten.** Those pages list top repos, which the backfill's first tier grades within ~2 days, making "security-graded" true. Author pages list long tails, so their line becomes conditional.

---

## File map

| File | Responsibility | Task |
|---|---|---|
| `supabase/migrations/024_readme_fetch_marker.sql` (new) | three nullable columns | 1 |
| `backend/app/models/skill.py` | map the columns | 1 |
| `backend/app/services/readme_coverage.py` (new) | the "needs a README" rule + how a fetch result is recorded | 2 |
| `backend/tests/test_readme_coverage.py` (new) | its tests | 2 |
| `backend/app/scheduler/jobs.py` | Phase 5 uses the rule, records 404s, follows redirects; calls `refresh_grades` | 3, 4 |
| `backend/app/services/grade_refresh.py` (new) | which rows to grade, fingerprint, persistence | 4 |
| `backend/app/services/security_scanner.py` | loses `scan_all`; empty README → `unknown` | 4 |
| `backend/tests/test_grade_refresh.py` (new) | fingerprint + full-scan reasons + empty README | 4 |
| `frontend/src/utils/securityScanner.ts` | empty README → `unknown` | 5 |
| `frontend/src/pages/AnalyzerPage.tsx`, `frontend/src/components/AuditLeadCapture.tsx` | render `unknown` honestly | 5 |
| `backend/readme_backfill.py` | scheduled, marker-aware, quota- and sync-aware backfill | 6 |
| `backend/tests/test_readme_backfill.py` (new) | its pure decisions | 6 |
| `.github/workflows/readme-backfill.yml` (new) | 03/11/19 UTC schedule | 7 |
| `.github/workflows/deploy.yml` | don't republish after a failed sync | 8 |
| `frontend/scripts/shared-utils.mjs`, `generate-skill-pages.mjs`, `generate-badges.mjs`, `generate-author-pages.mjs`, `frontend/src/components/BadgeEmbed.tsx` | static surfaces | 9 |
| `frontend/src/lib/gradeState.ts` (new), `frontend/src/types/skill.ts`, `frontend/src/components/AuditVerdictCard.tsx` | SPA detail surface | 10 |

---

### Task 1: Migration 024 and model columns

**Order matters:** the migration must be applied to production *before* any code that maps the new columns is pushed — `db.query(Skill)` selects every mapped column and would crash the sync.

**Files:**
- Create: `supabase/migrations/024_readme_fetch_marker.sql`
- Modify: `backend/app/models/skill.py:80-97`

- [ ] **Step 1: Write the migration**

```sql
-- Grading coverage (docs/superpowers/specs/2026-09-23-grading-coverage-design.md).
--
-- readme_fetched_at — when a README fetch last got a definite answer from GitHub.
--   readme_content NULL                       → never fetched
--   readme_content ''  + readme_fetched_at    → GitHub had no README; retried after 30 days
--   readme_content text + readme_fetched_at   → fetched
-- Without it a repo with no README was re-fetched by every sync and backfill run, forever,
-- and every surface showed "not yet audited" for a repo that can never be audited.
--
-- security_scanned_at / scanner_version — when a row was last graded and by which rules
-- (sha256 of backend/app/services/security_scanner.py). grade_refresh.py uses them to
-- re-grade only rows whose inputs changed instead of all ~31K README'd rows every sync.
--
-- Additive: three nullable columns with no default, a metadata-only ALTER on 199K rows.
-- The 426 existing '' rows are deliberately left unstamped: some are ingestion artifacts
-- for repos that do have a README, so each is re-checked once by the backfill.
--
-- Security impact: none. Timestamps and a hash, readable through the existing
-- skills_public_read policy like every other skills column. RLS unchanged.

ALTER TABLE skills
  ADD COLUMN IF NOT EXISTS readme_fetched_at   timestamptz,
  ADD COLUMN IF NOT EXISTS security_scanned_at timestamptz,
  ADD COLUMN IF NOT EXISTS scanner_version     text;
```

- [ ] **Step 2: Apply it to production (serial, nothing else touching the DB)**

Check no sync is running first: `gh run list --workflow sync.yml --limit 1 --json status --jq '.[0].status'` must print `completed`.

```bash
cd backend && source venv/bin/activate && python3 - <<'PY'
import psycopg2
from dotenv import dotenv_values
c = psycopg2.connect(dotenv_values(".env")["SUPABASE_DB_URL"]); c.autocommit = True
cur = c.cursor()
cur.execute("SET statement_timeout = '30s'")
cur.execute(open("../supabase/migrations/024_readme_fetch_marker.sql").read())
cur.execute("""SELECT column_name, data_type FROM information_schema.columns
               WHERE table_name='skills' AND column_name IN
               ('readme_fetched_at','security_scanned_at','scanner_version') ORDER BY 1""")
print(cur.fetchall())
PY
```

Expected: `[('readme_fetched_at', 'timestamp with time zone'), ('scanner_version', 'text'), ('security_scanned_at', 'timestamp with time zone')]`

- [ ] **Step 3: Map the columns** — in `backend/app/models/skill.py`, after `readme_structure_score`:

```python
    readme_content = Column(Text, nullable=True)
    readme_structure_score = Column(Float, default=0.0)
    # When a README fetch last got a definite answer (see app/services/readme_coverage.py).
    readme_fetched_at = Column(DateTime(timezone=True), nullable=True)
```

and after `security_flags`:

```python
    security_flags = Column(Text, default="[]")
    # When this row was last graded, and by which rules (app/services/grade_refresh.py).
    security_scanned_at = Column(DateTime(timezone=True), nullable=True)
    scanner_version = Column(String(32), nullable=True)
```

- [ ] **Step 4: Run the suite** — `cd backend && python -m pytest tests/ -q` → all pass (231).

- [ ] **Step 5: Commit** — `git add supabase/migrations/024_readme_fetch_marker.sql backend/app/models/skill.py && git commit -m "feat(db): readme_fetched_at + grading stamps on skills (migration 024, applied)"`

---

### Task 2: The shared "needs a README" rule

**Files:**
- Create: `backend/app/services/readme_coverage.py`
- Test: `backend/tests/test_readme_coverage.py`

- [ ] **Step 1: Write the failing tests**

```python
"""The rule the sync and the backfill share for 'this repo still needs its README'."""
from datetime import datetime, timedelta, timezone

from app.services.readme_coverage import (
    MISSING_README_SQL, NO_README_RETRY_DAYS, readme_missing, readme_update,
)

NOW = datetime(2026, 9, 23, 12, tzinfo=timezone.utc)


def test_never_fetched_is_missing():
    assert readme_missing(None, None, NOW)


def test_a_fetched_readme_is_never_missing():
    assert not readme_missing("# Title", NOW - timedelta(days=400), NOW)
    assert not readme_missing("# Title", None, NOW)  # fetched before the marker existed


def test_confirmed_absent_waits_for_the_retry_window():
    assert not readme_missing("", NOW - timedelta(days=NO_README_RETRY_DAYS - 1), NOW)
    assert readme_missing("", NOW - timedelta(days=NO_README_RETRY_DAYS + 1), NOW)


def test_empty_without_a_marker_is_rechecked():
    # '' written before readme_fetched_at existed: some are ingestion artifacts
    # for repos that do have a README (gozen3ji/consulting-pptx-skill).
    assert readme_missing("", None, NOW)


def test_sql_matches_the_retry_window():
    assert f"interval '{NO_README_RETRY_DAYS} days'" in MISSING_README_SQL
    assert "readme_content IS NULL" in MISSING_README_SQL


def test_a_fetched_readme_is_written_with_the_marker():
    assert readme_update(None, "# Hi", absent=False, now=NOW) == {
        "readme_content": "# Hi", "readme_size": 4, "readme_fetched_at": NOW}


def test_absent_marks_a_row_without_text():
    assert readme_update(None, None, absent=True, now=NOW) == {
        "readme_content": "", "readme_size": 0, "readme_fetched_at": NOW}
    assert readme_update("", None, absent=True, now=NOW)["readme_fetched_at"] == NOW


def test_absent_never_erases_a_real_readme():
    # A 404 for a repo we hold text for is likelier a rename or a blip than a deleted README.
    assert readme_update("# Real", None, absent=True, now=NOW) == {}


def test_an_error_records_nothing():
    assert readme_update(None, None, absent=False, now=NOW) == {}
```

- [ ] **Step 2: Run them to see them fail** — `python -m pytest tests/test_readme_coverage.py -q` → `ModuleNotFoundError: No module named 'app.services.readme_coverage'`.

- [ ] **Step 3: Implement**

```python
"""Which repos still need their README fetched, and how a fetch result is recorded.

The sync (scheduler/jobs.py Phase 5) and the backfill (backend/readme_backfill.py)
both select targets by this rule and write results through it, so they cannot
disagree about a repo's state:

    readme_content NULL                       never fetched: a target
    readme_content ''   + readme_fetched_at   GitHub had no README when asked:
                                              a target again after NO_README_RETRY_DAYS
    readme_content ''   + no readme_fetched_at  '' written before the marker existed
                                              (June backfill, extra_repos artifacts): a target
    readme_content text                       fetched: never a target

Pure: imported by the backfill job, which installs only psycopg2.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

NO_README_RETRY_DAYS = 30

# The same rule for SQL WHERE clauses. It is never NULL, so NOT (...) is safe.
MISSING_README_SQL = (
    "(readme_content IS NULL OR (readme_content = '' AND (readme_fetched_at IS NULL "
    f"OR readme_fetched_at < now() - interval '{NO_README_RETRY_DAYS} days')))"
)


def readme_missing(content: str | None, fetched_at: datetime | None, now: datetime) -> bool:
    if content is None:
        return True
    if content:
        return False
    return fetched_at is None or fetched_at < now - timedelta(days=NO_README_RETRY_DAYS)


def readme_update(current: str | None, fetched: str | None, absent: bool, now: Any) -> dict[str, Any]:
    """Column values for one fetch result.

    fetched: README text from a 200. absent: GitHub said there is none (404, or a
    200 with nothing in it). A real README is never replaced by '' — a 404 for a
    repo we hold text for is likelier a rename or a blip than a deleted README.
    `now` is a datetime in tests and func.now() in the sync, so the stamp comes
    from the database clock that grade_refresh compares it with.
    """
    if fetched:
        return {"readme_content": fetched, "readme_size": len(fetched), "readme_fetched_at": now}
    if absent and not current:
        return {"readme_content": "", "readme_size": 0, "readme_fetched_at": now}
    return {}
```

- [ ] **Step 4: Run** — `python -m pytest tests/test_readme_coverage.py -q` → 9 passed.

- [ ] **Step 5: Commit** — `git add backend/app/services/readme_coverage.py backend/tests/test_readme_coverage.py && git commit -m "feat(sync): one rule for which repos still need a README"`

---

### Task 3: Sync Phase 5 uses the rule, records 404s, follows renames

**Files:** Modify `backend/app/scheduler/jobs.py` (297-311 helper, 583-639 Phase 5, 706-725 upsert)

- [ ] **Step 1: Replace `_repo_names_with_readme` with `_repo_names_settled`**

```python
def _repo_names_settled(db: "Session", names: list[str], chunk: int = 1000) -> set[str]:
    """Which of these repos need no README fetch: they have one, or GitHub
    recently confirmed they don't (app/services/readme_coverage.py)."""
    from app.models.skill import Skill  # inline like the rest of this module, avoids a circular import
    from app.services.readme_coverage import MISSING_README_SQL

    found: set[str] = set()
    for i in range(0, len(names), chunk):
        rows = (
            db.query(Skill.repo_full_name)
            .filter(Skill.repo_full_name.in_(names[i:i + chunk]))
            .filter(not_(text(MISSING_README_SQL)))
            .all()
        )
        found.update(r.repo_full_name for r in rows)
    return found
```

Add `from sqlalchemy import not_, text` to the imports at the top of `jobs.py` (beside `from sqlalchemy.orm import Session`).

- [ ] **Step 2: Phase 5 selection** — replace the `null_readme_skills` query and the backfill `have_readme` query:

```python
            from app.services.readme_coverage import MISSING_README_SQL
            null_readme_skills = (
                db.query(Skill.repo_full_name)
                .filter(text(MISSING_README_SQL))
                .order_by(Skill.score.desc().nullslast())
                .limit(1000)
                .all()
            )
            readme_targets = {r.repo_full_name for r in null_readme_skills} & set(all_repos.keys())
            # (backfill comment unchanged)
            backfill_pending = [fn for fn in all_repos if fn.lower() in backfill_names]
            if backfill_pending:
                readme_targets |= set(backfill_pending) - _repo_names_settled(db, backfill_pending)
            # Everything this sync saw that still needs a README, new or not.
            readme_targets |= select_readme_targets(all_repos, _repo_names_settled(db, list(all_repos)))
```

The old comment about catching `''` goes: the shared rule covers it.

- [ ] **Step 3: Phase 5 fetch loop** — declare `readme_absent: set[str] = set()` beside `readme_cache`, open the client with `httpx.AsyncClient(timeout=30.0, follow_redirects=True)` (a renamed repo answers 301; without following it the fetch looked like "no README"), and replace the status handling:

```python
                            if resp.status_code == 200:
                                body = resp.text[:50000]
                                if body.strip():
                                    readme_cache[full_name] = body
                                else:
                                    readme_absent.add(full_name)
                            elif resp.status_code == 404:
                                readme_absent.add(full_name)
                            elif resp.status_code in (403, 429):
```

(the 403/429 branch and the rest of the loop stay as they are)

- [ ] **Step 4: Upsert records both outcomes** — replace the two `readme = readme_cache.get(...)` blocks:

```python
                if existing:
                    existing.prev_stars = existing.stars
                    for key, val in repo_data.items():
                        setattr(existing, key, val)
                    name = existing.repo_full_name
                    for col, val in readme_update(existing.readme_content, readme_cache.get(name),
                                                  name in readme_absent, func.now()).items():
                        setattr(existing, col, val)
                    updated_count += 1
                else:
                    new_skill = Skill(**repo_data)
                    # (prev_stars comment and line unchanged)
                    name = repo_data.get("repo_full_name", "")
                    for col, val in readme_update(None, readme_cache.get(name),
                                                  name in readme_absent, func.now()).items():
                        setattr(new_skill, col, val)
                    db.add(new_skill)
```

Add `from app.services.readme_coverage import readme_update` and `from sqlalchemy import func` (merge into the Step 1 import: `from sqlalchemy import func, not_, text`).

- [ ] **Step 5: Verify** — `python -c "import app.scheduler.jobs"` (no error) and `python -m pytest tests/ -q` → all pass. `grep -n "_repo_names_with_readme" -r app` → no hits.

- [ ] **Step 6: Commit** — `git commit -am "fix(sync): record 'no README on GitHub', stop re-fetching it every run, follow renames"`

---

### Task 4: Incremental grading

**Files:**
- Create: `backend/app/services/grade_refresh.py`
- Modify: `backend/app/services/security_scanner.py` (delete `scan_all`, 686-751; empty-README guard in `_scan`)
- Modify: `backend/app/scheduler/jobs.py:819-820`
- Test: `backend/tests/test_grade_refresh.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Which rows get re-graded, and the rules fingerprint that forces a full pass."""
from pathlib import Path
from types import SimpleNamespace

from app.services import grade_refresh
from app.services.security_scanner import SecurityScanner


def test_fingerprint_is_the_rules_file(tmp_path: Path):
    f = tmp_path / "rules.py"
    f.write_text("PATTERN = 'a'\n")
    first = grade_refresh.fingerprint(f)
    assert first == grade_refresh.fingerprint(f) and len(first) == 16
    f.write_text("PATTERN = 'b'\n")
    assert grade_refresh.fingerprint(f) != first


def test_the_live_fingerprint_hashes_the_scanner_not_the_bookkeeping():
    scanner_file = Path(grade_refresh.security_scanner.__file__)
    assert grade_refresh.RULES_FINGERPRINT == grade_refresh.fingerprint(scanner_file)


def test_scan_full_env_forces_a_full_pass(monkeypatch):
    monkeypatch.setenv("SCAN_FULL", "1")
    assert grade_refresh.full_scan_reason(db=None) == "SCAN_FULL=1"  # decided before any query


def test_scan_all_no_longer_lives_in_the_rules_file():
    assert not hasattr(SecurityScanner, "scan_all")


def test_an_empty_readme_is_unknown_not_safe():
    skill = SimpleNamespace(readme_content="", author_name="x", stars=3, license=None,
                            repo_full_name="x/y", homepage_url="")
    assert SecurityScanner().scan_single(skill) == ("unknown", [])
```

- [ ] **Step 2: Run to see them fail** — `python -m pytest tests/test_grade_refresh.py -q` → `ModuleNotFoundError: No module named 'app.services.grade_refresh'`.

- [ ] **Step 3: Create `grade_refresh.py`**

```python
"""Writing security grades to the catalog: which rows, and when.

The rules live in security_scanner.py; this module decides which rows to grade
and stores the result. The split is what makes RULES_FINGERPRINT honest: it
hashes security_scanner.py, so any change to how a README is graded — a pattern,
a helper, the trust tiers — changes it and forces a full re-grade, while edits
here do not.

A full pass runs when a README'd row carries a different scanner_version (the
rules changed, or the row was graded before stamps existed) or SCAN_FULL=1.
Otherwise only rows whose inputs moved since they were graded: a README fetched
after the last grade, or stars/license/homepage changed (the sync and the
stale-row probe bump last_synced only when a value actually changes). Before
this, every sync re-read ~31K READMEs (~1.5 GB) and re-graded all of them.

Chunked with a commit per batch and keyset pagination by id (see
memory: scan-all-single-transaction-timeout — one 106K-row transaction hit
57014 and wrote nothing).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

from sqlalchemy import bindparam, func, or_, update
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services import security_scanner

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
FINGERPRINT_CHARS = 16


def fingerprint(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:FINGERPRINT_CHARS]


RULES_FINGERPRINT = fingerprint(Path(security_scanner.__file__))

_TABLE = Skill.__table__
# Grading is not a sync. Writing last_synced explicitly stops the ORM's
# onupdate=now() from firing: a bumped last_synced hides the row from the
# stale-row probe (refresh-stale.yml orders by it) and freezes its stars.
_WRITE_GRADE = (
    update(_TABLE)
    .where(_TABLE.c.id == bindparam("_id"))
    .values(
        security_grade=bindparam("_grade"),
        security_flags=bindparam("_flags"),
        security_scanned_at=func.now(),
        scanner_version=RULES_FINGERPRINT,
        last_synced=_TABLE.c.last_synced,
    )
)


def _has_readme():
    return (Skill.readme_content.isnot(None), Skill.readme_content != "")


def full_scan_reason(db: Session | None) -> str | None:
    if os.environ.get("SCAN_FULL") == "1":
        return "SCAN_FULL=1"
    stale = (
        db.query(Skill.id)
        .filter(*_has_readme())
        .filter(or_(Skill.scanner_version.is_(None), Skill.scanner_version != RULES_FINGERPRINT))
        .limit(1)
        .first()
    )
    return "rules fingerprint changed or rows never stamped" if stale else None


def _inputs_changed_since_graded():
    # greatest() skips NULLs, so a row never fetched through the marker still
    # re-grades when last_synced moves.
    return or_(
        Skill.security_scanned_at.is_(None),
        Skill.security_scanned_at < func.greatest(Skill.readme_fetched_at, Skill.last_synced),
    )


def _grade_readme_rows(db: Session, full: bool, stats: dict, batch_size: int) -> None:
    scanner = security_scanner.SecurityScanner()
    last_id = 0
    while True:
        q = db.query(Skill).filter(*_has_readme()).filter(Skill.id > last_id)
        if not full:
            q = q.filter(_inputs_changed_since_graded())
        batch = q.order_by(Skill.id.asc()).limit(batch_size).all()
        if not batch:
            return
        rows = []
        for skill in batch:
            grade, flags = scanner.scan_single(skill)
            rows.append({"_id": skill.id, "_grade": grade, "_flags": json.dumps(flags)})
            stats["scanned"] += 1
            stats[grade] = stats.get(grade, 0) + 1
        last_id = batch[-1].id
        db.execute(_WRITE_GRADE, rows)
        db.commit()


def _mark_readmeless_unknown(db: Session, stats: dict, batch_size: int) -> None:
    # Only rows not already 'unknown', so this stays a near no-op at steady state.
    last_id = 0
    while True:
        ids = [
            r.id for r in (
                db.query(Skill.id)
                .filter((Skill.readme_content.is_(None)) | (Skill.readme_content == ""))
                .filter(Skill.security_grade.isnot(None))
                .filter(Skill.security_grade != "unknown")
                .filter(Skill.id > last_id)
                .order_by(Skill.id.asc())
                .limit(batch_size)
                .all()
            )
        ]
        if not ids:
            return
        db.query(Skill).filter(Skill.id.in_(ids)).update(
            {"security_grade": "unknown", "security_flags": "[]", "last_synced": Skill.last_synced},
            synchronize_session=False,
        )
        stats["no_readme"] += len(ids)
        last_id = ids[-1]
        db.commit()


def refresh_grades(db: Session, batch_size: int = BATCH_SIZE) -> dict:
    stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "reject": 0, "unknown": 0, "no_readme": 0}
    reason = full_scan_reason(db)
    logger.info("scan mode=%s%s fingerprint=%s", "full" if reason else "incremental",
                f" reason={reason}" if reason else "", RULES_FINGERPRINT)
    _grade_readme_rows(db, full=bool(reason), stats=stats, batch_size=batch_size)
    _mark_readmeless_unknown(db, stats, batch_size)
    logger.info(
        "Security scan complete: %d scanned, %d safe, %d caution, %d unsafe, %d reject, %d newly-unknown",
        stats["scanned"], stats["safe"], stats["caution"], stats["unsafe"], stats["reject"], stats["no_readme"],
    )
    return stats
```

- [ ] **Step 4: Edit `security_scanner.py`** — delete the whole `scan_all` method (686-751). In `_scan`, right after `readme = (skill.readme_content or "")[:15000]`:

```python
        if not readme:
            # Nothing to grade is not "nothing found". refresh_grades never sends
            # an empty README here, but the admin preview and the /api scan path
            # did, and received "safe".
            return "unknown", []
```

Remove `json` from the imports only if nothing else in the file uses it (`grep -n "json\." backend/app/services/security_scanner.py`).

- [ ] **Step 5: Call it from the sync** — `jobs.py:819-820` becomes:

```python
            from app.services.grade_refresh import refresh_grades
            sec_stats = refresh_grades(db)
```

- [ ] **Step 6: Run** — `python -m pytest tests/ -q` → all pass, including the 5 new.

- [ ] **Step 7: Read-only check against production** — confirm the queries compile and the first sync will be full:

```bash
python3 - <<'PY'
import os; os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.services import grade_refresh as g
from app.models.skill import Skill
eng = create_engine(dotenv_values(".env")["SUPABASE_DB_URL"])
with Session(eng) as db:
    print("reason:", g.full_scan_reason(db), "| fingerprint:", g.RULES_FINGERPRINT)
    print("incremental rows now:", db.query(Skill.id).filter(*g._has_readme()).filter(g._inputs_changed_since_graded()).count())
PY
```

Expected: `reason: rules fingerprint changed or rows never stamped`; incremental rows ≈ 31K (nothing stamped yet).

- [ ] **Step 8: Commit** — `git add backend/app/services/grade_refresh.py backend/tests/test_grade_refresh.py && git commit -am "perf(sync): grade only rows whose inputs changed; full pass when the rules file changes"`

---

### Task 5: The analyzer stops calling a missing README "safe"

**Files:** Modify `frontend/src/utils/securityScanner.ts:18-24, 449`, `frontend/src/pages/AnalyzerPage.tsx` (GRADE_CONFIG, two no-flag messages, DeepAuditOffer render), `frontend/src/components/AuditLeadCapture.tsx` (copy)

- [ ] **Step 1: Type** — `grade: "safe" | "caution" | "unsafe" | "reject" | "unknown";`

- [ ] **Step 2: Guard** — in `scanReadme`, right after `const trustTier = getTrustTier(author, stars, license);`:

```ts
  // No README (a 404, or the unauthenticated readme call failed): nothing to
  // grade is not "safe". Mirrors the Python rule path.
  if (!original) return _buildResult("unknown", [], trustTier);
```

- [ ] **Step 3: AnalyzerPage** — add to `GRADE_CONFIG`:

```ts
  unknown: {
    label: "No README",
    labelZh: "无 README",
    color: "text-gray-600 dark:text-gray-300",
    bg: "bg-gray-50 dark:bg-gray-800/40",
    border: "border-gray-200 dark:border-gray-700",
    icon: "?",
  },
```

Both no-flag messages (around 512-518 and 640-650) branch on `scan.grade === "unknown"` first:

```tsx
              {scan.grade === "unknown"
                ? isZh
                  ? "GitHub 上没有可读取的 README,无法做规则扫描 —— 这不等于安全。"
                  : "No README could be read from GitHub, so there was nothing to scan — this is not a clean result."
                : scan.flags.length === 0
                  ? /* existing text unchanged */
```

and the green box at 640-650 renders only when `scan.grade !== "unknown"` (the gray message above already explains). Render `<DeepAuditOffer … />` only when `result.scan.grade !== "unknown"` — its non-risky copy says "Green light ✓".

- [ ] **Step 4: AuditLeadCapture** — `copyFor` gets a third branch; pass `g === "unknown"`:

```ts
function copyFor(zh: boolean, risky: boolean, unknown: boolean, owner: string, flagCount: number): Copy {
```

with headlines — zh `"这个仓库没有可评的 README —— 要我们看看你们整套栈吗?"`, en `"No README here to grade — want us to audit your whole stack instead?"` — chosen before the risky/clean branches. Call site: `copyFor(lang === "zh", RISKY_GRADES.has(g), g === "unknown", owner, flagCount)`.

- [ ] **Step 5: Verify** — `cd frontend && npx tsc -b --noEmit && npm run lint 2>&1 | tail -1 && npm run build:check 2>&1 | tail -1`. Dev server: `/analyzer/?repo=` on a repo known to have no README (pick one from `SELECT repo_full_name FROM skills WHERE readme_content='' AND stars>0 LIMIT 5`) shows "No README", no green box, no Pro card. Screenshot.

- [ ] **Step 6: Commit** — `git commit -am "fix(analyzer): a repo with no README is 'no README', not SAFE"`

---

### Task 6: The backfill script

**Files:** Rewrite `backend/readme_backfill.py`; Test `backend/tests/test_readme_backfill.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Pure decisions of the scheduled README backfill."""
import readme_backfill as rb
from app.services.readme_coverage import MISSING_README_SQL


def test_keeps_the_first_tier_while_work_remains():
    assert rb.choose_floor(rb.DROP_BELOW, allow_drop=True) == rb.DEFAULT_FLOOR


def test_drops_to_one_star_once_the_first_tier_is_nearly_done():
    assert rb.choose_floor(rb.DROP_BELOW - 1, allow_drop=True) == rb.LOW_FLOOR


def test_never_drops_without_the_flag():
    assert rb.choose_floor(0, allow_drop=False) == rb.DEFAULT_FLOOR


def test_zero_star_repos_are_never_targets():
    assert rb.clamp_floor(0) == rb.LOW_FLOOR == 1


def test_stops_under_the_quota_floor():
    assert rb.quota_exhausted(rb.QUOTA_FLOOR - 1)
    assert not rb.quota_exhausted(rb.QUOTA_FLOOR)


def test_candidates_follow_the_shared_rule():
    sql = rb.CANDIDATE_SQL
    assert MISSING_README_SQL in sql
    assert "security_grade = 'unknown'" in sql and "repo_status" in sql
    assert "stars >= %(floor)s" in sql and "ORDER BY stars DESC" in sql


def test_import_needs_no_credentials():
    # CI imports this module in tests without GH_TOKEN or a database.
    assert rb.main
```

- [ ] **Step 2: Run to see them fail** — `python -m pytest tests/test_readme_backfill.py -q` → `KeyError: 'GH_TOKEN'` at import (the current module reads it at import time).

- [ ] **Step 3: Rewrite `backend/readme_backfill.py`**

```python
#!/usr/bin/env python3
"""README backfill — fetch READMEs for ungraded repos the sync never revisits.

The sync fetches READMEs only for repos its incremental search returned in that
run, so a dormant repo that entered the catalog without one stayed ungraded
forever: on 2026-09-23, 7,711 live repos with >=5 stars and 49,867 with 1-4.
This walks those rows most-starred first and records every definite answer
through app/services/readme_coverage.py, the rule the sync uses too. The next
sync grades what it fetched.

Scheduled by .github/workflows/readme-backfill.yml at 03/11/19 UTC, between
syncs. One request per second globally (4 threads fill latency gaps) and one
autocommit UPDATE per row — the load the instance tolerated in June, when 8
workers alongside an index build made its REST API 504. Stops early when the
GitHub quota the sync shares falls under QUOTA_FLOOR, or a sync is queued or
running.

Env:  GH_TOKEN; SUPABASE_DB_URL (or backend/.env);
      GITHUB_REPOSITORY + ACTIONS_TOKEN (optional) to see a running sync.
Args: --floor N (5)  --cap N (1500)  --allow-floor-drop
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.services.readme_coverage import MISSING_README_SQL

WORKERS = 4
MIN_INTERVAL = 1.0      # seconds between request starts, globally
QUOTA_FLOOR = 1500      # leave this much of the shared token for the next sync
DEFAULT_FLOOR = 5       # first tier: repos someone looks at
LOW_FLOOR = 1           # second tier; 0-star repos are never fetched
DROP_BELOW = 50         # first tier counts as done below this many candidates
CHUNK = 100             # rows between quota / running-sync checks
DEFAULT_CAP = 1500
README_MAX = 50000
HTTP_TIMEOUT = 30

CANDIDATE_SQL = (
    "SELECT repo_full_name FROM skills "
    "WHERE security_grade = 'unknown' AND repo_status IS DISTINCT FROM 'gone' "
    f"AND stars >= %(floor)s AND {MISSING_README_SQL} "
    "ORDER BY stars DESC LIMIT %(cap)s"
)
COUNT_SQL = CANDIDATE_SQL.split(" ORDER BY")[0].replace("SELECT repo_full_name", "SELECT count(*)")
WRITE_SQL = (
    "UPDATE skills SET readme_content = %s, readme_size = %s, readme_fetched_at = now() "
    "WHERE repo_full_name = %s AND (readme_content IS NULL OR readme_content = '')"
)


def clamp_floor(floor: int) -> int:
    return max(floor, LOW_FLOOR)


def choose_floor(first_tier_left: int, allow_drop: bool) -> int:
    return LOW_FLOOR if allow_drop and first_tier_left < DROP_BELOW else DEFAULT_FLOOR


def quota_exhausted(remaining: int) -> bool:
    return remaining < QUOTA_FLOOR


class Pacer:
    def __init__(self, interval: float):
        self.interval, self.lock, self.last = interval, threading.Lock(), 0.0

    def wait(self) -> None:
        with self.lock:
            delay = self.interval - (time.time() - self.last)
            if delay > 0:
                time.sleep(delay)
            self.last = time.time()


def db_url() -> str:
    env_file = Path(__file__).with_name(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            m = re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)
            if m:
                return m.group(1).strip()
    return os.environ["SUPABASE_DB_URL"]


def fetch(full_name: str, token: str, pacer: Pacer) -> tuple[str, str | None, int]:
    """('ok', text, remaining) | ('absent', '', remaining) | ('error', None, remaining).
    urllib follows the 301 GitHub sends for a renamed repo."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{full_name}/readme",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw",
                 "User-Agent": "agentskillshub-readme-backfill"})
    pacer.wait()
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            remaining = int(r.headers.get("X-RateLimit-Remaining", "5000"))
            text = r.read().decode("utf-8", "replace")[:README_MAX]
            return ("ok", text, remaining) if text.strip() else ("absent", "", remaining)
    except urllib.error.HTTPError as e:
        remaining = int(e.headers.get("X-RateLimit-Remaining", "5000"))
        if e.code in (403, 429):
            return "error", None, 0  # rate limited: the quota check ends the run
        return ("absent", "", remaining) if e.code == 404 else ("error", None, remaining)
    except Exception:  # noqa: BLE001 — URLError/SSL/timeout: try again next run
        return "error", None, 5000


def sync_active() -> bool:
    """A sync queued or running on this repository (Actions API). False when
    run locally without the Actions env."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("ACTIONS_TOKEN")
    if not repo or not token:
        return False
    for status in ("in_progress", "queued"):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/workflows/sync.yml/runs?status={status}&per_page=1",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                if json.load(r).get("total_count", 0):
                    return True
        except Exception:  # noqa: BLE001 — can't tell: be safe
            return True
    return False


class Writer:
    """One autocommit connection per thread."""

    def __init__(self, url: str):
        self.url, self.local = url, threading.local()

    def write(self, full_name: str, text: str) -> bool:
        import psycopg2  # imported here so tests need no driver
        for attempt in range(3):
            try:
                conn = getattr(self.local, "conn", None)
                if conn is None:
                    conn = self.local.conn = psycopg2.connect(self.url)
                    conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(WRITE_SQL, (text, len(text), full_name))
                return True
            except Exception:  # noqa: BLE001 — broken connection: reconnect and retry
                self.local.conn = None
                time.sleep(0.5 * (attempt + 1))
        return False


def candidates(url: str, floor: int, cap: int) -> list[str]:
    import psycopg2
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '60s'")
        cur.execute(CANDIDATE_SQL, {"floor": floor, "cap": cap})
        return [r[0] for r in cur.fetchall()]


def count_first_tier(url: str) -> int:
    import psycopg2
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '60s'")
        cur.execute(COUNT_SQL, {"floor": DEFAULT_FLOOR})
        return cur.fetchone()[0]


def summarize(lines: list[str]) -> None:
    text = "\n".join(lines)
    print(text, flush=True)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(text + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=int, default=DEFAULT_FLOOR)
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--allow-floor-drop", action="store_true")
    args = ap.parse_args()

    token, url = os.environ["GH_TOKEN"].strip(), db_url()
    floor = clamp_floor(args.floor)
    if args.allow_floor_drop and floor == DEFAULT_FLOOR:
        left = count_first_tier(url)
        floor = choose_floor(left, allow_drop=True)
        print(f"first tier (>= {DEFAULT_FLOOR} stars) left: {left} -> floor {floor}", flush=True)
    targets = candidates(url, floor, args.cap)
    print(f"targets: {len(targets)} (floor {floor}, cap {args.cap}) · {WORKERS} workers · <= {1 / MIN_INTERVAL:.0f}/s",
          flush=True)

    pacer, writer = Pacer(MIN_INTERVAL), Writer(url)
    counts = {"ok": 0, "absent": 0, "error": 0, "write_failed": 0}
    stopped = ""

    def one(full_name: str) -> int:
        status, text, remaining = fetch(full_name, token, pacer)
        if status != "error" and not writer.write(full_name, text or ""):
            status = "write_failed"
        counts[status] += 1
        return remaining

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i in range(0, len(targets), CHUNK):
            if sync_active():
                stopped = "a sync is queued or running"
                break
            lowest = min(pool.map(one, targets[i:i + CHUNK]))
            print(f"  [{min(i + CHUNK, len(targets))}/{len(targets)}] {counts} · quota {lowest}", flush=True)
            if quota_exhausted(lowest):
                stopped = f"GitHub quota {lowest} < {QUOTA_FLOOR}"
                break

    summarize([
        "## README backfill",
        f"- floor: {floor} stars · cap {args.cap} · targets {len(targets)}",
        f"- fetched: {counts['ok']} · no README on GitHub: {counts['absent']} · "
        f"errors (retried next run): {counts['error']} · write failures: {counts['write_failed']}",
        f"- stopped early: {stopped}" if stopped else "- ran to the end of its batch",
    ])
    return 1 if counts["write_failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run** — `python -m pytest tests/test_readme_backfill.py -q` → 7 passed; full suite green.

- [ ] **Step 5: Local smoke run against production, tiny cap** (no sync running; quota check first with `gh api rate_limit --jq .resources.core.remaining`):

`GH_TOKEN=$(gh auth token) python readme_backfill.py --cap 20`

Expected: `targets: 20 (floor 5 …)`, a summary with fetched + absent + errors = 20 (or fewer if stopped), exit 0. Then read-only check: `SELECT count(*) FROM skills WHERE readme_fetched_at > now() - interval '10 minutes'` → the same number as fetched + absent.

- [ ] **Step 6: Commit** — `git add backend/readme_backfill.py backend/tests/test_readme_backfill.py && git commit -m "feat(backfill): marker-aware README backfill that yields to the sync and its quota"`

---

### Task 7: Schedule the backfill

**Files:** Create `.github/workflows/readme-backfill.yml`

- [ ] **Step 1: Write it**

```yaml
name: README backfill

# Fetches READMEs for ungraded repos the sync never revisits (it fetches only
# for repos its incremental search returned). The next sync grades them.
# See docs/superpowers/specs/2026-09-23-grading-coverage-design.md.
#
# 03/11/19 UTC: after sync (00/08/16, up to 2h) and before refresh-stale
# (04/12/20); the 45-minute timeout guarantees it is gone before refresh-stale
# starts. It deliberately does NOT join sync's concurrency group: a run queued
# into a group cancels that group's pending run, which could be a sync. The
# script instead stops itself every 100 rows if a sync is queued or running.

on:
  schedule:
    - cron: "0 3,11,19 * * *"
  workflow_dispatch:
    inputs:
      cap:
        description: "Max repos this run (1 GitHub API call each)"
        default: "1500"
      floor:
        description: "Minimum stars (never below 1)"
        default: "5"

concurrency:
  group: readme-backfill
  cancel-in-progress: false

permissions:
  contents: read
  actions: read

jobs:
  backfill:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # The script's only non-stdlib dependency; app.services.readme_coverage is pure.
      - name: Install deps
        run: pip install psycopg2-binary==2.9.9

      - name: Backfill READMEs
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
          ACTIONS_TOKEN: ${{ github.token }}
        run: python readme_backfill.py --cap "${{ inputs.cap || '1500' }}" --floor "${{ inputs.floor || '5' }}"

  notify-failure:
    needs: backfill
    if: failure()
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: "README backfill failed",
              body: `README backfill failed. [View run](https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId})`,
            });
```

- [ ] **Step 2: Validate** — `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/readme-backfill.yml'))"` → no error.

- [ ] **Step 3: Commit** — `git add .github/workflows/readme-backfill.yml && git commit -m "ci: schedule the README backfill between syncs"`

---

### Task 8: Don't republish after a failed sync

**Files:** Modify `.github/workflows/deploy.yml` (the `build` job)

- [ ] **Step 1:** Under `jobs: build:` add:

```yaml
    # A failed sync can leave grades half-written; don't publish that. Pushes
    # and manual runs always build.
    if: github.event_name != 'workflow_run' || github.event.workflow_run.conclusion == 'success'
```

- [ ] **Step 2: Validate** YAML as in Task 7 Step 2. **Commit** — `git commit -am "ci(deploy): skip the rebuild when the sync that triggered it failed"`

---

### Task 9: Static surfaces say why a repo is ungraded

**Files:** Modify `frontend/scripts/shared-utils.mjs` (fetchAllSkills columns + new `gradeState`), `frontend/scripts/generate-skill-pages.mjs:310-314, 598-603`, `frontend/scripts/generate-badges.mjs:24-26` + its caller, `frontend/scripts/generate-author-pages.mjs:212, 226`, `frontend/src/components/BadgeEmbed.tsx:12`

- [ ] **Step 1: `shared-utils.mjs`** — add `"readme_size", "readme_fetched_at"` to the fetchAllSkills column list (after `"security_grade", "security_flags"`), and export:

```js
/** Why a row does or doesn't have a grade (backend/app/services/readme_coverage.py):
 *  graded · pending (README fetched, graded at the next sync) · no_readme (GitHub has
 *  none, so it can't be graded) · not_fetched (queued). */
export function gradeState(s) {
  if (s.security_grade && s.security_grade !== "unknown") return "graded";
  if ((s.readme_size || 0) > 0) return "pending";
  if (s.readme_fetched_at) return "no_readme";
  return "not_fetched";
}
```

- [ ] **Step 2: Skill pages** — import `gradeState`; the ungraded verdict and H1 branch on it:

```js
      : gradeState(skill) === "no_readme"
        ? `No README on GitHub, so it cannot be security-graded${qualityPart}.`
        : `Not yet audited${qualityPart}.`;
```

```js
            : gradeState(skill) === "no_readme"
              ? " — no README to audit"
              : " — not yet audited"
```

(Use the variable name the surrounding function already has for the row — read the function head first.)

- [ ] **Step 3: Badges** — `gradeStyle(grade, state)` returns `{ text: "NO README", color: "#6b7280" }` when `state === "no_readme"`, else the existing mapping; `makeBadgeSvg(skill.security_grade, gradeState(skill))`.

- [ ] **Step 4: BadgeEmbed** — alt text `Security status by Agent Skills Hub` (an ungraded repo's badge reads UNAUDITED; the alt must not claim a grade).

- [ ] **Step 5: Author pages** — after `safeN`:

```js
  const gradedN = group.skills.filter((s) => s.security_grade && s.security_grade !== "unknown").length;
  const gradedPhrase = gradedN === group.skills.length
    ? "security-graded"
    : `security-graded where a README exists (${gradedN} of ${group.skills.length})`;
```

and the sentence uses `${gradedPhrase}` in place of the literal `security-graded`.

- [ ] **Step 6: Verify** — `node --check` on the four scripts; `npm run build:check`. Run `node scripts/generate-badges.mjs` locally only if `VITE_SUPABASE_*` are set, and check one `NO README` badge renders; otherwise leave it to the deploy build.

- [ ] **Step 7: Commit** — `git commit -am "fix(pages): say 'no README on GitHub' instead of 'not yet audited' when that's the reason"`

---

### Task 10: SPA detail page

**Files:** Create `frontend/src/lib/gradeState.ts`; Modify `frontend/src/types/skill.ts` (Skill), `frontend/src/components/AuditVerdictCard.tsx`

- [ ] **Step 1: `gradeState.ts`**

```ts
/** Why a row does or doesn't have a grade — same rule as scripts/shared-utils.mjs. */
export type GradeState = "graded" | "pending" | "no_readme" | "not_fetched";

export function gradeState(s: {
  security_grade: string | null;
  readme_size?: number | null;
  readme_fetched_at?: string | null;
}): GradeState {
  if (s.security_grade && s.security_grade !== "unknown") return "graded";
  if ((s.readme_size ?? 0) > 0) return "pending";
  if (s.readme_fetched_at) return "no_readme";
  return "not_fetched";
}
```

- [ ] **Step 2: Types** — in `interface Skill` add `readme_size?: number | null;` and `readme_fetched_at?: string | null;` (the detail query is `select("*")`, so they arrive with no query change).

- [ ] **Step 3: AuditVerdictCard** — `const state = gradeState(skill); const zh = lang === "zh";` (take `lang` from `useI18n()` too). For `grade === "unknown"`, the label and the verdict sentence come from:

```ts
const UNGRADED_COPY = {
  no_readme: {
    label: "NO README",
    en: "This repo has no README on GitHub, so it can't be rule-graded. Check the code, the credentials it asks for, and who maintains it before you trust it.",
    zh: "这个仓库在 GitHub 上没有 README,无法做规则评级。在信任它之前,请检查代码、它索要的凭证,以及维护者是谁。",
  },
  pending: {
    label: "GRADING",
    en: "README fetched — its grade lands with the next sync (every 8 hours).",
    zh: "README 已抓取,评级会在下一次同步时出来(每 8 小时一次)。",
  },
} as const;
```

`not_fetched` keeps the existing `UNAUDITED` label and `t("auditCard.verdict.unknown")`. Strings live in the component, not `translations.ts` (806 lines, already over the 800-line limit).

- [ ] **Step 4: Verify** — `npx tsc -b --noEmit`, lint, `build:check`; dev server on a `/skill/<id>` whose row is `readme_content = ''` with a marker (pick after the Task 6 smoke run) → "NO README" card; a graded row unchanged. Screenshot, dark and light.

- [ ] **Step 5: Commit** — `git commit -am "fix(skill): the audit card says 'no README' or 'grading' instead of 'never audited'"`

---

### Task 11: Rollout and verification

- [ ] **Step 1:** Push (migration already applied in Task 1). Wait for no sync in progress.
- [ ] **Step 2:** `gh workflow run readme-backfill.yml -f cap=200 -f floor=5`; read the job summary; read-only count of rows stamped in the last hour.
- [ ] **Step 3:** Next sync: its log must show `scan mode=full reason=rules fingerprint changed or rows never stamped`; record its duration. The sync after must show `scan mode=incremental` and a shorter duration.
- [ ] **Step 4:** Scheduled runs continue at cap 1500. Daily read-only check: `unknown` by star bucket (the query in the spec). Stop criteria: ≥5★ unknown ≤ 50 → add `--allow-floor-drop` to the workflow's `run:` line and commit.
- [ ] **Step 5:** If any sync exceeds 90 minutes twice in a row, change the cron default cap to 750.
- [ ] **Step 6:** Update memory (`scanner-rules-snyk-and-dryrun-2026-09.md` gains the fingerprint rule; new `grading-coverage-2026-09.md` with the numbers and the stop criteria).
