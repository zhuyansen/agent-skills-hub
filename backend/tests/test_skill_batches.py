"""One query per batch, and no row touched after its batch was committed."""
from types import SimpleNamespace

from app.services import skill_batches as sb
from app.services.quality_analyzer import QualityAnalyzer
from app.services.token_estimator import TokenEstimator


class _Query:
    def __init__(self, db):
        self.db, self.names, self.after, self.cap = db, None, 0, None

    def filter(self, clause):
        right = clause.right
        if hasattr(right, "value") and isinstance(right.value, (list, tuple)):
            self.names = list(right.value)
        else:
            self.after = right.value
        return self

    def order_by(self, *a):
        return self

    def limit(self, n):
        self.cap = n
        return self

    def all(self):
        self.db.queries += 1
        rows = [r for r in self.db.rows if (r.repo_full_name in self.names if self.names is not None else r.id > self.after)]
        return rows[:self.cap] if self.cap else rows


class _Row(SimpleNamespace):
    """A skill with the two fields the batching reads; anything else an analyzer asks for is empty."""

    def __getattr__(self, name):
        return None


class _Db:
    def __init__(self, n):
        self.rows = [_Row(id=i, repo_full_name=f"o/r{i}", readme_size=10) for i in range(1, n + 1)]
        self.queries = self.commits = 0

    def query(self, *a):
        return _Query(self)

    def commit(self):
        self.commits += 1


def test_named_rows_come_in_batches():
    db = _Db(1200)
    names = [r.repo_full_name for r in db.rows]
    sizes = [len(b) for b in sb.skill_batches(db, names, 500)]
    assert sizes == [500, 500, 200] and db.queries == 3


def test_all_rows_come_by_id_until_none_are_left():
    db = _Db(1200)
    sizes = [len(b) for b in sb.skill_batches(db, None, 500)]
    assert sizes == [500, 500, 200] and db.queries == 4  # the fourth finds nothing


def test_an_analyzer_commits_once_per_batch_and_counts_every_row():
    db = _Db(1200)
    assert TokenEstimator().estimate_all(db, batch_size=500, repo_names=[r.repo_full_name for r in db.rows]) == 1200
    assert (db.queries, db.commits) == (3, 3)
    assert all(r.estimated_tokens is not None for r in db.rows)


def test_no_analyzer_loads_everything_at_once():
    import inspect
    for fn in (QualityAnalyzer.analyze_all, TokenEstimator.estimate_all):
        src = inspect.getsource(fn)
        assert "skill_batches(" in src and ".all()" not in src
